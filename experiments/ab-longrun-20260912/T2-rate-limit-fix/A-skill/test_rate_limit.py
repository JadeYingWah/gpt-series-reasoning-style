"""Tests for RateLimiter — must fail on the broken implementation first."""
import unittest
from unittest.mock import patch

from rate_limit import RateLimiter


class TestRateLimiter(unittest.TestCase):
    def test_allows_up_to_limit(self):
        rl = RateLimiter(limit=3, window_seconds=60)
        with patch("time.time", return_value=1000.0):
            self.assertTrue(rl.allow("a"))
            self.assertTrue(rl.allow("a"))
            self.assertTrue(rl.allow("a"))

    def test_denies_fourth_within_window(self):
        rl = RateLimiter(limit=3, window_seconds=60)
        with patch("time.time", return_value=1000.0):
            self.assertTrue(rl.allow("a"))
            self.assertTrue(rl.allow("a"))
            self.assertTrue(rl.allow("a"))
            self.assertFalse(rl.allow("a"))

    def test_denies_stays_false_after_limit(self):
        rl = RateLimiter(limit=3, window_seconds=60)
        with patch("time.time", return_value=1000.0):
            for _ in range(3):
                rl.allow("a")
            self.assertFalse(rl.allow("a"))
            self.assertFalse(rl.allow("a"))

    def test_window_resets_after_expiry(self):
        rl = RateLimiter(limit=3, window_seconds=60)
        with patch("time.time", return_value=1000.0):
            self.assertTrue(rl.allow("a"))
            self.assertTrue(rl.allow("a"))
            self.assertTrue(rl.allow("a"))
            self.assertFalse(rl.allow("a"))
        # 61 seconds later — window has expired, counter must reset
        with patch("time.time", return_value=1061.0):
            self.assertTrue(rl.allow("a"))

    def test_keys_are_independent(self):
        rl = RateLimiter(limit=3, window_seconds=60)
        with patch("time.time", return_value=1000.0):
            self.assertTrue(rl.allow("a"))
            self.assertTrue(rl.allow("a"))
            self.assertTrue(rl.allow("a"))
            self.assertFalse(rl.allow("a"))
            # key b must not be affected by key a's exhaustion
            self.assertTrue(rl.allow("b"))
            self.assertTrue(rl.allow("b"))
            self.assertTrue(rl.allow("b"))
            self.assertFalse(rl.allow("b"))

    def test_same_count_across_keys_within_limits(self):
        rl = RateLimiter(limit=2, window_seconds=30)
        with patch("time.time", return_value=2000.0):
            self.assertTrue(rl.allow("x"))
            self.assertTrue(rl.allow("y"))
            self.assertTrue(rl.allow("x"))
            self.assertFalse(rl.allow("x"))
            self.assertTrue(rl.allow("y"))
            self.assertFalse(rl.allow("y"))


if __name__ == "__main__":
    unittest.main()
