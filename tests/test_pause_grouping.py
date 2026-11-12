import pytest
from sqlmodel import SQLModel, Session
from starlette.requests import Request
from tascam_app.web import read_all_clips, templates
from tascam_app.models import Song, Clip, SourceFile
from tests.test_repertoire import test_engine, mock_admin

@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)

def test_clips_api_returns_sorted_for_pause_calculation():
    with Session(test_engine) as session:
        src = SourceFile(id=10, filename="260218_0001.wav")
        song = Song(id=10, title="Song 10")
        session.add_all([src, song])
        session.commit()

        # Add clips out of order
        c2 = Clip(id=102, source_file_id=10, song_id=10, file_path="data/clips/102.mp3", start_seconds=643.6, duration_seconds=110.8)
        c1 = Clip(id=101, source_file_id=10, song_id=10, file_path="data/clips/101.mp3", start_seconds=376.7, duration_seconds=176.7)
        c3 = Clip(id=103, source_file_id=10, song_id=10, file_path="data/clips/103.mp3", start_seconds=877.8, duration_seconds=36.3)
        session.add_all([c2, c1, c3])
        session.commit()

        clips = read_all_clips(session=session, user=mock_admin)
        test_clips = [c for c in clips if c.id in (101, 102, 103)]
        assert len(test_clips) == 3

        # Must be ordered by filename asc and start_seconds asc
        starts = [c.start_seconds for c in test_clips]
        assert starts == [376.7, 643.6, 877.8]

def test_pause_calculation_and_partitioning_logic():
    """
    Simulate the client-side partitioning algorithm in Python
    to ensure exact match with mathematical specifications.
    """
    def partition_clips(clips, threshold_sec):
        if not clips:
            return []
        if threshold_sec <= 0:
            return [{"clips": clips, "pause_after": 0}]

        blocks = []
        current_block = [clips[0]]

        for i in range(1, len(clips)):
            prev = clips[i - 1]
            curr = clips[i]
            diff_source = prev.get("source_file_id") != curr.get("source_file_id")
            prev_end = prev["start_seconds"] + prev["duration_seconds"]
            pause = max(0.0, curr["start_seconds"] - prev_end)

            if diff_source or pause >= threshold_sec:
                blocks.append({
                    "clips": current_block,
                    "pause_after": pause,
                    "is_new_session": diff_source
                })
                current_block = [curr]
            else:
                current_block.append(curr)

        if current_block:
            blocks.append({
                "clips": current_block,
                "pause_after": 0.0,
                "is_new_session": False
            })
        return blocks

    test_clips = [
        {"id": 1, "source_file_id": 1, "start_seconds": 100.0, "duration_seconds": 50.0}, # end 150
        {"id": 2, "source_file_id": 1, "start_seconds": 170.0, "duration_seconds": 40.0}, # pause 20s (< 90s) -> same block
        {"id": 3, "source_file_id": 1, "start_seconds": 230.0, "duration_seconds": 30.0}, # end 260
        {"id": 4, "source_file_id": 1, "start_seconds": 500.0, "duration_seconds": 60.0}, # pause 240s (>= 90s) -> new block!
        {"id": 5, "source_file_id": 1, "start_seconds": 580.0, "duration_seconds": 40.0}, # pause 20s -> same block
    ]

    # Threshold 90s
    blocks = partition_clips(test_clips, 90.0)
    assert len(blocks) == 2
    # Block 1 has clips 1, 2, 3
    assert [c["id"] for c in blocks[0]["clips"]] == [1, 2, 3]
    assert blocks[0]["pause_after"] == 240.0 # 500 - 260 = 240s pause
    # Block 2 has clips 4, 5
    assert [c["id"] for c in blocks[1]["clips"]] == [4, 5]
    assert blocks[1]["pause_after"] == 0.0

    # Threshold 300s (5m) -> all in one block because 240s < 300s
    blocks_relaxed = partition_clips(test_clips, 300.0)
    assert len(blocks_relaxed) == 1
    assert len(blocks_relaxed[0]["clips"]) == 5

    # Threshold 10s (tight) -> clips 1 and 2 split because pause is 20s
    blocks_tight = partition_clips(test_clips, 10.0)
    assert len(blocks_tight) == 5

def test_index_template_contains_pause_selector():
    scope = {"type": "http", "method": "GET", "path": "/", "headers": []}
    req = Request(scope)
    rendered = templates.TemplateResponse("index.html", {"request": req, "user": mock_admin})
    assert rendered.status_code == 200
    html = rendered.body.decode("utf-8")
    assert 'id="select-pause-threshold"' in html
    assert 'value="90"' in html
    assert 'Pause split:' in html
