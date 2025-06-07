@echo on

echo Current directory: %cd%

echo Checking virtual environment...
if exist venv\Scripts\activate.bat (
    echo Virtual environment found
    echo Activating virtual environment...
    call .\venv\Scripts\activate.bat
    if errorlevel 1 (
        echo Failed to activate virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment activated
) else (
    echo Virtual environment not found
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
