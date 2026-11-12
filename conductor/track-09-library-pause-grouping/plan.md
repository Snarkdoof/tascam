# Track 09 Plan: Library Pause Visualization & Song Grouping

## Phases

### Phase 1: Conductor & Checkpoint Setup
- [x] Create track specification and plan.
- [x] Register track in `conductor/tracks.md` and `conductor/index.md`.
- [x] Local git checkpoint.

### Phase 2: UI Controls & Templates
- [x] Add pause threshold selector dropdown to `#library-view .header-row` in `tascam_app/templates/index.html`.

### Phase 3: CSS Styles
- [x] Style `.song-block` container cards and `.song-block-header`.
- [x] Style `.pause-divider` line and duration badge.
- [x] Style `.take-badge` and compact take count indicators.
- [x] Ensure mobile responsiveness.

### Phase 4: Frontend Logic in `app.js`
- [x] Implement `formatPauseDuration(seconds)`.
- [x] Implement `partitionClipsIntoSongBlocks(clips, thresholdSec)`.
- [x] Update `renderGroups()` to render song blocks and pause dividers.
- [x] Add block-level "Select All Takes" and "+ Rep" triggers.
- [x] Connect threshold `<select>` with `localStorage` persistence and immediate reactive re-render.

### Phase 5: Verification & Tests
- [x] Unit tests for pause gap calculations and block partitioning in `tests/test_pause_grouping.py`.
- [x] Verify existing clip actions (playback, inline edit, delete, download, repertoire modal) remain functional.
- [x] Update `AGENT_MAP.md`.
