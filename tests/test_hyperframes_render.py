import unittest
from hyperframes_render import fit_text, wrap_words
from visual_engine import build_visual_panel, classify_scene, visual_css


class HyperFramesTextLayoutTests(unittest.TestCase):
    def test_title_wraps_inside_safe_line_width(self):
        lines = wrap_words("PROGRESSIVE OVERLOAD BUILDS STRONGER MUSCLES", 20)
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(len(line) <= 20 for line in lines))

    def test_fit_text_keeps_all_words_and_returns_bounded_font(self):
        source = "TRAIN SMARTER RECOVER BETTER AND BUILD MUSCLE"
        lines, size = fit_text(source, 2, 30, 43, 30)
        self.assertEqual(" ".join(lines), source)
        self.assertGreaterEqual(size, 30)
        self.assertLessEqual(size, 43)

    def test_long_title_is_bounded_to_safe_box(self):
        lines, size = fit_text(" ".join(["ANATOMY"] * 40), 3, 20, 78, 48)
        self.assertLessEqual(len(lines), 4)
        self.assertTrue(all(len(line) <= 32 for line in lines))
        self.assertGreaterEqual(size, 48)
        self.assertLessEqual(size, 78)
        self.assertTrue(lines[-1].endswith("…"))

    def test_long_subtitle_is_bounded_to_safe_box(self):
        lines, size = fit_text(" ".join(["TRAINING"] * 30), 2, 30, 43, 30)
        self.assertLessEqual(len(lines), 3)
        self.assertTrue(all(len(line) <= 43 for line in lines))
        self.assertGreaterEqual(size, 30)
        self.assertLessEqual(size, 43)
        self.assertTrue(lines[-1].endswith("…"))

    def test_empty_subtitle_has_safe_fallback(self):
        self.assertEqual(wrap_words("", 30), [""])

    def test_daily_workflow_installs_renderer_and_sets_public_mode(self):
        with open(".github/workflows/daily.yml", encoding="utf-8") as f:
            workflow = f.read()
        self.assertIn('node-version: "22"', workflow)
        self.assertIn("hyperframes@0.9.31", workflow)
        self.assertIn("UPLOAD_PRIVACY: public", workflow)
        self.assertIn('HYPERFRAMES_RENDER: "1"', workflow)
        self.assertNotIn(r"public\n", workflow)

    def test_scene_visuals_classify_common_fitness_topics(self):
        self.assertEqual(classify_scene({"narration": "Water improves hydration"}), "hydration")
        self.assertEqual(classify_scene({"narration": "Protein supports muscle growth"}), "muscle")
        self.assertEqual(classify_scene({"narration": "Insulin is a hormone signal"}), "hormones")
        self.assertEqual(classify_scene({"narration": "Calories determine energy balance"}), "fat_loss")

    def test_each_topic_has_distinct_visual_metaphor(self):
        cases = {
            "muscle": "Muscle fibers adapt to mechanical tension",
            "nutrition": "Food digestion and nutrient absorption",
            "heart": "Heart pumps blood and oxygen",
            "fat_loss": "Calorie deficit and fat loss",
            "hydration": "Water and electrolyte balance",
            "exercise": "Squat exercise and joint movement",
            "hormones": "Insulin hormone receptor signaling",
        }
        panels = {}
        for expected, narration in cases.items():
            category, panel = build_visual_panel({"narration": narration}, 7)
            self.assertEqual(category, expected)
            self.assertIn(f"panel-{expected}", panel)
            self.assertIn('data-scene="7"', panel)
            panels[expected] = panel
        self.assertEqual(len(set(panels.values())), len(cases))
        self.assertIn("fiber-group", panels["muscle"])
        self.assertIn("heart-shape", panels["heart"])
        self.assertIn("electrolytes", panels["hydration"])
        self.assertIn("receptor", panels["hormones"])

    def test_dynamic_scene_labels_are_escaped(self):
        _, panel = build_visual_panel({
            "narration": "Muscle recovery",
            "visual_title": "<script>alert(1)</script>",
            "visual_subtitle": "Repair & rebuild",
        }, 4)
        self.assertNotIn("<script>", panel)
        self.assertIn("&lt;script&gt;", panel)
        self.assertIn("Repair &amp; rebuild", panel)

    def test_svg_ids_are_unique_per_scene(self):
        _, first = build_visual_panel({"narration": "Muscle growth"}, 1)
        _, second = build_visual_panel({"narration": "Heart rate"}, 2)
        self.assertIn('id="panelGlow1"', first)
        self.assertIn('id="panelGlow2"', second)
        self.assertIn("@keyframes heartbeat", visual_css())


if __name__ == "__main__":
    unittest.main()
