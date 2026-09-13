"""Tests for RateLimiter — written against the spec, expected to fail on the broken impl."""
import time
import unittest

from rate_limit import RateLimiter


class TestRateLimiter(unittest.TestCase):
    def test_allows_up_to_limit(self):
        rl = RateLimiter(limit=3, window_seconds=60)
        for i in range(3):
            self.assertTrue(rl.allow("a"), f"call {i + 1} should be allowed")

    def test_fourth_call_in_window_denied(self):
        rl = RateLimiter(limit=3, window_seconds=60)
        for _ in range(3):
            self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"), "4th call in same window must be denied")

    def test_window_reset_allows_again(self):
        rl = RateLimiter(limit=3, window_seconds=0.05)
        for _ in range(3):
            self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))
        time.sleep(0.06)  # window elapsed
        self.assertTrue(rl.allow("a"), "after window expires, allow() must succeed again")

    def test_keys_are_independent(self):
        rl = RateLimiter(limit=3, window_seconds=60)
        for _ in range(3):
            self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))
        # key "b" must not be affected by key "a"
        for i in range(3):
            self.assertTrue(rl.allow("b"), f"key b call {i + 1} should be allowed")
        self.assertFalse(rl.allow("b"))


if __name__ == "__main__":
    unittest.main()
