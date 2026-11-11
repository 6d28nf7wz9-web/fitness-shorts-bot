# ViMax standalone evaluation (experimental)

This experiment is intentionally isolated from the production Shorts/Long workflows.

## Current status

- The branch is based on the existing `main` pipeline.
- ViMax is evaluated as a separate upstream project: https://github.com/HKUDS/ViMax
- No ViMax code has been vendored into this repository and no production workflow is changed.
- Static review only so far. A rendered video has **not** been produced in this environment.

## Why this is the first candidate

ViMax provides a Script2Video pipeline: explicit script -> character/storyboard planning -> shot decomposition -> keyframes -> generated video clips -> final video. Its upstream README documents Script2Video and a browser UI. The upstream project is MIT licensed.

## Requirements / cost gate

Upstream currently requires Python 3.12+ and recommends `uv sync`. The documented Script2Video example uses:
- OpenRouter chat model (Gemini model routed through OpenRouter)
- Google Nano Banana image generation
- Google Veo video generation

These are external model services. The ViMax source code is open source, but model generation is not automatically free or unlimited. API keys, provider availability, billing/credits, and rate limits must be in place. The sample config has image/video limits of 2 requests/minute and 50/day.

## FitFuel test case

Use `test_script.txt` as a small, real excerpt from the existing L001 long-video script. The first evaluation should be deliberately small (3-4 shots maximum) to limit cost and turnaround time.

Requested visual direction:
- consistent cinematic 3D anatomical fitness explainer
- realistic human anatomy / muscle groups where relevant
- scene visuals must directly illustrate the narration
- avoid generic unrelated gym montage
- portrait 9:16 if supported by the selected generator; verify output dimensions rather than assuming
- no generated text inside footage; titles/captions remain the responsibility of our existing renderer

## Acceptance checklist

Do not integrate or replace Pixabay/HyperFrames unless the generated sample passes all of these:
1. Every shot matches the specific narration beat.
2. Visual identity stays consistent across shots.
3. Anatomy is credible and readable, not distorted.
4. Output is usable in portrait format and has adequate resolution.
5. No unwanted text, logos, or watermarks in generated footage.
6. We can estimate cost per 30 seconds and per 3-minute video.
7. The generated clips can be handed to our current renderer without changing production behavior.

## Next execution step

Run ViMax from its own checkout (not inside the production pipeline), configure the OpenRouter and Google provider keys in the local environment / GitHub Actions secrets, then run Script2Video with `test_script.txt`. Save the final MP4 and intermediate storyboard/keyframes as an artifact for visual review.

Do not place API keys in tracked files. Do not enable automatic uploads. Do not merge this branch into `main` until the output is approved.
