# FitFuel Text-to-Video preflight (free-only)

## What this branch adds

- Converts each Gemini scene's narration + visual title into a provider-ready prompt.
- Keeps the channel's consistent 3D anatomical fitness-explainer identity.
- Creates `output/t2v_prompt_plan.json` with one prompt per scene, 9:16 format, and a target clip length of 3–5 seconds.
- Adds the prompt plan to the preview artifact for inspection.
- Makes **zero** requests to Kling, Runway, or Wan. No credits can be consumed by this stage.

## Why generation is currently blocked

An API key only proves authentication; it does not prove that the account has free API credits.

As of 2026-11-11, the official published terms indicate:

- **Kling Developer API:** video API resource packages are prepaid/balance-based. The API documentation directs users to purchase video resource packages.
- **Runway Dev API:** API generation consumes Runway Dev credits. Runway's one-time 125-credit Free plan is for the Runway app and is separate from Dev API credits.
- **Wan 2.2 hosted through Replicate:** the hosted model is billed per generated second.

Therefore, none of the three credentials can safely be assumed to have free API quota. This branch intentionally does not test by submitting a generation request, because even a short test may incur a charge. The app's browser free credits must not be confused with API credits.

## Current behavior

1. Gemini writes the script.
2. Voiceover creates per-scene audio timings.
3. `text_to_video.py` writes the Text-to-Video prompt plan.
4. `clips_fast.py` continues to use the existing relevant stock-footage route.
5. The preview artifact contains both `final.mp4` and `t2v_prompt_plan.json`.

The existing Image-to-Video path remains hard-locked off. No Kling, Runway, or Wan API request is made by this branch.

## What is needed to unlock a genuine free test

We need a provider dashboard/API response that explicitly confirms an API-specific free balance or a provider-enforced no-charge quota. A website trial credit, a non-empty key, or a billing dashboard with a payment method is not sufficient. Once that evidence exists, the provider can be enabled with a strict per-run scene cap and a no-paid-fallback rule.
