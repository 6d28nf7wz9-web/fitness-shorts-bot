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


## Blender CGI preview (manual / not auto-published)

The experimental Blender scene pipeline is available without changing the daily upload path:

```bash
# Render a safe built-in preview (no YouTube upload)
FITFUEL_PREVIEW_FAST=1 python blender_preview.py --fixture --duration 2.5

# Render scenes from a generated Gemini script, then assemble them with HyperFrames
FITFUEL_3D_PREVIEW=1 FITFUEL_3D_SCENE_SECONDS=4.0 python assemble.py
```

The second command is an explicit local opt-in. The scheduled `.github/workflows/daily.yml` does not set `FITFUEL_3D_PREVIEW`; production continues using the established footage path until the CGI assets and visual review are approved. The manual **Blender 3D preview (safe, no upload)** workflow publishes a 7-day downloadable preview artifact only.


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


## Controlled biceps-curl rig (isolated preview branch)

The branch `feat/fitfuel-controlled-exercise-rig` adds a dedicated Blender test scene for a dumbbell biceps curl. The elbow pivot stays fixed, the forearm follows a deterministic curl arc, the hand and dumbbell share one parent, and the biceps highlight contracts during the rep.

This is still a **preview-only prototype**; it does not alter the daily workflow or publish anything to YouTube.

To render the focused five-second test:
1. Open **Actions → Blender controlled exercise preview**.
2. Select branch `feat/fitfuel-controlled-exercise-rig`.
3. Choose `fast_preview=true` for a quick low-resolution check, or `false` for the higher-quality render.
4. Run the workflow and download the `fitfuel-controlled-exercise-preview` artifact.

The workflow runs syntax and scene-routing checks, renders only the biceps-curl scene, probes the MP4, and retains the preview artifact for 7 days. Review the actual hand grip, dumbbell orientation, elbow stability, and full curl cycle before considering any production integration.
