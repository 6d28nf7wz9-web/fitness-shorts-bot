"""Scene-aware body language and facial accents for the existing FitFuel avatar."""
import json

from production_motion_engine import presenter_expression, presenter_gesture
from visual_engine import classify_scene


def scene_motion_cues(layout, script_path="output/script.json", audio_path="output/audio_info.json"):
    """Map spoken scenes to timecoded presenter gesture/expression cues."""
    if layout != "short":
        return []
    try:
        with open(script_path, encoding="utf-8") as f:
            scenes = json.load(f).get("scenes", [])
        with open(audio_path, encoding="utf-8") as f:
            audio = json.load(f)
    except (OSError, ValueError, TypeError):
        return []

    cues, cursor = [], 0.0
    for scene, timing in zip(scenes, audio):
        duration = max(0.0, float(timing.get("seconds", 0)))
        category = classify_scene(scene)
        narration = scene.get("narration", "")
        cues.append({
            "start": round(cursor, 3),
            "end": round(cursor + duration, 3),
            "gesture": presenter_gesture(narration, category),
            "expression": presenter_expression(narration, category),
        })
        cursor += duration
    return cues


def ffmpeg_motion_expression(cues, component):
    """Build a bounded FFmpeg expression for subtle per-scene avatar motion."""
    expression = "0"
    for cue in reversed(cues):
        gesture = cue.get("gesture", "talk")
        start, end = float(cue["start"]), float(cue["end"])
        phase = f"(t-{start:.3f})"
        if component == "angle":
            settings = {
                "point": "0.090+0.035*sin(2*PI*" + phase + "*0.65)",
                "explain": "0.070*sin(2*PI*" + phase + "*0.7)",
                "compare": "0.080*sin(2*PI*" + phase + "*1.0)",
                "demonstrate": "0.075*sin(2*PI*" + phase + "*0.85)",
                "talk": "0.050*sin(2*PI*" + phase + "*0.55)",
            }
        elif component == "x":
            settings = {
                # Larger, scene-specific shifts prevent the presenter from feeling pinned.
                "point": "18+14*sin(2*PI*" + phase + "*0.65)",
                "explain": "12*sin(2*PI*" + phase + "*0.7)",
                "compare": "22*sin(2*PI*" + phase + "*1.0)",
                "demonstrate": "16*sin(2*PI*" + phase + "*0.85)",
                "talk": "8*sin(2*PI*" + phase + "*0.55)",
            }
        else:
            raise ValueError("component must be 'angle' or 'x'")
        value = settings.get(gesture, settings["talk"])
        expression = f"if(between(t,{start:.3f},{end:.3f}),{value},{expression})"
    return expression


def apply_expression_mouth_states(states, expression_events, fps=30):
    """Use existing avatar mouth sprites for brief expression accents, preserving lip sync."""
    result = list(states)
    for event in expression_events or []:
        start = max(0, int(float(event.get("start", 0)) * fps))
        end = min(len(result), start + max(1, int(0.23 * fps)))
        target = {"smile": "wide", "surprise": "open", "concern": "round"}.get(
            event.get("expression")
        )
        if target:
            for frame in range(start, end):
                if result[frame] != "closed":
                    result[frame] = target
    return result
