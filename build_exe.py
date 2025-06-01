import PyInstaller.__main__
import os

# Get absolute path to the main script
main_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'main.py')

# Build the executable
PyInstaller.__main__.run([
    main_script,
    '--onefile',  # Create a single executable file
    '--windowed',  # Don't show the console window
    '--name', 'Gestor de Inquilinos',  # Name of the executable
    '--icon', 'icon.ico'  # Add an icon if you have one
])
