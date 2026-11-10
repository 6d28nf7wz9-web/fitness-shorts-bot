# HyperFrames isolated prototype

This folder is an **experiment only**. It does not replace or modify the production Pixabay/Shorts/long-video pipeline.

## Goal
Validate HyperFrames as a deterministic vertical-video composition layer for branded captions, title cards, simple explainer graphics, and overlays.

## Requirements
- Node.js 22+
- FFmpeg
- Internet access on first `npx` run (to download HyperFrames and the GSAP CDN)

## Run locally (from this folder)
```bash
npx hyperframes preview
npx hyperframes lint
npx hyperframes render --output hyperframes-test.mp4 --fps 30
```

Open the preview URL printed by HyperFrames. Render output stays inside this folder.

## Prototype acceptance checks
- 1080 × 1920 portrait output, 30 fps, 8 seconds
- Three timed text/graphic beats animate predictably
- Render completes and MP4 plays
- No changes to root Python scripts, GitHub Actions schedules, Pixabay source, YouTube upload/privacy, or production output paths

## Next phase (only after this prototype passes)
Test a separate composition that layers captions/graphics over a copied sample clip. Keep all integration work on this branch until reviewed.
