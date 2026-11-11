# FitFuel hybrid Image-to-Video (I2V)

## Safety defaults

- Image-to-video is **disabled by default**. The production workflow passes provider secrets only to the footage step, but no paid API request is made unless `I2V_ENABLED=1`.
- The integration makes one request to exactly one selected provider. It does not retry a paid generation or cascade to another paid provider.
- At most two scenes per Short can be generated (`I2V_MAX_SCENES` is hard-capped at 2).
- Each provider is configured for a five-second generation. The existing FFmpeg scene processor then fits/loops that source to the narration duration.
- If the feature is disabled, a still image is missing, or a provider fails, the scene uses the existing stock-footage pipeline.
- Tests mock all provider requests. CI never calls Kling, Runway, or Replicate.

## Still-image inputs

The current pipeline does not yet generate AI still images automatically. Until a separate still-image stage is approved and implemented, place prepared 3D reference stills here:

- `output/i2v_inputs/scene_1.png`
- `output/i2v_inputs/scene_2.png`

JPEG is also accepted (`.jpg` / `.jpeg`). Use portrait images where possible, at least 300 px on each side. The input file must be 5 MB or smaller. The still should already depict the exact anatomy/subject to preserve; the I2V prompt adds only subtle motion and camera movement.

## GitHub Actions configuration

The daily workflow exposes these environment variables only to the `clips_fast.py` step:

| Variable | Default | Purpose |
|---|---:|---|
| `I2V_ENABLED` | `0` | Master switch; leave off until the owner explicitly approves a paid generation |
| `I2V_PROVIDER` | `kling` | One of `kling`, `runway`, `wan` |
| `I2V_MAX_SCENES` | `2` | Number of eligible early scenes, hard-capped at 2 |

Provider credentials are read from repository Actions secrets:

- `KLING_API_KEY`
- `RUNWAY_API_KEY`
- `WAN_API_KEY` — this must be a **Replicate API token** for the official `wan-video/wan-2.2-i2v-a14b` model; Wan 2.2 itself does not issue a universal API key.

Do not set `I2V_ENABLED=1` until the still-image inputs, provider account balance, model selection, and expected cost have been reviewed and the owner has explicitly approved generation. The feature remains off unless that variable is deliberately changed.

## Provider implementation

- Kling: official Kling 2.5 Turbo image-to-video endpoint; task polling by task ID.
- Runway: official Runway Dev `/v1/image_to_video` endpoint using `gen4_turbo`, with the documented API version header.
- Wan 2.2: Replicate's official `wan-video/wan-2.2-i2v-a14b` prediction endpoint.

All output is downloaded to a temporary raw path and normalized to the existing 1080x1920 scene format by `clips.process`. Captions, voice, presenter placement, and HyperFrames composition remain unchanged.
