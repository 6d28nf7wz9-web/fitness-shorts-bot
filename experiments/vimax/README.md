# ViMax FitFuel preview runner

This remains an isolated evaluation on `experiment/vimax-standalone-evaluation`; production workflows and `main` are untouched.

## What the preview does
- Uses the real FitFuel protein / muscle-growth excerpt in `test_script.txt`.
- Requests at most 3 shots and a consistent cinematic 3D anatomical fitness-explainer identity.
- Uses one image candidate to limit generation calls.
- Patches only the temporary ViMax checkout to use Nano Banana 2 image generation and Veo 3.1 Fast at 720p, both requested in portrait 9:16.
- Uploads the MP4, storyboard and first frames as a GitHub Actions artifact for 7 days.

## Current test result
- ViMax installed successfully.
- Gemini 3.5 Flash-Lite generated a 3-shot storyboard and decomposed the shot descriptions.
- Rendering stopped at image generation: Google's free tier does not provide a free quota for the current image-generation models. The first image request was rejected with quota error, and upstream ViMax's error handler masked it with a `status_code` attribute bug.
- No MP4 has been produced. The latest failed run artifact contains the storyboard only.

## Credentials and paid-render guard
The workflow reuses the repository's existing `GEMINI_API_KEY` Actions secret. Chat planning uses Gemini 3.5 Flash-Lite. Image generation is configured for Nano Banana 2 (`gemini-3.1-flash-image`), and video generation uses Veo 3.1 Fast at 720p in portrait 9:16.

**Paid rendering is deliberately disabled by default.** The job runs only when the repository Actions variable `VIMAX_PAID_RENDER` is set to `true`. The 3-shot test is capped at about 24 seconds of Veo output: at the published Veo 3.1 Fast 720p rate of $0.10/second, this is approximately **$2.40** for video, plus about **$0.067 per 1K generated image** (likely 3–6 images, roughly $0.20–$0.40). Expected total is roughly **$2.60–$2.80**, but actual charges depend on shot count, image count and billing. Chat planning uses Flash-Lite and remains subject to its free-tier quota.

To enable after explicit approval: add the repository Actions variable `VIMAX_PAID_RENDER=true` under Settings -> Secrets and variables -> Actions -> Variables. The existing `GEMINI_API_KEY` secret is used; never put keys in tracked files or chat. Do not enable the variable until the user approves paid generation.

## Run / retrieve
The workflow is `.github/workflows/vimax-fitfuel-preview.yml`. It uploads `FitFuel-ViMax-preview` after a completed run. Open the Actions run and download the artifact. Artifact retention is 7 days.

No automatic YouTube upload is enabled.

## Deterministic Blender fallback preview

The companion workflow `.github/workflows/fitfuel-script-preview.yml` renders the same FitFuel protein script without paid image-generation APIs:

- Edge TTS narration using `en-US-AndrewNeural`
- Blender scenes selected by explicit `visual_type` and timed to each narration segment
- HyperFrames is not required for this isolated fallback; `assemble.py` performs the final FFmpeg mux with the repository captions and music
- Output: 480x854 portrait source scenes, final H.264/AAC MP4 at 30 fps
- The workflow uploads a 7-day artifact and never publishes to YouTube

The first ViMax attempt reached storyboard generation but failed when Google returned HTTP 429 for `gemini-2.5-flash-preview-image` (free-tier quota limit is zero for that model). The ViMax workflow is therefore manual-only; it must not be treated as a successful render or silently retried against the same exhausted quota.

The Blender output is a stylized procedural 3D preview, not photorealistic anatomical CGI. Review the actual artifact before any production adoption.

