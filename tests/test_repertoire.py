import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from tascam_app.web import app, get_current_user, get_session
from tascam_app.models import User, Song, Clip, SourceFile, Repertoire, RepertoireItem

# In-memory SQLite for testing with StaticPool so all connections share the same memory DB
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)

def get_test_session():
    with Session(test_engine) as session:
        yield session

mock_admin = User(id=1, email="admin@test.com", name="Admin User", is_admin=True, is_approved=True)
mock_regular = User(id=2, email="user@test.com", name="Regular User", is_admin=False, is_approved=True)

current_test_user = mock_admin

def get_test_user():
    return current_test_user

app.dependency_overrides[get_session] = get_test_session
app.dependency_overrides[get_current_user] = get_test_user

client = TestClient(app)

def test_repertoire_crud_and_items():
    global current_test_user
    current_test_user = mock_admin

    # Setup dummy source file, song, clips
    with Session(test_engine) as session:
        src = SourceFile(id=1, filename="260101_001.wav")
        song1 = Song(id=1, title="Song Alpha", artist="The Band", is_named=True)
        song2 = Song(id=2, title="Song Beta", artist="The Band", is_named=True)
        clip1 = Clip(id=1, source_file_id=1, song_id=1, file_path="data/clips/1.mp3", start_seconds=0.0, duration_seconds=180.0)
        clip2 = Clip(id=2, source_file_id=1, song_id=2, file_path="data/clips/2.mp3", start_seconds=180.0, duration_seconds=240.0)
        clip3 = Clip(id=3, source_file_id=1, song_id=1, file_path="data/clips/3.mp3", start_seconds=420.0, duration_seconds=120.0)
        session.add_all([src, song1, song2, clip1, clip2, clip3])
        session.commit()

    # 1. Create Repertoire
    res = client.post("/api/repertoires", json={"name": "Setlist Summer 2026", "description": "Festival set"})
    assert res.status_code == 200
    rep = res.json()
    assert rep["name"] == "Setlist Summer 2026"
    assert rep["item_count"] == 0
    assert rep["total_duration_seconds"] == 0.0
    rep_id = rep["id"]

    # 2. Add single item
    res = client.post(f"/api/repertoires/{rep_id}/items", json={"clip_id": 1, "notes": "Drop D tuning"})
    assert res.status_code == 200
    item1 = res.json()
    assert item1["position"] == 0
    assert item1["notes"] == "Drop D tuning"
    assert item1["clip"]["id"] == 1
    assert item1["song"]["title"] == "Song Alpha"

    # 3. Batch add items
    res = client.post(f"/api/repertoires/{rep_id}/items/batch", json={"clip_ids": [2, 3]})
    assert res.status_code == 200
    assert res.json()["added_count"] == 2

    # 4. Read repertoire detail
    res = client.get(f"/api/repertoires/{rep_id}")
    assert res.status_code == 200
    detail = res.json()
    assert detail["name"] == "Setlist Summer 2026"
    assert detail["item_count"] == 3
    assert detail["total_duration_seconds"] == 180.0 + 240.0 + 120.0
    items = detail["items"]
    assert len(items) == 3
    assert items[0]["position"] == 0 and items[0]["clip_id"] == 1
    assert items[1]["position"] == 1 and items[1]["clip_id"] == 2
    assert items[2]["position"] == 2 and items[2]["clip_id"] == 3

    # 5. List repertoires
    res = client.get("/api/repertoires")
    assert res.status_code == 200
    rep_list = res.json()
    assert len(rep_list) == 1
    assert rep_list[0]["item_count"] == 3
    assert rep_list[0]["total_duration_seconds"] == 540.0

    # 6. Reorder items: put clip 3 first, then 1, then 2
    res = client.put(f"/api/repertoires/{rep_id}/reorder", json={"item_ids": [items[2]["id"], items[0]["id"], items[1]["id"]]})
    assert res.status_code == 200

    res = client.get(f"/api/repertoires/{rep_id}")
    detail = res.json()
    assert detail["items"][0]["clip_id"] == 3
    assert detail["items"][1]["clip_id"] == 1
    assert detail["items"][2]["clip_id"] == 2

    # 7. Update item note
    res = client.patch(f"/api/repertoires/{rep_id}/items/{items[0]['id']}", json={"notes": "Fast tempo intro"})
    assert res.status_code == 200
    assert res.json()["notes"] == "Fast tempo intro"

    # 8. Delete an item and verify position normalization
    item_to_delete_id = detail["items"][1]["id"] # The middle one
    res = client.delete(f"/api/repertoires/{rep_id}/items/{item_to_delete_id}")
    assert res.status_code == 200

    res = client.get(f"/api/repertoires/{rep_id}")
    detail = res.json()
    assert detail["item_count"] == 2
    assert detail["items"][0]["position"] == 0
    assert detail["items"][1]["position"] == 1

    # 9. Update repertoire name
    res = client.patch(f"/api/repertoires/{rep_id}", json={"name": "Updated Setlist", "description": "New notes"})
    assert res.status_code == 200
    assert res.json()["name"] == "Updated Setlist"
    assert res.json()["description"] == "New notes"

    # 10. Delete repertoire and check underlying clips remain
    res = client.delete(f"/api/repertoires/{rep_id}")
    assert res.status_code == 200

    res = client.get(f"/api/repertoires/{rep_id}")
    assert res.status_code == 404

    # Verify clip 1 is still in DB
    with Session(test_engine) as session:
        c = session.get(Clip, 1)
        assert c is not None
        # Verify RepertoireItem was deleted
        rep_items = session.exec(SQLModel.metadata.tables["repertoireitem"].select()).all()
        assert len(rep_items) == 0

def test_repertoire_privacy():
    global current_test_user

    # Admin creates private repertoire
    current_test_user = mock_admin
    res = client.post("/api/repertoires", json={"name": "Secret Repertoire", "is_private": True})
    assert res.status_code == 200
    rep_id = res.json()["id"]

    # Regular user should not see it in list
    current_test_user = mock_regular
    res = client.get("/api/repertoires")
    assert res.status_code == 200
    assert len(res.json()) == 0

    # Regular user cannot get detail
    res = client.get(f"/api/repertoires/{rep_id}")
    assert res.status_code == 403

def test_index_template_rendering():
    with Session(test_engine) as session:
        user = User(email="test@example.com", name="Test User", is_approved=True)
        session.add(user)
        session.commit()

    # Simulate logged-in session
    res = client.get("/", headers={"Cookie": ""})
    # Without cookie redirects to login
    assert res.status_code == 200
    assert "Login" in res.text or "google" in res.text.lower()

    # Test with session
    client.cookies.set("session", "dummy")
    # Using TestClient session middleware
    from starlette.testclient import TestClient as StarletteTestClient
    with client:
        # Check template directly through Jinja2
        from tascam_app.web import templates
        from starlette.requests import Request
        scope = {"type": "http", "method": "GET", "path": "/", "headers": []}
        req = Request(scope)
        rendered = templates.TemplateResponse("index.html", {"request": req, "user": mock_admin})
        assert rendered.status_code == 200
        html = rendered.body.decode("utf-8")
        assert "nav-repertoire" in html
        assert "repertoire-view" in html
        assert "modal-new-repertoire" in html
        assert "modal-add-to-repertoire" in html
        assert "btn-batch-add-repertoire" in html

