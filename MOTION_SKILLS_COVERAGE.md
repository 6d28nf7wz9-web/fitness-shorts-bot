# iart-ai/motion-skills: 56-skill FitFuel coverage audit

Upstream: https://github.com/iart-ai/motion-skills  
Catalog checked: 2026-11-17. The hub defines 56 agent-workflow skills across 19 separately installable packs. A skill is guidance plus references/tooling for an agent, not a runtime video plugin. FitFuel therefore ports the production techniques into its existing Python, SVG/CSS, HyperFrames and FFmpeg pipeline; it does not install 56 unrelated render stacks or introduce paid services.

## FitFuel implementation map

| Upstream skill | FitFuel treatment |
|---|---|
| short-form-video | Hook / support / payoff, pacing, pattern interrupts and loop-aware closing via motion_director.py |
| caption-animation | Word-aligned kinetic emphasis; audio timing remains authoritative |
| countdown-video | Reserved for future timed challenge/countdown scenes; not forced into explainers |
| lower-thirds (TikTok pack) | Safe-zone brand/presenter identity treatment |
| text-message-animation | Not applicable to current fitness explainer format |
| audiogram | Voice-led scene pacing and waveform-style audio cue concepts; no podcast-only waveform screen |
| youtube-intro-outro | Brand opening/closing hierarchy without wasting the short hook window |
| product-demo-video | Adapted for equipment / exercise demonstration inserts, not fake device UI |
| promo-video | CTA/payoff hierarchy; no discount/price overlays |
| photo-slideshow | Camera drift/push/pull and focal transitions for still/stock fallback shots |
| ad-creative-video | Reusable topic-to-visual templates; no ad variants |
| launch-video | Tease → explain → reveal rhythm for hook/payoff |
| testimonial-video | Quote emphasis treatment available for evidence / study-result scenes |
| chart-animation | Progressive data/metric reveals and count-up-ready visual primitives |
| animated-infographic | Staggered labels, callouts and diagram hierarchy |
| presentation-video | Narration-led staged reveals; no slide-deck dependency |
| explainer-video | Script → scene intent → visual metaphor → narration sync → render |
| wrapped-video | Reusable scene templates and structured data support; no personal recap format |
| diagram-animation | Continuous category-specific SVG motion and sequential signal/flow movement |
| whiteboard-animation | Stroke-draw principle applied selectively to SVG paths, not a full whiteboard style |
| isometric-animation | 2.5D depth, layered panels and camera perspective; no heavy 3D dependency |
| map-animation | Not applicable to exercise / physiology scenes unless a future geography topic requires it |
| gsap-web | Timeline/easing principles translated to CSS/HyperFrames; GSAP not added |
| 60fps-animation | Prefer transform/opacity motion and bounded CSS animation complexity; final Short remains 30fps |
| page-transition-animation | Scene enter/exit grammar adapted to video cuts, not web navigation |
| accessible-animation | Reduced-motion fallback and safe text contrast / safe zones |
| micro-interaction | Presenter emphasis and controlled attention resets; no interactive UI controls |
| glassmorphism | Restrained translucent science panels and depth, not excessive blur |
| svg-animation | SVG stroke reveal, dash flow, pulse and transform-based diagram animation |
| lottie-animation | Lottie-compatible asset boundary documented; not added as an unnecessary runtime |
| ascii-animation | Not applicable to branded fitness explainers |
| animation-principles | Easing, anticipation, follow-through, staging and restrained secondary motion |
| color-motion | Consistent FitFuel palette and semantic category color roles |
| shot-composition | 9:16 safe areas, focal hierarchy and alternating composition |
| motion-art-direction | Scene-specific motion grammar and visual restraint |
| after-effects | Delivery / render discipline adapted; no Adobe dependency |
| beat-sync-editing | Scene pacing and sparse sound cues; beat sync only when music timing is available |
| remotion-video | Data-driven render architecture principles; HyperFrames retained as current renderer |
| logo-animation | Brand reveal / identity hierarchy; no separate long intro |
| motion-background | Continuous low-amplitude background drift and layered depth |
| kinetic-typography | Word-level, narration-aligned key-term emphasis |
| creative-brief | Scene intent and focal-point metadata as a compact per-scene brief |
| motion-pricing | Not a video-engine runtime feature; excluded from production rendering |
| client-revisions | Preview-only iteration and no-publish review gate |
| video-delivery-specs | 1080×1920, 30fps, safe-zone and FFprobe validation |
| brand-motion-guidelines | Shared easing, palette, spacing and presenter behavior tokens |
| shader-glsl | Shader concepts reserved for a future optional renderer; no GPU-only dependency |
| threejs-animation | 2.5D camera/depth principles adapted; full Three.js not justified for current CI |
| particle-system | Small semantic particles / signal dots and fluid movement in SVG |
| manim | Mathematical/physiology diagram sequencing; Manim itself not added to keep renders light |
| generative-illustration | Deterministic vector metaphor generation; no uncontrolled generated assets |
| javascript-animation | Seekable, deterministic timeline and frame-verification principles; CSS/HyperFrames implementation |
| soundtrack | Narration-safe music bed, sparse SFX, and duration-aligned mix |
| lower-thirds (transparent pack) | Safe-zone presenter/brand treatment; alpha export not required for baked Shorts |
| talking-head-b-roll | Spoken-line segmentation, line-specific B-roll queries and strict relevance fallback |
| talking-head | Presenter remains a separate visual layer with speech-linked gestures and expression states |

## Current implementation and verification

- `clips_fast.py`: sentence-specific query ranking. Named exercises such as Romanian deadlift, squat, bench press, hip thrust and others take priority over broad gym queries; each cut uses its own spoken sentence as context.
- `visual_engine.py` + `hyperframes_render.py`: distinct SVG diagrams remain topic-specific. Their existing flow/pulse animations continue throughout scenes; the HyperFrames scene layer adds category-specific motion tracks and staggered progressive reveals (claim → evidence) rather than a one-time entrance-only effect.
- `avatar_motion.py` + `avatar.py`: the existing real presenter (not a second cartoon avatar) receives timecoded point / explain / compare / demonstrate / talk body-language cues. The existing lip-sync sprites receive short smile / surprise / concern accents while preserving closed-mouth frames; subtle FFmpeg lean/rotation follows each scene.
- `motion_director.py`: hook/support/payoff, shot pacing, focal hierarchy, composition and camera movement.
- Preview and CI must stay upload-disabled. No change to YouTube upload settings is authorized by this document.

## Honest scope

Some upstream skills are for maps, chat stories, e-commerce, ad production, web UI, client pricing or specialized renderers. Forcing those into every fitness Short would make the output less coherent and the pipeline heavier. Their relevant transferable principles are mapped above; their unrelated deliverables are intentionally not activated.
