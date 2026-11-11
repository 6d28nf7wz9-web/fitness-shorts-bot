"""Live smoke test for the optional Coverr API integration.

Skipped automatically when COVERR_API_KEY is not configured.
"""
import os
import unittest

import requests


class CoverrApiSmokeTest(unittest.TestCase):
    def test_search_returns_downloadable_mp4(self):
        api_key = os.getenv("COVERR_API_KEY", "").strip()
        if not api_key:
            self.skipTest("COVERR_API_KEY is not configured")

        response = requests.get(
            "https://api.coverr.co/videos",
            headers={"x-api-key": api_key},
            params={
                "query": "fitness",
                "page_size": 5,
                "sort": "popular",
                "urls": "true",
            },
            timeout=25,
        )
        self.assertEqual(
            response.status_code,
            200,
            "Coverr API did not accept the configured key",
        )

        payload = response.json()
        hits = payload.get("hits", [])
        self.assertTrue(hits, "Coverr returned no results for 'fitness'")

        downloadable = [
            item for item in hits
            if (item.get("urls") or {}).get("mp4_download")
        ]
        self.assertTrue(
            downloadable,
            "Coverr returned results but no downloadable MP4 URLs",
        )

        first = downloadable[0]
        self.assertTrue(first.get("id"), "Coverr result is missing its video ID")
        self.assertTrue(
            (first.get("urls") or {}).get("mp4_download", "").startswith("https://"),
            "Coverr MP4 download URL is not HTTPS",
        )


if __name__ == "__main__":
    unittest.main()
