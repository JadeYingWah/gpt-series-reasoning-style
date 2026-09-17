@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py "植物大战僵尸.py"
  goto :end
)
where python >nul 2>nul
if not errorlevel 1 (
  python "植物大战僵尸.py"
  goto :end
)
echo [!] 未找到 Python，请先安装 Python 3
:end
if errorlevel 1 pause
