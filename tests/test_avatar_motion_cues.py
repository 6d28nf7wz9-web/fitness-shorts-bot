import json
import tempfile
import unittest
from pathlib import Path

from avatar_motion import (
    apply_expression_mouth_states,
    ffmpeg_motion_expression,
    scene_motion_cues,
)


class AvatarMotionCueTests(unittest.TestCase):
    def test_scene_cues_follow_spoken_intent_and_accumulate_timestamps(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "script.json"
            audio = Path(tmp) / "audio.json"
            script.write_text(json.dumps({"scenes": [
                {"visual_title": "Squat Form", "narration": "Look at this squat. Great progress."},
                {"visual_title": "Training Comparison", "narration": "Compare these two methods."},
            ]}), encoding="utf-8")
            audio.write_text(json.dumps([
                {"seconds": 2.5}, {"seconds": 3.0},
            ]), encoding="utf-8")
            cues = scene_motion_cues("short", str(script), str(audio))
        self.assertEqual(cues[0]["gesture"], "point")
        self.assertEqual(cues[0]["expression"], "smile")
        self.assertEqual(cues[1]["gesture"], "compare")
        self.assertEqual(cues[1]["start"], 2.5)
        self.assertEqual(cues[1]["end"], 5.5)

    def test_gesture_motion_expression_changes_by_scene(self):
        cues = [
            {"start": 0, "end": 2, "gesture": "point"},
            {"start": 2, "end": 4, "gesture": "compare"},
        ]
        angle = ffmpeg_motion_expression(cues, "angle")
        x = ffmpeg_motion_expression(cues, "x")
        self.assertIn("between(t,0.000,2.000)", angle)
        self.assertIn("between(t,2.000,4.000)", angle)
        self.assertIn("sin(", angle)
        self.assertIn("sin(", x)
        self.assertEqual(ffmpeg_motion_expression([], "angle"), "0")

    def test_scene_gestures_have_visible_but_bounded_motion(self):
        cues = [
            {"start": 0, "end": 2, "gesture": "point"},
            {"start": 2, "end": 4, "gesture": "compare"},
        ]
        angle = ffmpeg_motion_expression(cues, "angle")
        x = ffmpeg_motion_expression(cues, "x")
        self.assertIn("0.065+0.025*sin", angle)
        self.assertIn("0.060*sin", angle)
        self.assertIn("18+14*sin", x)
        self.assertIn("22*sin", x)

    def test_expression_accents_preserve_closed_mouth_frames(self):
        states = ["mid", "closed", "open", "wide"]
        result = apply_expression_mouth_states(
            states, [{"start": 0, "expression": "smile"}], fps=30
        )
        self.assertEqual(result, ["wide", "closed", "wide", "wide"])
        self.assertEqual(states, ["mid", "closed", "open", "wide"])

    def test_short_presenter_overlay_stays_inside_fixed_anchor_box(self):
        from pathlib import Path
        source = Path("avatar.py").read_text(encoding="utf-8")
        self.assertIn('overlay=x={SHORT_AVATAR_X}:y={SHORT_AVATAR_Y}', source)
        self.assertNotIn("overlay=x='{SHORT_AVATAR_X}+({x_expr})'", source)

    def test_long_layout_has_no_short_scene_cues(self):
        self.assertEqual(scene_motion_cues("long"), [])


if __name__ == "__main__":
    unittest.main()
