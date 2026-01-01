from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from datetime import datetime
from db_config import get_db_connection
from psycopg2.extras import RealDictCursor

medicine_bp = Blueprint('medicine', __name__, url_prefix='/medicines')

@medicine_bp.route('/')
def list_medicines():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.medicine_id, m.generic_name, m.brand_name, m.form, m.strength,
       m.batch_no, m.expiry_date, m.quantity, m.mrp,
       m.low_stock_threshold, s.name AS supplier_name,
       m.location
       FROM medicines m
       LEFT JOIN suppliers s ON m.supplier_id = s.supplier_id
       ORDER BY m.medicine_id DESC;
    """)
    medicines = cur.fetchall()
    print(medicines)
    conn.close()
    return render_template("medicines.html", medicines=medicines)

def generate_batch_no():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Fetch last batch number from DB
    cur.execute("SELECT batch_no FROM medicines ORDER BY medicine_id DESC LIMIT 1")
    result = cur.fetchone()

    conn.close()

    today = datetime.now().strftime('%y%m%d')

    if result and result["batch_no"].startswith("BAT" + today):
        latest_number = int(result["batch_no"][-3:])  # last 3 digits
        new_number = latest_number + 1
    else:
        new_number = 1  # New day or no previous batch

    return f"BAT{today}{new_number:03d}"
# 🔹 Add Medicine Page Route
@medicine_bp.route('/add', methods=["GET", "POST"])
def add_medicine():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT supplier_id, name FROM suppliers ORDER BY name ASC")
    suppliers = cur.fetchall()
    print(suppliers)
    batch_no = generate_batch_no()

    if request.method == "POST":
        data = (
            request.form["generic_name"],
            request.form["brand_name"],
            request.form["form"],
            request.form["strength"],
            request.form["primary_ingredient"],
            request.form["description"],
            request.form["health_condition"],
            request.form.get("is_otc") == "on",
            request.form["batch_no"], 
            request.form["mfg_date"],
            request.form["expiry_date"],
            request.form["quantity"],
            request.form["cost_price"],
            request.form["mrp"],
            request.form["supplier_id"],
            request.form["reorder_level"],
            request.form["low_stock_threshold"],
            request.form["location"]
        )

        cur.execute("""
            INSERT INTO medicines (
                generic_name, brand_name, form, strength, primary_ingredient,
                description, health_condition, is_otc, batch_no, mfg_date, expiry_date,
                quantity, cost_price, mrp, supplier_id, reorder_level,
                low_stock_threshold, location
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, data)

        conn.commit()
        conn.close()

        flash("Medicine added successfully!")
        return redirect(url_for("medicine.add_medicine"))

    conn.close()
    return render_template("add_medicine.html", suppliers=suppliers, batch_no=batch_no)


# 🔹 Independent Auto-Suggestion Route
@medicine_bp.route("/suggest/<category>")
def suggest(category):
    query = request.args.get("query", "")

    allowed = {
        "generic": "generic_name",
        "brand": "brand_name",
        "strength": "strength",
        "ingredient": "primary_ingredient",
        "health": "health_condition"
    }

    if category not in allowed:
        return jsonify([])

    column = allowed[category]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        f"SELECT DISTINCT {column} FROM medicines WHERE {column} ILIKE %s LIMIT 10",
        (f"%{query}%",)
    )
    rows = cur.fetchall()
    conn.close()

    return jsonify([r[0] for r in rows if r[0]])
@medicine_bp.route('/delete/<int:medicine_id>', methods=["GET"])
def delete_medicine(medicine_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM medicines WHERE medicine_id = %s", (medicine_id,))
    conn.commit()

    cur.close()
    conn.close()
    flash("Medicine deleted successfully!")
    return redirect(url_for('medicine.list_medicines'))

@medicine_bp.route('/edit/<int:medicine_id>', methods=["GET", "POST"])
def edit_medicine(medicine_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == "POST":
        data = (
            request.form["generic_name"],
            request.form["brand_name"],
            request.form["form"],
            request.form["strength"],
            request.form["primary_ingredient"],
            request.form["description"],
            request.form["health_condition"],
            request.form.get("is_otc") == "on",
            request.form["batch_no"],
            request.form["mfg_date"],
            request.form["expiry_date"],
            request.form["quantity"],
            request.form["cost_price"],
            request.form["mrp"],
            request.form["supplier_id"],
            request.form["reorder_level"],
            request.form["low_stock_threshold"],
            request.form["location"],
            medicine_id
        )

        cur.execute("""
            UPDATE medicines SET
                generic_name=%s, brand_name=%s, form=%s, strength=%s,
                primary_ingredient=%s, description=%s, health_condition=%s,
                is_otc=%s, batch_no=%s, mfg_date=%s, expiry_date=%s,
                quantity=%s, cost_price=%s, mrp=%s, supplier_id=%s,
                reorder_level=%s, low_stock_threshold=%s, location=%s,
                updated_at=CURRENT_TIMESTAMP
            WHERE medicine_id=%s
        """, data)

        conn.commit()
        cur.close()
        conn.close()
        flash("Medicine Updated Successfully!")
        return redirect(url_for('medicine.list_medicines'))

    # Fetch selected medicine
    cur.execute("SELECT * FROM medicines WHERE medicine_id = %s", (medicine_id,))
    medicine = cur.fetchone()

    # For Supplier dropdown
    cur.execute("SELECT supplier_id, name FROM suppliers ORDER BY name")
    suppliers = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("edit_medicine.html", medicine=medicine, suppliers=suppliers)
