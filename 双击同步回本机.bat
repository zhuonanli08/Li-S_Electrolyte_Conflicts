@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0from_cloud.ps1" %*
pause
