@echo off
chcp 65001 >nul
cd /d "%~dp0"
where java >nul 2>nul
if errorlevel 1 (
  echo [!] 未找到 Java，请安装 Java 8 及以上版本后再试
  pause
  exit /b
)
java -cp . CarrotFantasy
if errorlevel 1 pause
