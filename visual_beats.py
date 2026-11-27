"""Sentence/phrase-level visual beat planner for narration-aligned illustrations."""
import html
import re

from visual_engine import build_visual_panel


def split_visual_beats(narration, max_words=7):
    """Split narration into readable semantic beats; never create one meaningless icon per word."""
    text = re.sub(r"\s+", " ", str(narration or "")).strip()
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?;:])\s+", text)
    beats = []
    for sentence in sentences:
        words = sentence.split()
        while len(words) > max_words:
            # Prefer clause boundaries; otherwise use a fixed readable phrase window.
            cut = max_words
            for i in range(max_words, max(2, max_words - 3), -1):
                if words[i - 1].lower().rstrip(",") in {"and", "but", "because", "while", "which", "that", "so", "then"}:
                    cut = i
                    break
            beats.append(" ".join(words[:cut]).strip(" ,;:"))
            words = words[cut:]
        if words:
            beats.append(" ".join(words).strip(" ,;:"))
    return [b for b in beats if b]


def build_visual_beat_overlays(scene, duration, scene_index, absolute_start):
    """Create one dedicated explanatory illustration per phrase, covering the full narration interval."""
    beats = split_visual_beats(scene.get("narration", ""))
    if not beats:
        beats = [str(scene.get("visual_title") or "THE SCIENCE")]
    weights = [max(1, len(x.split())) for x in beats]
    total_weight = sum(weights)
    cursor = float(absolute_start)
    overlays = []
    for beat_index, (beat, weight) in enumerate(zip(beats, weights), 1):
        beat_duration = float(duration) * weight / total_weight
        beat_scene = dict(scene)
        beat_scene["narration"] = beat
        beat_scene["visual_title"] = beat
        beat_scene["visual_subtitle"] = ""
        _, panel = build_visual_panel(beat_scene, scene_index * 100 + beat_index)
        panel = panel.replace('class="science-panel ', 'class="science-panel visual-beat ', 1)
        label = html.escape(beat, quote=True)
        panel = panel.replace("</div>", f'<div class="visual-beat-label">{label}</div></div>', 1)
        overlays.append(
            f'<div class="clip visual-beat-clip" data-start="{cursor:.3f}" '
            f'data-duration="{beat_duration:.3f}" data-track-index="2">{panel}</div>'
        )
        cursor += beat_duration
    return overlays


def visual_beat_css():
    return """
.visual-beat{top:990px!important;height:570px!important;left:72px!important;right:72px!important;
  animation:visual-beat-enter .28s ease-out both}
.visual-beat .science-svg{top:145px!important;height:350px!important}
.visual-beat-label{position:absolute;left:30px;right:30px;top:94px;z-index:3;
  color:#f5f8ff;font-size:20px;font-weight:800;line-height:1.18;text-align:center;
  text-shadow:0 2px 12px #000;max-height:48px;overflow:hidden}
@keyframes visual-beat-enter{from{opacity:0;transform:translateY(18px) scale(.985)}
 to{opacity:1;transform:translateY(0) scale(1)}}
"""
