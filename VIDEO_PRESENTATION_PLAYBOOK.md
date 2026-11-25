# FitFuel 2D Motion & Presentation Playbook

This is the production direction for FitFuel Shorts. **3D/Blender is discontinued.** Do not add Blender, Three.js, WebGL, Manim, GPU rendering, or paid image/video generation to the production path.

## Upstream repositories reviewed

- https://github.com/iart-ai/motion-skills — 56-skill hub; use as a technique index, not as a runtime dependency.
- https://github.com/iart-ai/tiktok-video-skills — short-form hooks, pacing, caption emphasis, pattern interrupts.
- https://github.com/iart-ai/explainer-video-skills — scene intent, scientific explanation, storyboard logic, visual review.
- https://github.com/iart-ai/b-roll-skills — spoken-line-to-B-roll matching and relevance checks.
- https://github.com/iart-ai/motion-design-skills — typography, transitions, brand consistency, motion hierarchy.
- ViMax (previously evaluated) — script-to-storyboard and scene-planning concepts only; its paid/cloud video-generation dependencies are not part of the free production path.
- OpenVideoStudio (previously evaluated) — script/storyboard/keyframe/voice/subtitle/editing workflow concepts only; do not add a second full editor/runtime.

## Production rules

1. Hook in the first 1–2 seconds: one clear curiosity gap, bold visual claim, or concrete problem. No long logo intro.
2. Every narration sentence gets a visual intent: presenter, relevant B-roll, or a purpose-built 2D scientific illustration. Never repeat the same generic diagram for unrelated scenes.
3. Prefer lightweight 2D: SVG paths, CSS transforms/opacity, animated charts, callouts, flow diagrams, timelines, iconography, labels, and split-screen comparisons.
4. Match motion to meaning: flow for circulation, branching for hormones/signals, progressive fill for energy/nutrition, line draw for movement mechanics, count-up for metrics, and restrained pulse for emphasis.
5. Use kinetic typography sparingly but deliberately: emphasize the spoken keyword at the moment it is said; keep captions separate from titles and within 9:16 safe zones.
6. Alternate visual scale and composition every few seconds: presenter close/medium, full-frame B-roll, diagram, comparison, metric card. Avoid identical scene layouts back-to-back.
7. Presenter is a separate layer. Use subtle speech-linked expression/gesture cues; do not let the presenter cover the scientific focal point or captions.
8. B-roll must match the spoken sentence, not merely the broad topic. If relevance is weak, use the topic-specific 2D visual instead.
9. Sound supports the explanation: clean narration first, restrained music bed, sparse transition/emphasis cues. No random effects.
10. End with a concise payoff and a natural loop/CTA; avoid adding a long outro.

## Scene contract

Each scene should carry or derive:
- `visual_category` / `visual_type`
- `visual_title` and concise `visual_subtitle`
- `visual_intent` (what the viewer should understand)
- `visual_metaphor` (diagram/chart/comparison/timeline/callout/B-roll/presenter)
- `motion_cue` (draw/reveal/fill/flow/pulse/count-up/zoom)
- `focal_point` and `shot_size`
- narration timing and relevant B-roll query

If metadata is absent, infer it from the narration with a safe 2D fallback. Keep classification deterministic and test it offline.

## Review gates

- Unit tests prove different categories produce genuinely different 2D compositions.
- A preview must be rendered with publishing disabled.
- Inspect the opening hook, every scene transition, text/caption safe zones, presenter overlap, visual relevance, and final payoff.
- Validate 1080x1920, 30fps, audio presence, duration, and FFprobe output.
- Never claim visual quality is approved until the actual preview frames/video have been inspected.

## Free-first implementation order

1. Keep HyperFrames + FFmpeg as the single composition/render path.
2. Strengthen script-to-scene intent and hook/payoff structure.
3. Expand the category-specific SVG/2D illustration library and its motion grammar.
4. Improve sentence-level B-roll matching and use 2D illustrations as fallback.
5. Add narration-aligned kinetic typography, presenter gestures, and sound cues.
6. Generate and inspect one complete preview before any production rollout.

The upstream repositories are reference material. Port the useful methods into the existing pipeline; do not install entire stacks or introduce paid services just because a repository contains them.
