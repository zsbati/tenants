from setuptools import setup, find_packages

setup(
    name="tenants_manager",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'tenants_manager=tenants_manager.__main__:main'
        ]
    },
    install_requires=[
        'PyQt6==6.6.1',
        'SQLAlchemy==2.0.23',
        'python-dotenv==1.0.0',
        'PyQt6-Qt6==6.6.1',
        'PyQt6-sip==13.6.0'
    ]
)
