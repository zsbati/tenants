# Tenant Management System

A desktop application for managing tenants and rental properties, built with Python and PyQt6.

## Features

- Tenant management
- Rental contract tracking
- Payment tracking
- Portuguese language interface
- SQLite database
- Modern GUI with tabs for different functionalities

## Requirements

- Python 3.8+
- PyQt6
- SQLAlchemy
- python-dotenv

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Initialize the database:
```bash
python -c "import sys; sys.path.append('.'); from src.utils.database import DatabaseManager; DatabaseManager().initialize_database()"
```

2. Run the application:
```bash
python src/main.py
```

## Project Structure

```
tenants/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── tenant.py
│   ├── views/
│   │   ├── __init__.py
│   │   └── main_window.py
│   └── utils/
│       ├── __init__.py
│       └── database.py
├── requirements.txt
└── README.md
```

## License

MIT License
