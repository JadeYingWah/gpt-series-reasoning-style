# T2 · 限流器修复 · 证据报告

## 完成门三条款

### 条款 1：磁盘自检清单

| 路径 | 作用 |
|------|------|
| `<实验根目录>\ab-longrun-20260912\T2-rate-limit-fix\A-skill\test_rate_limit.py` | 新建；6 个 unittest 用例 |
| `<实验根目录>\ab-longrun-20260912\T2-rate-limit-fix\A-skill\rate_limit.py` | 修复；按 key 分桶 + 窗口过期重置 |
| `<实验根目录>\ab-longrun-20260912\T2-rate-limit-fix\A-skill\response.md` | 本文件 |

关键 diff（`rate_limit.py`）：

```diff
-        # DEFECT 1: global counter, not per-key
-        self.count = 0
-        self.start = time.time()
+        self._hits = {}  # key -> (window_start, count)

     def allow(self, key="default"):
         now = time.time()
-        # DEFECT 2: never resets window
-        self.count += 1
-        return self.count <= self.limit
+        start, count = self._hits.get(key, (None, 0))
+        if start is None or now - start >= self.window:
+            start, count = now, 0
+        count += 1
+        self._hits[key] = (start, count)
+        return count <= self.limit
```

### 条款 2：回归测试 RED→GREEN 完整循环

先写测试、对**当前坏实现**实跑 → RED；再修实现 → GREEN。两段均为本会话 fresh 实跑输出。

#### RED（修复前，exit=1）

```text
test_allows_up_to_limit (test_rate_limit.TestRateLimiter.test_allows_up_to_limit) ... ok
test_denies_fourth_within_window (test_rate_limit.TestRateLimiter.test_denies_fourth_within_window) ... ok
test_denies_stays_false_after_limit (test_rate_limit.TestRateLimiter.test_denies_stays_false_after_limit) ... ok
test_keys_are_independent (test_rate_limit.TestRateLimiter.test_keys_are_independent) ... FAIL
test_same_count_across_keys_within_limits (test_rate_limit.TestRateLimiter.test_same_count_across_keys_within_limits) ... FAIL
test_window_resets_after_expiry (test_rate_limit.TestRateLimiter.test_window_resets_after_expiry) ... FAIL
======================================================================
FAIL: test_keys_are_independent (test_rate_limit.TestRateLimiter.test_keys_are_independent)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<实验根目录>\ab-longrun-20260912\T2-rate-limit-fix\A-skill\test_rate_limit.py", line 51, in test_keys_are_independent
    self.assertTrue(rl.allow("b"))
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: False is not true
======================================================================
FAIL: test_same_count_across_keys_within_limits (test_rate_limit.TestRateLimiter.test_same_count_across_keys_within_limits)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<实验根目录>\ab-longrun-20260912\T2-rate-limit-fix\A-skill\test_rate_limit.py", line 61, in test_same_count_across_keys_within_limits
    self.assertTrue(rl.allow("x"))
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: False is not true
======================================================================
FAIL: test_window_resets_after_expiry (test_rate_limit.TestRateLimiter.test_window_resets_after_expiry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<实验根目录>\ab-longrun-20260912\T2-rate-limit-fix\A-skill\test_rate_limit.py", line 41, in test_window_resets_after_expiry
    self.assertTrue(rl.allow("a"))
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: False is not true
----------------------------------------------------------------------
Ran 6 tests in 0.003s
FAILED (failures=3)
EXIT:1
```

RED 命中缺陷：多 key 隔离（2 例）+ 窗口过期重置（1 例）。未删除任何失败用例。

#### GREEN（修复后，exit=0）

```text
test_allows_up_to_limit (test_rate_limit.TestRateLimiter.test_allows_up_to_limit) ... ok
test_denies_fourth_within_window (test_rate_limit.TestRateLimiter.test_denies_fourth_within_window) ... ok
test_denies_stays_false_after_limit (test_rate_limit.TestRateLimiter.test_denies_stays_false_after_limit) ... ok
test_keys_are_independent (test_rate_limit.TestRateLimiter.test_keys_are_independent) ... ok
test_same_count_across_keys_within_limits (test_rate_limit.TestRateLimiter.test_same_count_across_keys_within_limits) ... ok
test_window_resets_after_expiry (test_rate_limit.TestRateLimiter.test_window_resets_after_expiry) ... ok
----------------------------------------------------------------------
Ran 6 tests in 0.001s
OK
EXIT:0
```

### 条款 3：检测方法与覆盖面

- **工具**：`python -m unittest test_rate_limit -v`（Python 3.14.5）
- **时间控制**：`unittest.mock.patch("time.time", ...)`，确定性窗口边界（t=1000 → t=1061，window=60）
- **用例清单（6）**：
  1. `test_allows_up_to_limit` — limit=3 时前 3 次 True
  2. `test_denies_fourth_within_window` — 同窗第 4 次 False
  3. `test_denies_stays_false_after_limit` — 超限后持续 False
  4. `test_window_resets_after_expiry` — 窗口过后重置并再次允许
  5. `test_keys_are_independent` — key 耗尽不影响另一 key
  6. `test_same_count_across_keys_within_limits` — 两 key 交错计数互不串扰
- **覆盖面 vs 规格**：limit 边界 ✓；窗口重置 ✓；多 key 隔离 ✓。未覆盖项如实标注：并发线程安全、滑动窗口语义（规格为固定窗口）、内存清理（无 TTL 淘汰）。

## 改动说明

原实现两处缺陷：

1. **全局计数**（`self.count` / `self.start` 不区分 key）→ 任一 key 耗尽后其他 key 也被拒。
2. **从不重置窗口** → 超时后计数仍累加，永不再放行。

修复：按 key 存 `(window_start, count)`；当 `now - start >= window` 时重置该 key 的窗口；再自增并判断 `count <= limit`。

## 验收清单对照

- [x] 测试文件存在且可执行（`test_rate_limit.py`，exit=0）
- [x] response 含修复前失败输出（RED 段，exit=1，failures=3）
- [x] 修复后测试通过（GREEN 段，OK，6/6）
- [x] 边界：窗口重置、多 key 隔离有测试覆盖（用例 4、5、6）

## 禁止项自检

- 未只改测试不改实现（`rate_limit.py` 已修复，diff 如上）
- 未删除失败用例（RED 中 3 个 FAIL 均保留并在 GREEN 中通过）
