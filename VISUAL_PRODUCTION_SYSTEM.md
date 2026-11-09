# FitFuel Visual Production System

## Non-negotiable visual target
The target is cinematic, subject-specific 3D educational animation—not flat infographic cards, primitive mannequins, generic stock footage, or camera zooms over static diagrams. A render is not production-ready merely because it is an MP4.

## One visual language, multiple specialist scene families
Every narration beat must resolve to a specialist family and a concrete visual asset plan.

| Family | Required hero assets | Required motion | Accuracy checks |
|---|---|---|---|
| Exercise biomechanics | Realistic human anatomical model, rig, exercise equipment, muscle groups | Full exercise cycle, joint articulation, muscle activation overlays | Exercise-specific joint path, correct prime movers, no floating limbs |
| Muscle anatomy | Layered skin/muscle model, muscle bundles and fibers | Camera push-in, fiber contraction, tissue-level transition | Correct muscle location and fiber orientation |
| Digestive system | Esophagus, stomach, liver, pancreas, small/large intestine | Food bolus/peristalsis, organ cutaway, absorption transition | Anatomically ordered digestive route; distinguish digestion from absorption |
| Food and nutrition | Photorealistic food assets, cutaway/ingredient assets, plate | Food assembly, cutaway, ingredient/nutrient reveal | Food identity and portion depiction match narration |
| Metabolism and hormones | Cells, mitochondria, adipocytes, bloodstream, relevant organs | Molecular transport, receptor binding, ATP/energy transitions | Do not invent pathways or imply unsupported causality |
| Hydration | Human/muscle tissue, blood plasma, cells | Fluid movement and cell-level changes | Avoid misleading claims about instant muscle changes |
| Sleep and recovery | Human body, brain, muscle tissue, circadian cues | Day/night transition, recovery processes | Separate established mechanisms from simplifications |
| General science | Scene-specific assets selected from narration | Cause-to-effect action, not decorative movement | Every visual must explain the sentence being spoken |

## Production architecture
1. **Narration-to-beat planner** emits a typed scene family, entities, action, camera plan, highlighted structures, and evidence/accuracy notes.
2. **Asset resolver** obtains approved, licensed 3D assets and records source, license, attribution, scale, and anatomical review status. No unlicensed scraping.
3. **Scene builder** assembles assets, lighting, camera, labels, and materials in Blender. Use real meshes and rigs; procedural geometry is allowed for molecules/cells and supporting elements, not as a substitute for a realistic human or organ model.
4. **Motion layer** animates the actual subject and relevant structures. Every beat must contain meaningful subject motion.
5. **Render and quality gate** checks duration, frame variation, asset coverage, no missing textures, no black frames, and scene-to-narration matching.
6. **Preview-only review** is mandatory. No generated visual system is enabled in public uploads until its preview is approved.

## Visual quality gate
A scene fails if it uses a stick/ellipsoid mannequin as the hero human, a row of labeled boxes as the hero digestive system, a static food plate as the whole food scene, or camera drift as its only motion. A successful render must show the actual named subject and the action described in the narration.

## Licensing and scientific integrity
- Store asset attribution and license metadata alongside every downloaded model/texture.
- Prefer permissive/public-domain assets and retain attribution where required.
- Never label a simplified educational model as clinical-grade anatomy.
- Use only the structures and mechanisms needed to explain the narration; uncertain mechanisms must be simplified conservatively.
- If a required approved asset is unavailable, fail the preview or use a clearly disclosed temporary placeholder. Never silently substitute the old flat diagram.

## Rollout
- Stage A: asset and scene-family registry, renderer contract, automated quality checks.
- Stage B: first hero scenes: squat biomechanics, digestive tract food journey, photorealistic meal breakdown.
- Stage C: render review and iteration on realism, motion, lighting, and camera.
- Stage D: connect approved scenes to Shorts and Long pipelines behind a feature flag.
- Stage E: enable public production only after human approval of preview artifacts.
