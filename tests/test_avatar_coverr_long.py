import ast
import pathlib
import unittest
from unittest.mock import patch

from long_assemble import stock_attribution
from long_clips import track_stock_download


def read_avatar_layouts():
    tree = ast.parse(pathlib.Path("avatar.py").read_text(encoding="utf-8"))
    assignment = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "LAYOUTS" for target in node.targets)
    )
    return ast.literal_eval(assignment.value)


class PresenterLayoutTests(unittest.TestCase):
    def test_short_presenter_is_in_upper_left_safe_zone(self):
        layout = read_avatar_layouts()["short"]
        top = 1920 - layout["h"] - layout["bottom"]
        self.assertEqual(layout["x"], "32")
        self.assertGreaterEqual(top, 0)
        self.assertLess(top + layout["h"], 420)


class LongCoverrIntegrationTests(unittest.TestCase):
    def test_coverr_download_is_tracked_by_asset_id(self):
        with patch("stock_sources.track_coverr_download") as track:
            track_stock_download({"id": "coverr:abc123"})
        track.assert_called_once_with("abc123")

    def test_non_coverr_download_does_not_call_coverr_tracking(self):
        with patch("stock_sources.track_coverr_download") as track:
            track_stock_download({"id": "pixabay:123"})
        track.assert_not_called()

    def test_coverr_source_and_creator_are_credited(self):
        credits = stock_attribution([{
            "asset_id": "coverr:abc123",
            "page": "https://coverr.co/videos/example",
            "author": "Example Creator",
        }])
        self.assertIn("Coverr", credits)
        self.assertIn("https://coverr.co/", credits)
        self.assertIn("Example Creator", credits)

    def test_empty_stock_list_has_no_empty_credit_block(self):
        self.assertEqual(stock_attribution([]), "")


if __name__ == "__main__":
    unittest.main()
