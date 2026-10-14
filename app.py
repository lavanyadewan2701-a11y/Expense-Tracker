"""Main Flask application for the Personal Expense Tracker."""

import math
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, url_for

from database import (
    add_transaction,
    delete_transaction,
    get_categories,
    get_category_analysis,
    get_balance,
    get_dashboard_data,
    get_monthly_analysis,
    get_transaction,
    get_transactions,
    init_db,
    update_transaction,
)
from database import MAX_AMOUNT

app = Flask(__name__)
app.config["SECRET_KEY"] = "personal-expense-tracker-local-key"

EXPENSE_CATEGORIES = [
    "Food",
    "Transport",
    "Education",
    "Entertainment",
    "Shopping",
    "Bills",
    "Health",
    "Other",
]


def validate_form(form, transaction_type, transaction_id=None):
    """Validate shared transaction fields and return clean values or errors."""
    errors = []
    amount_text = form.get("amount", "").strip()
    category = form.get("category", "").strip()
    date_text = form.get("date", "").strip()
    description = form.get("description", "").strip()

    try:
        amount = float(amount_text)
        if not math.isfinite(amount) or amount <= 0:
            errors.append("Amount must be greater than zero.")
        elif amount > MAX_AMOUNT:
            errors.append("Amount cannot be greater than ₹1,000,000,000.")
    except ValueError:
        amount = None
        errors.append("Enter a valid positive amount.")

    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        errors.append("Enter a valid date.")

    if not category:
        errors.append("Select a category or income source.")
    if transaction_type == "expense" and category not in EXPENSE_CATEGORIES:
        errors.append("Select a category from the list.")
    if not errors and transaction_type == "expense" and get_balance(transaction_id) - amount < 0:
        errors.append("This expense would make your balance negative.")

    return amount, category, description, date_text, errors


@app.route("/")
def dashboard():
    totals, categories, recent = get_dashboard_data()
    return render_template(
        "dashboard.html",
        totals=totals,
        categories=categories,
        recent=recent,
    )


@app.route("/expense/add", methods=["GET", "POST"])
def add_expense():
    if request.method == "POST":
        amount, category, description, date_text, errors = validate_form(request.form, "expense")
        if not errors:
            add_transaction("expense", amount, category, description, date_text)
            flash("Expense added successfully.", "success")
            return redirect(url_for("transactions"))
        for error in errors:
            flash(error, "danger")
    return render_template(
        "add_expense.html",
        categories=EXPENSE_CATEGORIES,
        today=datetime.now().strftime("%Y-%m-%d"),
    )


@app.route("/income/add", methods=["GET", "POST"])
def add_income():
    if request.method == "POST":
        amount, source, description, date_text, errors = validate_form(request.form, "income")
        if not errors:
            add_transaction("income", amount, source, description, date_text)
            flash("Income added successfully.", "success")
            return redirect(url_for("transactions"))
        for error in errors:
            flash(error, "danger")
    return render_template(
        "add_income.html",
        today=datetime.now().strftime("%Y-%m-%d"),
    )


@app.route("/transactions")
def transactions():
    filters = {
        "search": request.args.get("search", "").strip(),
        "category": request.args.get("category", "").strip(),
        "type": request.args.get("type", "").strip(),
        "date": request.args.get("date", "").strip(),
        "date_from": request.args.get("date_from", "").strip(),
        "date_to": request.args.get("date_to", "").strip(),
    }
    for field in ("date_from", "date_to"):
        if filters[field]:
            try:
                datetime.strptime(filters[field], "%Y-%m-%d")
            except ValueError:
                flash("Use valid dates for the transaction range.", "danger")
                filters[field] = ""
    if filters["date_from"] and filters["date_to"] and filters["date_from"] > filters["date_to"]:
        flash("The start date must be before or equal to the end date.", "danger")
        filters["date_from"], filters["date_to"] = filters["date_to"], filters["date_from"]
    return render_template(
        "transactions.html",
        transactions=get_transactions(filters),
        categories=get_categories(),
        filters=filters,
    )


@app.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
def edit_transaction(transaction_id):
    transaction = get_transaction(transaction_id)
    if transaction is None:
        flash("Transaction not found.", "danger")
        return redirect(url_for("transactions"))

    if request.method == "POST":
        amount, category, description, date_text, errors = validate_form(
            request.form, transaction["type"], transaction_id
        )
        if not errors:
            update_transaction(transaction_id, transaction["type"], amount, category, description, date_text)
            flash("Transaction updated successfully.", "success")
            return redirect(url_for("transactions"))
        for error in errors:
            flash(error, "danger")
        transaction = {**dict(transaction), **request.form.to_dict()}

    template = "add_expense.html" if transaction["type"] == "expense" else "add_income.html"
    return render_template(
        template,
        transaction=transaction,
        categories=EXPENSE_CATEGORIES,
        today=datetime.now().strftime("%Y-%m-%d"),
        is_edit=True,
    )


@app.post("/transactions/<int:transaction_id>/delete")
def remove_transaction(transaction_id):
    delete_transaction(transaction_id)
    flash("Transaction deleted.", "success")
    return redirect(url_for("transactions"))


@app.route("/analysis")
def analysis():
    category_data = get_category_analysis()
    monthly_data = get_monthly_analysis()
    return render_template(
        "analysis.html",
        category_data=category_data,
        monthly_data=monthly_data,
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
