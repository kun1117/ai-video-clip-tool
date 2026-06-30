@echo off
title Merge Video Clips
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "%~dp0generate_compilation.ps1"
pause
