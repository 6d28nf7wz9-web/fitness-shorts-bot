import json
import tempfile
import unittest
from pathlib import Path
from three_d_intelligence import PROVIDERS, build_scene_plan, classify_visual_intent, plan_scene, write_scene_plan

class ThreeDIntelligenceTests(unittest.TestCase):
    def test_anatomy_uses_reviewed_science_renderer(self):
        plan = plan_scene({"narration": "Muscle fibers and sarcomeres contract."}, True)
        self.assertEqual(plan["intent"], "scientific_anatomy")
        self.assertEqual(plan["provider"], "local_science")
        self.assertTrue(plan["requires_scientific_review"])
        self.assertFalse(plan["generation_enabled"])

    def test_exercise_form_prefers_real_stock(self):
        plan = plan_scene({"narration": "Watch a correct squat and deadlift form."})
        self.assertEqual(plan["intent"], "exercise_demo")
        self.assertEqual(plan["provider"], "stock")

    def test_worldgen_request_keeps_safe_fallback(self):
        plan = plan_scene({"visual_title": "A modern gym environment"}, True)
        self.assertTrue(plan["generation_requested"])
        self.assertFalse(plan["generation_enabled"])
        self.assertEqual(plan["provider"], "stock")
        self.assertEqual(plan["fallback_provider"], "local_science")

    def test_hunyuan_is_gated_pending_legal_clearance(self):
        self.assertTrue(PROVIDERS["hunyuan3d"]["commercial_clearance_required"])
        plan = plan_scene({"narration": "Show a reusable dumbbell object."}, True)
        self.assertEqual(plan["provider"], "local_science")
        self.assertFalse(plan["generation_enabled"])

    def test_classification_and_id_are_deterministic(self):
        scene = {"narration": "The heart pumps blood and oxygen."}
        self.assertEqual(classify_visual_intent(scene), "scientific_anatomy")
        self.assertEqual(plan_scene(scene)["scene_id"], plan_scene(scene)["scene_id"])

    def test_timeline_plan_and_json_output(self):
        scenes = [{"narration": "Protein synthesis inside a muscle cell."}, {"narration": "A coach demonstrates a shoulder press."}]
        plan = build_scene_plan(scenes, False)
        self.assertEqual(plan["scene_count"], 2)
        self.assertEqual(sum(plan["provider_counts"].values()), 2)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "output" / "scene_plan.json"
            written = write_scene_plan(scenes, path, False)
            self.assertTrue(path.exists())
            self.assertEqual(json.loads(path.read_text())["scene_count"], 2)
            self.assertEqual(written["scene_count"], 2)

if __name__ == "__main__":
    unittest.main()
