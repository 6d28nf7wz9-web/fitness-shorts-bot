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
