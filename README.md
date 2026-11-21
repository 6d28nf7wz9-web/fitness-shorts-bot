# fitness-shorts-bot
## HyperFrames Shorts renderer

The daily Shorts pipeline now uses HyperFrames after Gemini script generation,
voice synthesis, and Pixabay clip selection. `hyperframes_render.py` creates one
timed composition per script scene, with scene-specific title/subtitle overlays
and the matching clip as its background. The final FFmpeg mux retains scene voice,
word-level ASS captions, and music.

Typography layout rules:
- scene title and subtitle are in fixed, separate safe zones;
- words wrap before the configured line width and HTML is escaped;
- title/subtitle never share the caption's lower-screen area;
- ASS captions stay bottom-anchored and are width/font fitted;
- HyperFrames lint runs before render and missing/invalid output stops upload.

Production render: portrait 1080×1920 at 30 fps. CI and the daily workflow use Node 22 and HyperFrames CLI 0.9.31.\n\nLocal run: install Node 22, FFmpeg, and `hyperframes@0.9.31` globally, then run `python hyperframes_render.py`.
Set `HYPERFRAMES_RENDER=0` only for an explicit legacy FFmpeg fallback.


## Stock-first visuals with optional Wan assistance

The production visual path uses relevant real footage from **Coverr and Pixabay**
(and optional Pexels/NASA/local licensed assets). Blender/CGI rendering has been
removed from the video assembly path.

Wan is an optional enhancement to one selected stock segment:
- The pipeline first selects and downloads a relevant Coverr/Pixabay clip.
- If explicitly enabled, it extracts a frame from that exact clip and sends the
  frame plus scene narration to Wan 2.2 image-to-video through Replicate.
- The prompt requires photorealistic live-action continuity, not CGI or 3D anatomy.
- At most one stock segment per Short can be enhanced. If Wan fails, the original
  stock clip is retained.
- The feature is hard-locked off in the daily workflow (I2V_ENABLED=0 and
  WAN_STOCK_ASSIST=0). Enabling it requires an intentional workflow change and
  a configured Replicate WAN_API_KEY; generation is a paid API operation.
- The earlier local Wan 2.1 Colab experiment is not part of scheduled production.
  It remains unsuitable as an automatic renderer on the free T4 setup based on
  the one-second/poor-motion preview.

## Multi-source free footage

The Shorts clip selector now aggregates:
- **Pixabay** (existing API key)
- **Coverr** (official video API; set GitHub Actions secret `COVERR_API_KEY`; free Demo tier is limited to 50 requests/hour)
- **Pexels** (official video search API; set GitHub Actions secret `PEXELS_API_KEY`)
- **NASA Image & Video Library** (public API; enabled by `NASA_VIDEO_SEARCH=1`; expect mostly science/space footage, not gym B-roll)
- **Mixkit + Videvo** (no stable public search API is used; import videos downloaded under the applicable free license into `stock_library/` and add a JSON sidecar).

Mixkit/Videvo local sidecar example (`stock_library/fitness_01.json`):
```json
{
  "source": "mixkit",
  "file": "fitness_01.mp4",
  "title": "Athlete doing dumbbell curls",
  "tags": ["biceps", "dumbbell", "gym", "strength"],
  "duration": 12,
  "width": 1920,
  "height": 1080,
  "author": "Contributor name",
  "url": "https://mixkit.co/"
}
```
The MP4 must be in the same folder. Commit this folder to the repository so GitHub Actions can access it. Use only assets whose individual license permits the intended YouTube/commercial use; preserve required attribution. Mixkit has both Free and Restricted licenses; Videvo license/attribution varies by clip. The selector checks local Mixkit/Videvo tags and downloads/copies matching assets into the normal clip pipeline.

Pexels API usage requires attribution/linking to Pexels and photographers where possible. Add the key in GitHub: **Settings → Secrets and variables → Actions → New repository secret → `PEXELS_API_KEY`**. If absent, the provider is skipped without breaking Pixabay. NASA search is optional and can be disabled with `NASA_VIDEO_SEARCH=0`.


Coverr API setup:
- Add repository secret `COVERR_API_KEY` under **Settings → Secrets and variables → Actions → New repository secret**.
- The selector searches `GET https://api.coverr.co/videos` with the official `x-api-key` header and downloads the signed MP4 URL returned by Coverr.
- Search results are cached for 24 hours to reduce API usage. The free Demo tier allows 50 API requests/hour.
- After a Coverr clip is actually downloaded, the pipeline calls Coverr's `PATCH /videos/:id/stats/downloads` tracking endpoint.
- Free Demo API usage requires crediting Coverr and the creator when listed. The upload description adds those credits and links. Coverr's current license allows commercial use, but does not allow redistributing raw stock files, bulk library downloads, or using API content to train AI.
- Sponsored partner assets and watermarked premium previews are excluded by the adapter.


## Optional ArtCraft scene-specific B-roll (additive fallback)

ArtCraft is an optional fourth visual path, not a replacement for Pixabay,
Coverr, Pexels, or the local licensed stock library.

Production order:
1. Search free stock providers for the exact spoken beat.
2. Accept stock only when the existing semantic matcher confirms an exact
   topic match; unrelated clips are rejected.
3. If no exact stock match exists, ArtCraft may generate a vertical,
   scene-specific B-roll cut, subject to an explicit per-run generation budget.
4. If ArtCraft is disabled, unavailable, or fails, retain the existing
   science-visual fallback. HyperFrames can compose verified stock and
   ArtCraft clips in the same scene.

ArtCraft generation is **off by default**. It requires all three settings:
- GitHub Actions secret `ARTCRAFT_API_KEY` (API access is gated by ArtCraft;
  an account may need the provider to enable API keys).
- Repository variable `ARTCRAFT_ENABLED=1`.
- Repository variable `ARTCRAFT_MAX_GENERATIONS` set to a deliberate positive
  integer. This is a hard maximum per Short; default is zero.

Optional settings: `ARTCRAFT_VIDEO_MODEL` (default `seedance_2p0`),
`ARTCRAFT_VIDEO_RESOLUTION` (default `seven_twenty_p`), and
`ARTCRAFT_MAX_WAIT_SECONDS` (default 240). ArtCraft generation can consume
credits and is not assumed to be free. Do not enable it until the account's
API access, model availability, and credit pricing are confirmed.

The provider uses ArtCraft's documented Omni API and downloads the completed
MP4 before passing it through the same FFmpeg normalization and HyperFrames
composition path. It does not upload or publish anything to YouTube.
