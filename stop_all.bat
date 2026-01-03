@echo off
title STOP ALL PYTHON PROCESSES

echo Stopping all Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

echo All Python processes stopped.
pause
