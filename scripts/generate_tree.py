"""
Directory tree generator utility.

This is a development utility script that prints a visual representation
of the project directory structure. It's meant to be run directly
from the command line, not imported as a module.
"""
import os
import sys
import logging

# Configure basic logging for the script
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)
logger = logging.getLogger('directory_tree')

# Directories and files to ignore
IGNORE_DIRS = {'.git', '__pycache__', 'venv', 'env', 'migrations', 'staticfiles', '.idea', '.vscode', 'node_modules'}
IGNORE_FILES = {'.DS_Store', 'Thumbs.db'}

def generate_tree(directory, max_depth=3, indent="", current_depth=0):
    """
    Generate and log a visual representation of the directory tree.
    
    Args:
        directory (str): The directory to generate the tree for
        max_depth (int): Maximum depth to traverse
        indent (str): Current indentation level
        current_depth (int): Current depth in the tree
    """
    if current_depth > max_depth:
        return
        
    try:
        entries = sorted(os.listdir(directory))
    except (OSError, PermissionError) as e:
        logger.warning(f"Cannot access {directory}: {e}")
        return
        
    entries = [e for e in entries if e not in IGNORE_FILES]
    dirs = [e for e in entries if os.path.isdir(os.path.join(directory, e)) and e not in IGNORE_DIRS]
    files = [e for e in entries if os.path.isfile(os.path.join(directory, e)) and e not in IGNORE_FILES]

    for idx, dirname in enumerate(dirs):
        is_last = (idx == len(dirs) - 1 and not files)
        logger.info(f"{indent}{'└── ' if is_last else '├── '}{dirname}/")
        generate_tree(
            os.path.join(directory, dirname), 
            max_depth, 
            indent + ("    " if is_last else "│   "), 
            current_depth + 1
        )

    for idx, filename in enumerate(files):
        is_last = (idx == len(files) - 1)
        logger.info(f"{indent}{'└── ' if is_last else '├── '}{filename}")

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logger.info(os.path.basename(project_root) + "/")
    generate_tree(project_root, max_depth=3)