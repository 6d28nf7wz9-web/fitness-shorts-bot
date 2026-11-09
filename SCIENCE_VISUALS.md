# Scientific Explainer Visuals

FitFuel renders original, scene-specific animated scientific illustrations rather than static title cards or generic stock footage.

## How it works
- Every narration scene receives a visual plan: a scene type, short heading, and concrete visual instruction.
- Pillow draws each frame and FFmpeg encodes the sequence at vertical 1080×1920 / 30 FPS.
- Visual elements are revealed progressively and move during the narration; each scene is matched to its spoken idea.
- Supported visual families include digestive tract and dietary fiber, muscle anatomy and muscle fibers, exercise biomechanics, protein synthesis, energy metabolism, hydration, recovery, food composition, and causal processes.
- The presenter avatar remains a separate overlay and is composited after the science animation.

## Visual accuracy
These are educational anatomical schematics, not clinical images or individualized medical advice. The renderer should only depict mechanisms supported by the narration and research context. Complex or unusual claims should be simplified conservatively rather than inventing anatomy.

## Controls
- `SCIENCE_VISUALS=1` (default): render animated science scenes.
- `SCIENCE_VISUALS=0`: retain the existing Pixabay clips.
- Rendered assets and metadata live in `output/science/` and `output/science_info.json`.
