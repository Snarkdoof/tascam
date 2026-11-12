# Track 09 Plan: Library Pause Visualization & Song Grouping

## Phases

### Phase 1: Conductor & Checkpoint Setup
- [x] Create track specification and plan.
- [x] Register track in `conductor/tracks.md` and `conductor/index.md`.
- [x] Local git checkpoint.

### Phase 2: UI Controls & Templates
- [ ] Add pause threshold selector dropdown to `#library-view .header-row` in `tascam_app/templates/index.html`.

### Phase 3: CSS Styles
- [ ] Style `.song-block` container cards and `.song-block-header`.
- [ ] Style `.pause-divider` line and duration badge.
- [ ] Style `.take-badge` and compact take count indicators.
- [ ] Ensure mobile responsiveness.

### Phase 4: Frontend Logic in `app.js`
- [ ] Implement `formatPauseDuration(seconds)`.
- [ ] Implement `partitionClipsIntoSongBlocks(clips, thresholdSec)`.
- [ ] Update `renderGroups()` to render song blocks and pause dividers.
- [ ] Add block-level "Select All Takes" and "+ Rep" triggers.
- [ ] Connect threshold `<select>` with `localStorage` persistence and immediate reactive re-render.

### Phase 5: Verification & Tests
- [ ] Unit tests for pause gap calculations and block partitioning in `tests/test_pause_grouping.py`.
- [ ] Verify existing clip actions (playback, inline edit, delete, download, repertoire modal) remain functional.
- [ ] Update `AGENT_MAP.md`.
