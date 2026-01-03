@echo off
title WORKER CLIENT

echo Activating virtual environment...
call venv\Scripts\activate

echo Starting Worker Client...
cd worker
python worker_client.py

pause
