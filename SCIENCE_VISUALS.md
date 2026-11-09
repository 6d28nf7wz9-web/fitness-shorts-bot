# Scientific Explainer Visuals

FitFuel can render original animated infographic scenes locally instead of relying exclusively on Pixabay footage.

## How it works
- `science_visuals.py` maps each narration scene to a visual family (muscle fibers, protein building, energy balance, hydration, sleep/recovery, progressive overload, or a concept card).
- Pillow draws the infographic; FFmpeg adds a gentle motion/zoom and encodes vertical 1080×1920 video at 30 FPS.
- Each generated scene is duration-matched to the corresponding narration scene.
- The generated clips are assembled with the existing voice, captions, music, and presenter avatar.

## Controls
- `SCIENCE_VISUALS=1` (default): render science diagrams and use them for the final video.
- `SCIENCE_VISUALS=0`: use the existing Pixabay clips unchanged.
- Generated assets and scene metadata live in `output/science/` and `output/science_info.json`.

## Important
These are educational schematic illustrations, not diagnostic/anatomical medical images. Topic matching is heuristic; review visual accuracy for sensitive or complex claims before publishing. The existing script validation and upload workflow remain in place.
