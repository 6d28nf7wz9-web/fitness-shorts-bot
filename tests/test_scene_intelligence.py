import unittest

from scene_intelligence import route_scene


class SceneRoutingTests(unittest.TestCase):
    def test_mechanism_routes_to_blender(self):
        route = route_scene({
            "visual_title": "Insulin signaling",
            "visual_subtitle": "Hormone binds to receptor",
            "narration": "Insulin sends a signal that helps cells take up glucose.",
        })
        self.assertEqual(route["source"], "blender")
        self.assertEqual(route["category"], "hormones")

    def test_observable_exercise_routes_to_stock_then_artcraft(self):
        route = route_scene({
            "visual_title": "Romanian Deadlift",
            "visual_subtitle": "Hip hinge technique",
            "narration": "Watch the athlete perform a Romanian deadlift.",
        })
        self.assertEqual(route["source"], "stock_then_artcraft")

    def test_explicit_anatomy_type_overrides_generic_words(self):
        route = route_scene({
            "visual_type": "muscle_anatomy",
            "visual_title": "Glute activation",
            "narration": "Show the athlete doing a hip thrust.",
        })
        self.assertEqual(route["source"], "blender")

    def test_food_preparation_prefers_real_footage(self):
        route = route_scene({
            "visual_title": "High protein meal",
            "visual_subtitle": "Prepare a balanced plate",
            "narration": "Watch someone cooking and chopping vegetables.",
            "visual_type": "food_nutrition",
        })
        self.assertEqual(route["source"], "stock_then_artcraft")


if __name__ == "__main__":
    unittest.main()
