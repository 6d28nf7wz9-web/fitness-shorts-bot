# ViMax FitFuel preview runner

This remains an isolated evaluation on `experiment/vimax-standalone-evaluation`; production workflows and `main` are untouched.

## What the preview does
- Uses the real FitFuel protein / muscle-growth excerpt in `test_script.txt`.
- Requests at most 3 shots and a consistent cinematic 3D anatomical fitness-explainer identity.
- Uses one image candidate to limit generation calls.
- Patches only the temporary ViMax checkout's Google Veo adapter to request `9:16` portrait video. The patch is not applied to the production repository or upstream.
- Uploads the MP4, storyboard and first frames as a GitHub Actions artifact for 7 days.

## Credentials
The workflow reuses the repository's existing `GEMINI_API_KEY` Actions secret for Gemini chat planning, Google image generation and Veo video generation. No API key is stored in the repository or printed in logs.

The render uses external paid / credit-limited APIs. The workflow checks that the secret exists before installing or generating anything.

## Run / retrieve
The workflow is `.github/workflows/vimax-fitfuel-preview.yml`. A push to this experiment branch triggers it; it can also be run manually after the workflow is available on the repository's default branch. When complete, open the Actions run and download the `FitFuel-ViMax-preview` artifact. Artifact retention is 7 days.

## Known evaluation limitation
The pipeline generates visual shots from still keyframes and Veo clips; this first test is about style, anatomy, continuity, and script-to-scene matching. Review the actual MP4 dimensions and output before considering any production integration. No automatic YouTube upload is enabled.
