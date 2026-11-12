import os
import unittest
from unittest.mock import patch

import wan_stock_assist


class WanStockAssistTests(unittest.TestCase):
    def test_disabled_by_default_and_never_calls_provider(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(wan_stock_assist, "is_enabled", return_value=False):
                with patch.object(wan_stock_assist, "generate_video") as generate:
                    result = wan_stock_assist.try_animate_stock(
                        "stock.mp4",
                        {"narration": "A person performs a squat"},
                        2.5,
                        "out.mp4",
                    )
        self.assertIsNone(result)
        generate.assert_not_called()

    def test_requires_separate_stock_assist_switch(self):
        with patch.dict(os.environ, {
            "I2V_ENABLED": "1",
            "I2V_PROVIDER": "wan",
            "WAN_STOCK_ASSIST": "0",
            "WAN_API_KEY": "test-token",
        }):
            with patch.object(wan_stock_assist, "is_enabled", return_value=True):
                with patch.object(wan_stock_assist, "generate_video") as generate:
                    result = wan_stock_assist.try_animate_stock(
                        "stock.mp4",
                        {"narration": "A person performs a squat"},
                        2.5,
                        "out.mp4",
                    )
        self.assertIsNone(result)
        generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
