# Personal Expense Tracker

A beginner-friendly web application for recording income and expenses, viewing transaction history, and understanding spending patterns. It is designed as a 2nd-year college Python project and runs locally on Flask with SQLite3.

## Objectives

- Record personal income and expenses in one place.
- Calculate balance and spending totals automatically.
- Filter and manage transaction records.
- Present category and monthly spending analysis visually.
- Demonstrate Python, Flask, HTML, CSS, SQL, and CRUD operations.

## Features

- Dashboard with total income, expenses, balance, transaction count, category breakdown, and recent activity.
- Add and edit expenses with validated amount, date, category, and description.
- Add and edit income with amount, date, source, and description.
- Transaction search, category/type/date filters, start/end date range history, editing, and deletion.
- Positive income and expense amounts with a maximum of 1,000,000,000; expenses cannot make the calculated balance negative.
- Category ranking with totals and percentages.
- Dynamic expense pie charts and monthly income/expense bar charts using Chart.js CDN.
- Responsive Bootstrap-based interface.

## Technologies Used

- Python 3.13
- Flask 3.x
- SQLite3 (included with Python)
- HTML5, CSS3, Bootstrap 5 CDN
- Chart.js CDN

`requirements.txt` contains only Flask. SQLite3 is part of Python and needs no separate installation.

## Database Design

The SQLite database is stored at `database/expenses.db`. The `transactions` table contains:

| Column | Description |
| --- | --- |
| `id` | Integer primary key |
| `type` | `income` or `expense` |
| `amount` | Positive numeric amount up to 1,000,000,000 |
| `category` | Expense category or income source |
| `description` | Optional note |
| `date` | Transaction date in YYYY-MM-DD format |
| `created_at` | Automatically recorded creation timestamp |

The table is created automatically by `init_db()` in `database.py`. All user values use parameterized SQL queries.

## Project Structure

```text
expense_tracker/
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── add_expense.html
│   ├── add_income.html
│   ├── transactions.html
│   └── analysis.html
├── static/
│   └── style.css
└── database/
    └── expenses.db
```

## Installation on Windows

1. Install Python 3.13 from [python.org](https://www.python.org/downloads/). During installation, enable **Add Python to PATH**.
2. Open Command Prompt or PowerShell and move into the project folder:

```powershell
cd "E:\Coding n stuff\Expense Tracker\expense_tracker"
```

3. Create a virtual environment:

```powershell
python -m venv venv
```

4. Activate it:

```powershell
venv\Scripts\activate
```

5. Install the required package:

```powershell
pip install -r requirements.txt
```

## How to Run

Start the application with:

```powershell
python app.py
```

Open this address in a browser:

```text
http://127.0.0.1:5000
```

The database and table are initialized automatically the first time the application starts. Press `Ctrl+C` in the terminal to stop the server.

## Future Improvements

- Add user login and separate data for each user.
- Export transactions to CSV or PDF.
- Add budgets and spending alerts.
- Support recurring transactions.
- Add year selection and more detailed reports.
- Add automated unit tests and deployment configuration.
