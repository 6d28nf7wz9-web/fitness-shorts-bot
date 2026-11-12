# FitFuel stock-first Wan assistance

## Production visual strategy

The Short is assembled from scene-matched real footage. Coverr and Pixabay are
the primary sources; Pexels, NASA and imported licensed stock remain optional
additional sources. The stock selector and relevance checks remain responsible
for choosing footage that matches each scene.

Wan is a supplementary tool, not the primary video renderer. When deliberately
enabled, the pipeline:
1. Selects and downloads a relevant Coverr/Pixabay stock clip.
2. Extracts one representative frame from that exact clip.
3. Sends that frame and the scene narration to Wan 2.2 image-to-video through
   Replicate, requesting subtle photorealistic live-action motion.
4. Uses the Wan result for that single segment only. If generation fails, it
   keeps the original stock footage.

The workflow allows no more than one Wan-enhanced segment per Short. Captions,
voice, music, HyperFrames typography and presenter/avatar compositing remain
separate and unchanged.

## Safety and cost defaults

- Wan assistance is disabled in the scheduled workflow:
  - I2V_ENABLED=0
  - WAN_STOCK_ASSIST=0
- Both switches must be intentionally enabled before any paid API request can
  happen.
- WAN_API_KEY must be a Replicate API token. The configured model is
  wan-video/wan-2.2-i2v-a14b; this is not the local Wan 2.1 Colab checkpoint.
- Only one stock segment is eligible per Short, and there is no paid-provider
  retry or fallback chain.
- If Wan is disabled, unconfigured, times out or fails, the selected Coverr/
  Pixabay clip remains the final visual.
- No scheduled job runs Blender or any 3D render step.

Do not enable paid Wan generation until the expected Replicate cost and one
sampled result have been reviewed. The free Colab T4 Wan 2.1 route is kept out of
the production workflow because its previous preview was too short and had
unreliable exercise motion.
