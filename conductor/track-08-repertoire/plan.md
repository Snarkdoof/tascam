# Track 08 Implementation Plan: Repertoire & Setlists

## Phases

### Phase 1: Models & Schemas
- [x] Define `Repertoire` and `RepertoireItem` in `tascam_app/models.py`.
- [x] Define Pydantic request/response schemas (`RepertoireRead`, `RepertoireDetailRead`, `RepertoireItemRead`, etc.).
- [x] Import new models in `tascam_app/database.py` and `migrate_db.py`.

### Phase 2: Backend APIs & Unit Tests
- [x] Implement CRUD routes for repertoires in `tascam_app/web.py`.
- [x] Implement item routes (single add, batch add, update notes/position, delete item, reorder items).
- [x] Create pytest test suite in `tests/test_repertoire.py` covering model creation, CRUD, batch add, reorder, and cascade behavior.
- [x] Verify with `uv run pytest`.

### Phase 3: Frontend Templates & Styling
- [x] Update `tascam_app/templates/index.html` navigation to place Repertoar first and make it active by default.
- [x] Add `#repertoire-view` (overview + detail views).
- [x] Add batch action button in recordings view and add-to-repertoire modal dialog.
- [x] Style the new components in `tascam_app/static/style.css`.

### Phase 4: Frontend Logic & Continuous Setlist Playback
- [x] Update `tascam_app/static/app.js` to manage repertoire state, view switching, and CRUD operations.
- [x] Connect "+ Rep" on clips and batch action in recordings view.
- [x] Implement auto-advance playback when a song ends in setlist context.

### Phase 5: Documentation & Verification
- [x] Update `AGENT_MAP.md`.
- [x] Mark Track 08 as completed in `conductor/index.md` and `conductor/tracks.md`.
