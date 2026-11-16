# FitFuel motion production playbook

This project adapts the MIT-licensed craft patterns in iart-ai/motion-skills. The upstream skills are agent workflows, not a runtime video API; FitFuel implements the relevant techniques in HyperFrames, FFmpeg, Python, SVG and CSS.

## Applied skill families

- TikTok / short-form: hook → support → payoff scene grammar, visual resets and vertical-safe title/caption zones.
- Explainer / diagram animation: topic classification and a distinct scientific SVG metaphor for each scene category.
- Motion design: eased entrances, controlled depth, alternating panel composition, camera push/drift/pull and a consistent brand system.
- Kinetic typography: synchronized word-group captions in the final mux, with a separate headline/subtitle reveal hierarchy.
- B-roll: only footage selected by the strict semantic matcher is eligible for the HyperFrames timeline. Science fallback scenes remain diagram-led.
- Deliver-and-verify: automated unit tests, HyperFrames lint/render and FFmpeg/ffprobe artifact checks.

## Scene production contract

1. Read each authored visual title, subtitle, narration and search keyword.
2. Use strict semantic stock matching; never substitute broad unrelated footage.
3. Use a B-roll file only when clips_info.json identifies a stock-backed scene, includes verified clip metadata, and the processed scene MP4 exists.
4. If footage is absent or the scene is a science fallback, use the designed canvas and topic-specific diagram.
5. Apply a deterministic scene motion plan: role, pace, focal point, layout, camera treatment and emphasis.
6. Render visuals through HyperFrames; add narration, word-group captions and music in the FFmpeg final mux.
7. Fail on structural/render errors; keep preview runs upload-disabled until the owner approves the video.

## Why not install every pack into CI?

The upstream repositories provide portable instructions and references for coding agents. They are not all runtime renderers. The relevant craft is adapted into FitFuel's scene director, visual engine, stock matcher and verification tests. This avoids unused dependencies, network installs and paid generation services on every run.

## References

- https://github.com/iart-ai/motion-skills
- https://github.com/iart-ai/tiktok-video-skills
- https://github.com/iart-ai/explainer-video-skills
- https://github.com/iart-ai/motion-design-skills
- https://github.com/iart-ai/kinetic-typography-skills
- https://github.com/iart-ai/b-roll-skills
- https://hyperframes.app/docs/6-reference/html-schema

Upstream motion-skills is MIT-licensed. This playbook records the production patterns adapted for FitFuel rather than copying the upstream skill files.
