@echo off

echo Activating virtual environment...
call .\venv\Scripts\activate.bat

if errorlevel 1 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

echo Running main.py...
python .\tenants_manager\main.py

if errorlevel 1 (
    echo Failed to run main.py
    pause
    exit /b 1
)

pause
