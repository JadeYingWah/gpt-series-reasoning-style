@echo off
cd /d "%~dp0arm-A-skill"
start http://localhost:3000
node server.js
pause
