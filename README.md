# Tenant Management System

A desktop application for managing tenants and rental properties, built with Python and PyQt6.

## Features

- Tenant management
- Rental contract tracking
- Payment tracking with history
- Portuguese language interface
- SQLite database
- Modern GUI with tabs for different functionalities
- Payment history with search and filtering
- Balance tracking with visual indicators

## Payment Management

### Viewing Payment History
1. **Right-click** on a tenant in the main list
2. Select "Ver Histórico de Pagamentos" from the context menu

### Payment History Window Features
- **Date Range Filter**:
  - Use the date pickers to filter payments by date range
  - The table updates automatically when dates change

- **Search**:
  - Type in the search box to filter payments by description
  - Search is case-insensitive

- **Pagination**:
  - Use "Anterior" (Previous) and "Próximo" (Next) buttons to navigate pages
  - Change "Itens por página" (Items per page) to show 10, 20, 50, or 100 items

- **Balance Display**:
  - Shows current balance at the top of the window
  - Red: Amount owed by tenant
  - Green: Credit available

### Registering a New Payment
1. In the Payment History window, click "Registrar Pagamento"
2. Fill in the payment details:
   - **Valor**: Amount paid
   - **Tipo de pagamento**: Payment type (Rent, Deposit, etc.)
   - **Data do pagamento**: Payment date
   - **Mês de referência**: Reference month for the payment
   - **Descrição**: Optional description or notes
3. Click "Salvar" to record the payment

### Handling Partial and Overpayments
- **Partial Payments**: 
  - Enter an amount less than the full rent
  - The remaining balance will be carried forward
  - Status will show as "Parcial" (Partial)

- **Overpayments**:
  - Enter an amount more than the full rent
  - The excess becomes a credit
  - Credit is automatically applied to future months

### Viewing Payment Details
- Click on a payment in the table
- Click "Ver Detalhes" to see full payment information

## Requirements

- Python 3.8+
- PyQt6
- SQLAlchemy
- python-dotenv
- alembic (for database migrations)

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
