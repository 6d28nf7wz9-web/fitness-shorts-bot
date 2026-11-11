"""Live smoke test for the Coverr API adapter.

Skipped automatically when COVERR_API_KEY is not configured.
"""
import os
import unittest


class CoverrApiSmokeTest(unittest.TestCase):
    def test_adapter_returns_downloadable_mp4(self):
        if not os.getenv("COVERR_API_KEY", "").strip():
            self.skipTest("COVERR_API_KEY is not configured")

        from stock_sources import _coverr

        hits = _coverr("fitness")
        self.assertTrue(hits, "Coverr adapter returned no fitness results")

        downloadable = [
            item for item in hits
            if str(item.get("id", "")).startswith("coverr:")
            and (item.get("videos", {}).get("large") or {}).get("url", "").startswith("https://")
        ]
        self.assertTrue(
            downloadable,
            "Coverr adapter did not normalize any downloadable MP4 results",
        )
        first = downloadable[0]
        self.assertTrue(first.get("tags"), "Coverr adapter returned no search metadata")
        self.assertGreater(first.get("duration", 0), 0, "Coverr duration is missing")


if __name__ == "__main__":
    unittest.main()
