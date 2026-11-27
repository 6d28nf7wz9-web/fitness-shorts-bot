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

    def test_preview_workflow_has_independent_upload_barrier(self):
        with open(".github/workflows/daily.yml", encoding="utf-8") as f:
            workflow = f.read()
        upload_step = workflow.split("      - name: Upload to YouTube", 1)[1].split(
            "      - name: Save preview video artifact", 1
        )[0]
        self.assertIn("github.event_name == 'schedule'", upload_step)
        self.assertIn("github.event_name == 'push'", workflow)
        self.assertIn("SKIP_UPLOAD: ${{ (github.event_name == 'push' || (github.event_name == 'workflow_dispatch' && inputs.preview_only)) && '1' || '' }}", workflow)
        self.assertIn("default: true", workflow)
        preview_step = workflow.split("      - name: Save preview video artifact", 1)[1].split(
            "      - name: Save learning data", 1
        )[0]
        self.assertIn("github.event_name == 'push'", preview_step)

    def test_render_fixture_composites_audio_reactive_presenter(self):
        with open(".github/workflows/hyperframes-integration.yml", encoding="utf-8") as f:
            workflow = f.read()
        self.assertIn("python -m pip install numpy pillow", workflow)
        self.assertIn("python avatar.py short", workflow)
        self.assertIn("test -s output/final.mp4.avatar", workflow)

    def test_render_has_distinct_scene_layout_compositions(self):
        with open("hyperframes_render.py", encoding="utf-8") as f:
            renderer = f.read()
        for layout in ("hook", "payoff", "stat_card", "comparison", "timeline",
                       "presenter_focus", "broll_focus", "diagram"):
            self.assertIn(f".scene-layout-{layout}", renderer)
        self.assertIn("scene-layout-presenter_focus .science-panel", renderer)
        self.assertIn("scene-layout-comparison .science-panel:after", renderer)

    def test_renderer_has_distinct_motion_design_for_scene_roles(self):
        with open("hyperframes_render.py", encoding="utf-8") as f:
            renderer = f.read()
        for animation in ("hook-impact", "payoff-settle", "stat-pop", "split-open",
                          "timeline-rise", "panel-slide-left", "diagram-draw",
                          "scene-progress"):
            self.assertIn(f"@keyframes {animation}", renderer)
        self.assertIn("motion-{html.escape(str(scene.get", renderer)
        self.assertIn("--scene-duration:{enddur}s", renderer)

    def test_integration_fixture_uses_cinematic_background_not_test_pattern(self):
        with open(".github/workflows/hyperframes-integration.yml", encoding="utf-8") as f:
            workflow = f.read()
        self.assertIn("noise=alls=10", workflow)
        self.assertIn("boxblur=18:2", workflow)
        self.assertIn("drawbox=x=110", workflow)
        self.assertNotIn("testsrc2=s=1080x1920", workflow)

    def test_scene_visuals_classify_common_fitness_topics(self):
        self.assertEqual(classify_scene({"narration": "Water improves hydration"}), "hydration")
        self.assertEqual(classify_scene({"narration": "Protein supports muscle growth"}), "muscle")
        self.assertEqual(classify_scene({"narration": "Insulin is a hormone signal"}), "hormones")

    def test_visual_panel_is_scene_specific_and_animated(self):
        category, panel = build_visual_panel({"narration": "Heart rate and blood flow deliver oxygen"}, 3)
        self.assertEqual(category, "heart")
        self.assertIn('data-scene="3"', panel)
        self.assertIn("CARDIOVASCULAR", panel)
        self.assertIn("science-svg", panel)
        self.assertIn("@keyframes orbit-dash", visual_css())

    def test_visual_panel_escapes_dynamic_text(self):
        category, panel = build_visual_panel({"narration": "<script> muscle recovery"})
        self.assertEqual(category, "muscle")
        self.assertNotIn("<script>", panel)


if __name__ == "__main__":
    unittest.main()
