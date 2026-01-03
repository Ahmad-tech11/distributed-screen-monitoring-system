@echo off
title MASTER SERVER

echo Activating virtual environment...
call venv\Scripts\activate

echo Starting Master Server...
cd master
python master_server.py

pause
