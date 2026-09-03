# Sulcus demo polish QA

This companion describes the pre-migration media preserved in the
[historical archive](archive/README.md). Its product terminology has been
updated to Sulcus; the archived recordings retain their original visuals.

## Problems found in the existing render

- **00:00 and 00:55.9** - scene-wide opacity fades left the exact first and last frames too close to the empty background.
- **00:04.2-00:04.7, 00:11.3-00:11.8, 00:23.3-00:23.8, 00:34.3-00:34.8, 00:44.3-00:44.8, 00:50.3-00:50.8** - overlapping scene fades produced ghosted double-headlines and competing layouts.
- **00:05.5-00:11.3** - the public CLI command clipped at the right edge of the terminal.
- **00:11.5-00:23.5** - the dashboard remained mostly full-frame and the camera focus values did not create meaningful panel emphasis; bottom labels sat too close to the social-player safe edge.
- **00:23.5-00:34.5** - long event metadata clipped inside timeline rows.
- **00:04.5-00:55.9** - several separators and symbols were visibly mojibaked after an earlier source encoding rewrite.
- **00:44.5-00:50.5** - checkpoint identifiers and terminal lines had no responsive width fitting.

## Polish applied

- Replaced overlapping scene opacity with stable, deliberate cuts while preserving scene order and duration.
- Kept the first hook and final payoff fully rendered on the first and last frames.
- Added reusable single-line font fitting with readable minimum sizes for CLI commands, output lines, event rows, and checkpoint output.
- Shortened only non-essential event metadata where required for readability.
- Added restrained dashboard focus moves across Agent Tree, Runtime Timeline, and Processes / IPC, with holds after each move.
- Moved dashboard overlays and labels into a consistent safe area.
- Replaced corrupted punctuation with encoding-stable ASCII equivalents.
- Preserved 1920x1080, 24 fps, 56-second pacing, scene order, narrative, visual identity, real command output, and real runtime data.

## Final render checks

- [x] Exact first and last frames are fully rendered and readable.
- [x] Every scene boundary was inspected at eight frames per second; no flashes, overlaps, or malformed frames remain.
- [x] Full-resolution terminal, dashboard, control, and checkpoint keyframes were checked for clipping and safe-area issues.
- [x] Dashboard focus transitions settle without snapping or overshoot.
- [x] The complete video and audio streams decode without errors (1,344 frames).
- [x] Export is constant 24 fps, 1920x1080 H.264 High Profile video with 48 kHz AAC stereo audio.
- [x] Focused behavior checks pass: 23 tests across the research-team demo, checkpoints, and dashboard scrolling.
