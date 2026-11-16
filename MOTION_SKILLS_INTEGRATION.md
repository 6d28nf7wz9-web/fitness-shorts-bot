# FitFuel Motion Skills Integration

This branch adapts selected ideas from the MIT-licensed [iart-ai/motion-skills](https://github.com/iart-ai/motion-skills) collection into the existing Python + HyperFrames pipeline. It does **not** install a separate AI agent, add paid services, or replace HyperFrames with Remotion.

## Adapted workflows

- **Short-form video** ([source skill](https://github.com/iart-ai/tiktok-video-skills)): first-frame hook, one visual idea per beat, retention-oriented pacing and a strong payoff.
- **Caption animation** ([source skill](https://github.com/iart-ai/tiktok-video-skills)): preserve the existing real audio timing and word-level subtitle pipeline; never invent evenly distributed word timestamps.
- **Explainer video** ([source skill](https://github.com/iart-ai/explainer-video-skills)): choose a visual metaphor that matches the scene's actual teaching point.
- **Talking-head B-roll** ([source skill](https://github.com/iart-ai/b-roll-skills)): use inserts only when they explain the spoken line; avoid unrelated stock footage. Science scenes remain on the branded diagram canvas when no relevant insert is verified.
- **Motion design** ([source skill](https://github.com/iart-ai/motion-design-skills)): one focal point, restrained depth, eased entrances, staggered hierarchy and vertical safe-area discipline.

## Local implementation

- `motion_director.py` assigns a deterministic hook / support / payoff role and a standard / long pacing class to every scene.
- `hyperframes_render.py` attaches those classes to each scene and includes the motion CSS in the HyperFrames composition.
- The existing `visual_engine.py` continues to own scientific topic classification and the distinct SVG visual metaphors.
- The existing audio/subtitle assembly remains unchanged. No fake word timing is introduced.
- The motion layer is dependency-free and keeps the current 1080×1920, 30fps render path.

## Verification contract

Before promoting this branch, run Python CI and HyperFrames integration, render a preview artifact, inspect hook / middle / payoff frames, verify readable titles and non-overlapping captions, and probe the final MP4 dimensions, frame rate and duration. A passing unit test alone is not proof of visual quality.

## Licensing

The upstream motion-skills collection is MIT licensed. This repository contains a small original adaptation of its general workflow concepts rather than vendoring the upstream skill text or scripts. See the upstream repositories for their full license and source material.
