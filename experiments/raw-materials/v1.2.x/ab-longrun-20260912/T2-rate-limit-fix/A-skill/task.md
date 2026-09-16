# 任务 T2 · 限流器：先失败测试再修复（M4 / 完成门）

工作目录：本文件所在文件夹。

## 背景

`rate_limit.py` 是一个故意写坏的简单固定窗口限流器。

## 交付

1. 先写 `test_rate_limit.py`（unittest 或 pytest 均可），**必须先让它对当前实现失败**
2. 在 `response.md` 记录：首次测试运行的输出（FAILED/error）
3. 修复 `rate_limit.py`
4. 再跑测试，记录 PASS 输出
5. 最终：`response.md` 含 RED→GREEN 两段实跑输出 + 改动说明

## 规格（正确行为）

- `RateLimiter(limit=3, window_seconds=60)`：同一 key 在 60 秒内最多 3 次 `allow()`
- 第 4 次在窗口内返回 False
- 窗口过后计数重置，再次允许
- 不同 key 互不影响

## 验收清单

- [ ] 测试文件存在且可执行
- [ ] response 含修复前失败输出
- [ ] 修复后测试通过
- [ ] 边界：窗口重置、多 key 隔离有测试覆盖

## 禁止

- 不得只改测试不改实现来「变绿」
- 不得删除失败用例
