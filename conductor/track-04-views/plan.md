# Plan: Track 04 - Filtered Song View

## Steps
1. **UI Layout:**
   - Add a navigation toggle between "All Clips" and "Named Songs".
2. **Fetch and Render:**
   - Implement JS function to fetch named songs from the API.
   - Render the list, grouped or sorted by date.
3. **Tag Management:**
   - Add an input field to add tags to a song.
   - Add "x" buttons on tag badges to remove them.
   - Wire these actions to the `PATCH /api/songs/{song_id}` endpoint.
4. **Player Integration:**
   - Ensure clicking a song loads its clips into the player and switches focus to the player view.
5. **Testing:**
   - Verify sorting, filtering, and tag persistence.
