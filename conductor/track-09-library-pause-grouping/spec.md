# Track 09 Specification: Library Pause Visualization & Song Grouping

## Objectives
1. Help the musician visually distinguish between:
   - **Takes/Cuts**: Fast replays and section practices of the same song (separated by short pauses < threshold).
   - **Song Changes**: Transitions to new songs / pieces where notes and sheet music are adjusted (separated by longer pauses >= threshold).
2. Render clear pause dividers between different song sessions with formatted pause duration (e.g. `⏸️ 3m 45s pause (Song change / Note break)`).
3. Cluster cuts of the same song into clean visual card groups ("Song Block / Takes"), showing total takes count and combined duration without forcing titles onto individual cuts (preserving the Named Songs list for full recordings).
4. Provide a configurable pause threshold selector in the Library view header (default 1.5 min / 90s, with options 45s, 90s, 2m, 3m, 5m, Off).
5. Support block-level batch actions: select all cuts in a block with a single click, or add an entire takes block directly to a repertoire.

## Architecture
- Grouping logic runs client-side in `tascam_app/static/app.js` using existing `start_seconds` and `duration_seconds` returned by `/api/clips`.
- State preference for threshold is saved in `localStorage['tascam_pause_threshold_sec']`.
- No database migrations or breaking API changes required.

## Data Model & Gap Calculation
$$\Delta t_{\text{pause}} = \max\left(0, \; C_{k+1}.\text{start\_seconds} - (C_k.\text{start\_seconds} + C_k.\text{duration\_seconds})\right)$$
- If $C_{k+1}.\text{source\_file\_id} \neq C_k.\text{source\_file\_id}$, it is a distinct recording and is treated as a major session break.
- If $\Delta t_{\text{pause}} \ge \text{threshold}$, split into a new Song Block and render a pause divider between the blocks.
- If $\Delta t_{\text{pause}} < \text{threshold}$, include in the same Song Block as consecutive cuts/takes.
