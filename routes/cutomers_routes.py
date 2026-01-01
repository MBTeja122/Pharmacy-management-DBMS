# routes/customer_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from db_config import get_db_connection
from datetime import datetime

customers_bp = Blueprint("customers_bp", __name__, url_prefix="/customers")

# Utility to generate unique customer ID like C112234
# 1️⃣ List Customers
@customers_bp.route("/")
def list_customers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers ORDER BY created_at DESC;")
    customers = cur.fetchall()
    conn.close()
    return render_template("customers.html", customers=customers)


# 2️⃣ Add Customer Form (GET) + Insert (POST)
@customers_bp.route("/add", methods=["GET", "POST"])
def add_customer():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form.get("phone", "")
        email = request.form.get("email", "")
        address = request.form.get("address", "")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO customers (name, phone, email, address)
            VALUES (%s, %s, %s, %s)
            RETURNING customer_id;
        """, (name, phone, email, address))
        row = cur.fetchone()
        new_id = row['customer_id']  # fetch the generated serial ID
        conn.commit()
        conn.close()

        flash(f"Customer {name} added with ID {new_id}!")
        next_page = request.args.get("next")  # return to billing if redirected
        return redirect(next_page or url_for("customers_bp.list_customers"))

    return render_template("add_customer.html")

# 3️⃣ Fetch customer data for billing (JSON)
@customers_bp.route("/get/<customer_id>")
def get_customer(customer_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers WHERE customer_id=%s;", (customer_id,))
    customer = cur.fetchone()
    conn.close()
    return jsonify(customer)
