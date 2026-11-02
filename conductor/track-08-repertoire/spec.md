# Track 08 Specification: Repertoire & Setlists

## Objectives
1. Provide a dedicated **Repertoar** section that acts as the primary starting screen of TascamFlow.
2. Allow musicians and bands to create and manage setlists/repertoires (e.g. "Main Set 2026", "Acoustic Rehearsal").
3. Enable adding songs/clips to a repertoire directly from the Recordings list (`Library`) and from the Named Songs view (`Songs`), supporting both single additions and multi-clip batch additions.
4. Support ordering, reordering, and attaching custom notes per song in a repertoire (e.g., key, capo, cues).
5. Support setlist playback (playing through a repertoire continuously).

## Database Schema
- **`Repertoire`**:
  - `id`: Integer primary key
  - `name`: String (name of the repertoire)
  - `description`: Optional String
  - `is_private`: Boolean (for admin/private control)
  - `created_at`: DateTime
  - `updated_at`: DateTime
  - `items`: Relationship to `RepertoireItem` (cascade delete-orphan)
- **`RepertoireItem`**:
  - `id`: Integer primary key
  - `repertoire_id`: Integer foreign key -> `repertoire.id`
  - `clip_id`: Optional Integer foreign key -> `clip.id`
  - `song_id`: Optional Integer foreign key -> `song.id`
  - `position`: Integer (0-based ordering index)
  - `notes`: Optional String
  - `created_at`: DateTime
  - Relationships to `Repertoire`, `Clip`, and `Song`

## API Endpoints
- `GET /api/repertoires`: List all repertoires with item count and total duration.
- `POST /api/repertoires`: Create a new repertoire.
- `GET /api/repertoires/{id}`: Detailed view of a repertoire with sorted items.
- `PATCH /api/repertoires/{id}`: Update repertoire name/description/privacy.
- `DELETE /api/repertoires/{id}`: Delete repertoire (leaves underlying clips intact).
- `POST /api/repertoires/{id}/items`: Add a single clip or song.
- `POST /api/repertoires/{id}/items/batch`: Add multiple clips (`{ clip_ids: [...] }`).
- `PATCH /api/repertoires/{id}/items/{item_id}`: Update notes or position.
- `DELETE /api/repertoires/{id}/items/{item_id}`: Remove item from repertoire.
- `PUT /api/repertoires/{id}/reorder`: Reorder items (`{ item_ids: [...] }`).

## UI / UX Architecture
- **Navigation**: `Repertoar` is first and default active tab, followed by `Songs` and `Library`.
- **Repertoire Overview (Start Screen)**:
  - List of repertoires with count of songs, total duration, description.
  - "Nytt repertoar" button and modal/inline form.
- **Repertoire Detail View**:
  - Breadcrumb / back button to repertoires list.
  - Ordered list of songs in repertoire with playback button, position controls (up/down), notes field, remove button.
  - "Spill alle" continuous playback mode.
- **Add to Repertoire from Library / Songs**:
  - Per-row button `+ Rep` opens selector modal.
  - Batch action in Recordings list: `Legg til i repertoar` for selected clips.
