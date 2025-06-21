import sys
import pkg_resources

def check_versions():
    print("Python version:", sys.version)
    print("\nInstalled packages:")
    
    # List of packages we're particularly interested in
    key_packages = [
        'SQLAlchemy',
        'PyQt6',
        'PyQt6-Qt6',
        'PyQt6-sip',
        'python-dotenv',
        'Werkzeug',
        'Jinja2',
        'MarkupSafe',
        'itsdangerous',
        'click',
        'packaging',
        'pyparsing',
        'pywin32',
        'pywin32-ctypes',
        'setuptools',
        'pip'
    ]
    
    # Get all installed packages
    installed_packages = {pkg.key: pkg for pkg in pkg_resources.working_set}
    
    # Print key packages first
    print("\nKey packages:")
    for pkg in key_packages:
        pkg_lower = pkg.lower()
        found = False
        for installed_pkg in installed_packages.values():
            if installed_pkg.key.lower() == pkg_lower:
                print(f"{pkg}: {installed_pkg.version}")
                found = True
                break
        if not found:
            print(f"{pkg}: Not installed")
    
    # Print all other packages
    print("\nAll installed packages:")
    for pkg in sorted(installed_packages.values(), key=lambda x: x.key):
        if pkg.key.lower() not in [p.lower() for p in key_packages]:
            print(f"{pkg.key}: {pkg.version}")

if __name__ == "__main__":
    check_versions()
