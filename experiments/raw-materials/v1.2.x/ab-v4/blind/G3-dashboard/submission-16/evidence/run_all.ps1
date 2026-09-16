# G3-dashboard A2plus 验证电池（可复现命令序列）
# 用法：powershell -ExecutionPolicy Bypass -File evidence\run_all.ps1
$ErrorActionPreference = 'Stop'
$ev = $PSScriptRoot
if (-not $ev){ $ev = Split-Path -Parent $MyInvocation.MyCommand.Path }

Write-Host '== 1/6 Node 独立复算 =='
node (Join-Path $ev 'compute_node.mjs')
Write-Host '== 2/6 Python 独立复算 + WCAG 对比度 =='
python (Join-Path $ev 'compute_python.py')
Write-Host '== 3/6 双语言交叉比对 =='
node (Join-Path $ev 'check_cross.mjs')
Write-Host '== 4/6 页面脚本语法检查 =='
node --check (Join-Path $ev 'page_script_extracted.js')
Write-Host 'OK syntax-check'
Write-Host '== 5/6 DOM 仿真交互测试（5 态 + URL 参数态 + 乱序迁移） =='
node (Join-Path $ev 'dom_shim_test.mjs')
Write-Host '== 6/6 真实浏览器 headless 渲染校验（最保守路径） =='
node (Join-Path $ev 'browser_check.mjs')
Write-Host '== 7/7 变异测试（验证体系鉴别力证明，临时目录运行后自清理） =='
node (Join-Path $ev 'mutation_test.mjs')
Write-Host '== 全部完成：证据见 out_node.json / out_python.json / out_contrast.json / out_shim.json / out_browser.json / out_mutation.json / out_render/*.html =='
