@echo off
cd /d "%~dp0arm-B-bare"
start http://localhost:3000
node server.js
pause
