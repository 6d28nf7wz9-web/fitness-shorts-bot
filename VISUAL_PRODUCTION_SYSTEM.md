# FitFuel visual production system

## Chosen production direction

FitFuel Shorts and long-form explainers use a stock-first visual workflow. The
primary visual sources are relevant, licensed Coverr and Pixabay footage, with
Pexels, NASA and imported licensed stock as optional supporting sources.

Blender/CGI character rendering has been removed from the production and preview
paths. Do not reintroduce procedural 3D people, exercise rigs or anatomy scenes
as production footage.

## Scene matching and assembly

1. Gemini writes narration and scene-level visual keywords/titles.
2. The footage selector searches available stock providers using the scene
   keywords and narration context.
3. Candidate clips must pass scene-relevance checks; unrelated generic footage
   is rejected rather than silently substituted.
4. Each scene is cut into short visual beats where useful, then assembled by
   HyperFrames with the existing FitFuel typography, captions, narration, music
   and presenter/avatar layer.
5. If a matching stock segment is selected and the optional Wan feature has
   been explicitly enabled, one frame from that exact stock segment can be
   animated with Wan. The original stock segment remains the fallback.

## Wan limits

- Wan is a helper, never the default footage source or complete video renderer.
- Wan output must remain photorealistic live action and preserve the reference
  frame's subject, objects and setting.
- At most one stock segment per Short can be enhanced.
- The feature is disabled by default and requires both I2V_ENABLED=1 and
  WAN_STOCK_ASSIST=1 plus a Replicate WAN_API_KEY.
- Paid generation is not enabled in scheduled production without explicit owner
  approval. Provider failures retain the original stock clip.

## Quality gates

- Scene visuals must match the narration, not merely the broad fitness category.
- Keep the established safe title/subtitle zones and bottom caption area.
- Preserve presenter/avatar placement away from captions and important footage.
- Validate render duration, dimensions, audio continuity and output file size.
- Preview-only runs must never upload to YouTube.
