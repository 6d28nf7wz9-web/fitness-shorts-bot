import unittest
from visual_scene_registry import resolve_scene_family, build_visual_contract

class VisualSceneRegistryTests(unittest.TestCase):
    def test_routes_exercise_to_biomechanics(self):
        self.assertEqual(resolve_scene_family("Show a squat and the quadriceps working"), "exercise_biomechanics")
    def test_routes_digestion_to_organs(self):
        self.assertEqual(resolve_scene_family("Follow food through the stomach and intestines"), "digestive_system")
    def test_routes_food_to_photoreal_assets(self):
        self.assertEqual(resolve_scene_family("Build a meal with protein and vegetables"), "food_nutrition")
    def test_routes_hormones_to_cellular_assets(self):
        self.assertEqual(resolve_scene_family("Insulin and glucose metabolism"), "metabolism_hormones")
    def test_contract_requires_real_assets_and_preview_approval(self):
        contract = build_visual_contract("Dietary fiber reaches the colon", "Fiber digestion")
        self.assertEqual(contract["family"], "digestive_system")
        self.assertTrue(contract["requires_approved_assets"])
        self.assertTrue(contract["preview_only_until_approved"])
        self.assertIn("peristalsis", contract["required_motion"])

if __name__ == "__main__":
    unittest.main()
