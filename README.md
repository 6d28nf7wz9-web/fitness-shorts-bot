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

Local run: `python hyperframes_render.py` (Node 22+, FFmpeg, HyperFrames).
Set `HYPERFRAMES_RENDER=0` only for an explicit legacy FFmpeg fallback.
