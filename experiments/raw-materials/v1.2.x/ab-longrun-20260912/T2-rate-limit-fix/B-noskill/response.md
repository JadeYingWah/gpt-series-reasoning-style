# T2 · 限流器 RED→GREEN 报告（B 臂 / 无 skill）

## 1. 首次测试运行（修复前 — RED）

```
$ python -m unittest test_rate_limit -v

test_allows_up_to_limit (test_rate_limit.TestRateLimiter.test_allows_up_to_limit) ... ok
test_fourth_call_in_window_denied (test_rate_limit.TestRateLimiter.test_fourth_call_in_window_denied) ... ok
test_keys_are_independent (test_rate_limit.TestRateLimiter.test_keys_are_independent) ... FAIL
test_window_reset_allows_again (test_rate_limit.TestRateLimiter.test_window_reset_allows_again) ... FAIL
======================================================================
FAIL: test_keys_are_independent (test_rate_limit.TestRateLimiter.test_keys_are_independent)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_rate_limit.py", line 35, in test_keys_are_independent
    self.assertTrue(rl.allow("b"), f"key b call {i + 1} should be allowed")
AssertionError: False is not true : key b call 1 should be allowed
======================================================================
FAIL: test_window_reset_allows_again (test_rate_limit.TestRateLimiter.test_window_reset_allows_again)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_rate_limit.py", line 26, in test_window_reset_allows_again
    self.assertTrue(rl.allow("a"), "after window expires, allow() must succeed again")
AssertionError: False is not true : after window expires, allow() must succeed again
----------------------------------------------------------------------
Ran 4 tests in 0.062s
FAILED (failures=2)
```

失败原因对应原实现两处缺陷：
1. 全局单一 `self.count` / `self.start`，不同 key 共享计数 → 多 key 隔离失败。
2. 从不根据 `window_seconds` 重置计数 → 窗口过后仍拒绝。

## 2. 修复说明

`rate_limit.py` 改为按 key 存 `(window_start, count)`：

- `self._state: dict[key -> (window_start, count)]` 替代全局计数。
- 每次 `allow()` 先检查 `now - window_start >= window_seconds`，过期则重置该 key。
- 达到 `limit` 返回 False，否则计数 +1 返回 True。

未改动测试用例以「变绿」；四个用例在 RED 与 GREEN 阶段保持一致。

## 3. 修复后测试运行（GREEN）

```
$ python -m unittest test_rate_limit -v

test_allows_up_to_limit (test_rate_limit.TestRateLimiter.test_allows_up_to_limit) ... ok
test_fourth_call_in_window_denied (test_rate_limit.TestRateLimiter.test_fourth_call_in_window_denied) ... ok
test_keys_are_independent (test_rate_limit.TestRateLimiter.test_keys_are_independent) ... ok
test_window_reset_allows_again (test_rate_limit.TestRateLimiter.test_window_reset_allows_again) ... ok
----------------------------------------------------------------------
Ran 4 tests in 0.061s
OK
```

## 验收清单

- [x] 测试文件存在且可执行（`test_rate_limit.py`，unittest）
- [x] response 含修复前失败输出（上文 RED）
- [x] 修复后测试通过（上文 GREEN，4/4 OK）
- [x] 边界覆盖：窗口重置（`test_window_reset_allows_again`）、多 key 隔离（`test_keys_are_independent`）
