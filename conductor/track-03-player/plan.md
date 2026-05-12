# Plan: Track 03 - Advanced Media Player

## Steps
1. **Setup `mcorp-sync`:**
   - Include the necessary JS libraries for `timingsrc` and `mcorp-sync`.
   - Refactor the existing `<audio>` element to be controlled by the timing object.
2. **Implement Navigation Controls:**
   - Add "Start from beginning" button.
   - Add "Skip back to start of current segment" button with the < 5s logic.
   - Add a "Skip back 3s" button for precision marking.
3. **Implement Marker UI:**
   - Create a UI section below the player to list markers.
   - Add a form to create a new marker at the current playback time.
   - Implement jumping to a marker when clicked.
4. **Implement Looping:**
   - Add UI to select a start and end marker for looping.
   - Use `timingsrc` events or a `requestAnimationFrame` loop to enforce the loop boundaries.
5. **API Integration:**
   - Wire up the marker creation/deletion UI to the `PATCH /api/clips/{clip_id}` endpoint.
6. **Testing:**
   - Manual testing of playback synchronization, looping accuracy, and marker persistence.
