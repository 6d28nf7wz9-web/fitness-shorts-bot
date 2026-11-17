# Production motion preview checkpoint

This branch is an isolated preview lane. Push-triggered Daily Short runs set
SKIP_UPLOAD=1 and save a `fitfuel-short-preview` artifact; they must not publish
to YouTube.

Current motion work:
- Edge TTS word-boundary timing is persisted in audio_info.json.
- Kinetic word animations use global scene offsets.
- Scene-specific scientific panels and motion direction are rendered by
  hyperframes_render.py.
- Sentence-level narration context is passed to B-roll matching.
- Sparse sound cues are generated and mixed during final assembly.
- The existing lip-synced presenter remains the only presenter layer.

Review gate: inspect the rendered MP4 for word/audio synchronization, scene
specificity, B-roll relevance, presenter safe-zone, transition continuity, and
sound balance before merging this branch into main.
