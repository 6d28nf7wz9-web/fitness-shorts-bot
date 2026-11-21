# FitFuel 3D Intelligence & Scientific Visualization Engine

## Phase 1 — dependency-free foundation
- \`three_d_intelligence.py\` classifies narration scenes and emits an explainable provider plan.
- Existing local science visuals and licensed stock remain production-safe routes.
- WorldGen is reserved for optional background environments; Hunyuan3D for optional reusable props.
- SAGE informs task-aware spatial planning but is not treated as a video renderer.
- Text2NeRF remains research-only until it proves a measurable benefit.
- No model weights, paid APIs, CUDA packages, or new runtime dependencies are installed.

## Safety and quality gates
1. Generated geometry is never assumed anatomically or biomechanically accurate.
2. Anatomy, microscopic biology, and exercise mechanics require scientific review.
3. Real people and exercise demonstrations prefer relevant real footage.
4. Provider failure always retains the existing local-science/stock route.
5. \`FITFUEL_3D_GENERATION\` defaults to \`0\`; planning never downloads models or calls providers.
6. Preview workflows remain dry-run and never upload to YouTube.

## Provider notes
- WorldGen: environment candidate; code is Apache-2.0, but weights and dependencies have separate terms and GPU requirements.
- Hunyuan3D-2: props candidate; Community License and applicable territory/distribution/attribution terms require review before commercial deployment.
- SAGE: research architecture reference for spatial task planning.
- Text2NeRF: research-only.

## Phase 2
Add an isolated GPU asset-generation workflow, separate from daily video rendering. Store each asset with source, license, prompt, dimensions, format, and review metadata. Only approved GLB/GLTF assets enter the renderer cache.

## Phase 3
Add Blender only as an optional renderer adapter after the existing render path is stable. Blender must not become a mandatory GitHub Actions dependency or replace the current renderer.
