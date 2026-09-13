#!/usr/bin/env bash
# G1-A2plus 验证复现脚本（在 evidence/ 目录下执行）
set -e
cd "$(dirname "$0")"
echo "[1/3] Python 精确分数 oracle 生成 vectors.json"
python oracle.py
echo "[2/3] Node 核心电池 + 变异测试（路径2/3）"
node test-core.mjs
echo "[3/3] Chrome headless CDP 实操验证（路径1，需本机 Chrome）"
node test-browser.mjs
echo "全部完成。结果见 results/ 与 screenshots/"
