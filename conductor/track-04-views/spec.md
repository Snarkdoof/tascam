# Track 04: Filtered Song View

## Objective
Create a dedicated view for organizing and accessing "named" songs.

## Requirements
1. **Named Songs List:**
   - Display a list of songs that have been explicitly named by the user.
   - Sort the list chronologically by date.
2. **Tagging UI:**
   - Allow users to add and remove tags from songs in this view.
   - Display tags visually (e.g., as pills/badges).
3. **Integration:**
   - Clicking a song in this list should open the Advanced Media Player (Track 03) for that song.

## Architecture
- Add a new section or page in the frontend (e.g., a new tab in `index.html` or a separate route).
- Fetch data from the new `GET /api/songs/named` endpoint.
