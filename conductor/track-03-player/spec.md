# Track 03: Advanced Media Player

## Objective
Upgrade the frontend audio player to support synchronized playback, precise navigation, looping, and marker management.

## Requirements
1. **mcorp-sync Integration:**
   - Utilize the `mcorp-sync` skill and `timingsrc` sequencer for robust playback synchronization.
2. **Marker Management UI:**
   - UI to add markers while listening.
   - Controls to skip back (e.g., 3s) and pause for precise placement.
   - Input fields for marker value (e.g., "A", "B", "16").
   - Display existing markers on a timeline or list.
3. **Advanced Playback Controls:**
   - Jump to specific markers.
   - Loop between two markers or a specific section.
   - "Start from beginning" button.
   - "Skip back to start of current segment" button.
   - Logic: If < 5 seconds into a segment, skip to the beginning of the *previous* segment.
4. **API Integration:**
   - Save new markers to the backend via the API.

## Architecture
- Modify `tascam_app/templates/index.html` and `tascam_app/static/` JS files.
- Ensure the `mcorp-sync` library is loaded and initialized correctly.
