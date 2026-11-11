import unittest
from blender_preview import FAMILY_TO_BLENDER, FIXTURE, load_script, scene_kind


class BlenderPreviewTests(unittest.TestCase):
    def test_fixture_has_scene_coverage(self):
        self.assertGreaterEqual(len(FIXTURE["scenes"]), 4)
        self.assertEqual(len({scene_kind(s) for s in FIXTURE["scenes"]}), 4)

    def test_narration_routes_to_specialist_scene(self):
        self.assertEqual(scene_kind({"narration": "stomach digestion and gut fiber"}), "digestion_fiber")
        self.assertEqual(scene_kind({"narration": "sleep and recovery"}), "recovery_sleep")
        self.assertEqual(scene_kind({"narration": "protein synthesis in muscle"}), "muscle_anatomy")

    def test_every_registry_family_has_a_blender_route(self):
        self.assertEqual(set(FAMILY_TO_BLENDER), {
            "exercise_biomechanics", "muscle_anatomy", "digestive_system",
            "food_nutrition", "metabolism_hormones", "hydration",
            "sleep_recovery", "general_science",
        })

    def test_fixture_loader_is_offline_and_deterministic(self):
        self.assertEqual(load_script("does-not-exist.json", fixture=True), FIXTURE)


if __name__ == "__main__":
    unittest.main()
