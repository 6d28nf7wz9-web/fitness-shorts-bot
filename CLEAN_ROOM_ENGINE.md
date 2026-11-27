# FitFuel Clean-Room Production Engine

This is a separate production path, not a redesign of the previous HyperFrames/visual-card engine.

## Architecture references
- DirectorX: director, footage analysis, story, beat grounding, sound, render, independent review.
- Footage Retrieval Automation: sentence-level footage retrieval, exact narration timing, least-used assets.
- OpenMontage: stage contracts, explicit production decisions, approval gates, post-render quality review. Its AGPL-3.0 code is not copied.
- ClipAtlas: separate media understanding/indexing from creative orchestration. Its AGPLv3 implementation is not copied.
- ShortForge: sourced footage, provenance, QC, human checkpoints. Its AGPL-3.0 code is not copied.
- iart-ai/motion-skills: MIT production craft guidance for kinetic typography, B-roll, and render/inspect iteration; no 3D/WebGL packs are used.
- Video Editing Kit: local FFmpeg/Python editing and project organization patterns.

## New visual grammar
Full-bleed real footage, sentence-grounded shot selection, restrained editorial grading, subtle camera drift, narration-synchronized subtitles, and deliberate shot changes. No presenter box, science-card panels, old SVG anatomy system, old scene layouts, HyperFrames, Blender, or paid generation.

## Existing FitFuel assets retained narrowly
output/script.json and output/audio_info.json are input contracts. clips.search, clips.pick_file, and clips.download are transport adapters for existing free-stock sources only. All planning, scoring, selection, edit decisions, subtitles, and rendering are new.

## Run
python fitfuel_cleanroom.py --plan-only builds a storyboard.
python fitfuel_cleanroom.py retrieves unused stock footage and renders output/cleanroom/final.mp4.

No upload or publish stage exists in this engine. Keep the workflow preview-only until the owner approves the result.
