from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify ,session
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
    batch_no = generate_batch_no()

    if request.method == "POST":
        try:
            # 1. Collect form data
            generic_name = request.form["generic_name"]
            brand_name = request.form["brand_name"]
            quantity = int(request.form["quantity"])
            cost_price = float(request.form["cost_price"])
            supplier_id = request.form["supplier_id"]
            pharmacist_id = session.get("pharmacist_id") # Get current logged-in user

            # 2. Insert into medicines (Existing Logic)
            cur.execute("""
                INSERT INTO medicines (
                    generic_name, brand_name, form, strength, primary_ingredient,
                    description, health_condition, is_otc, batch_no, mfg_date, expiry_date,
                    quantity, cost_price, mrp, supplier_id, reorder_level,
                    low_stock_threshold, location
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING medicine_id
            """, (
                generic_name, brand_name, request.form["form"], request.form["strength"],
                request.form["primary_ingredient"], request.form["description"],
                request.form["health_condition"], request.form.get("is_otc") == "on",
                request.form["batch_no"], request.form["mfg_date"], request.form["expiry_date"],
                quantity, cost_price, request.form["mrp"], supplier_id,
                request.form["reorder_level"], request.form["low_stock_threshold"],
                request.form["location"]
            ))
            new_medicine_id = cur.fetchone()['medicine_id']

            # 3. Create Purchase Header (New Logic)
            total_amount = quantity * cost_price
            cur.execute("""
                INSERT INTO purchases (supplier_id, pharmacist_id, total_amount, status)
                VALUES (%s, %s, %s, 'Completed')
                RETURNING purchase_id
            """, (supplier_id, pharmacist_id, total_amount))
            new_purchase_id = cur.fetchone()['purchase_id']

            # 4. Create Purchase Item Detail (New Logic)
            cur.execute("""
                INSERT INTO purchase_items (purchase_id, medicine_id, batch_no, expiry_date, quantity, unit_cost)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                new_purchase_id, new_medicine_id, request.form["batch_no"],
                request.form["expiry_date"], quantity, cost_price
            ))

            conn.commit()
            flash(f"Medicine and Purchase Record added successfully!")
            
        except Exception as e:
            conn.rollback()
            flash(f"Error: {str(e)}", "error")
        finally:
            conn.close()
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
        def clean_val(val): return val if val and val.strip() != "" else None

        # Collect data for updating both tables
        batch_no = request.form["batch_no"]
        expiry_date = request.form["expiry_date"]
        cost_price = clean_val(request.form["cost_price"])
        quantity = request.form["quantity"]

        data = (
            request.form["generic_name"], request.form["brand_name"], 
            request.form["form"], request.form["strength"],
            request.form["primary_ingredient"], request.form["description"], 
            request.form["health_condition"], request.form.get("is_otc") == "on",
            batch_no, clean_val(request.form["mfg_date"]), expiry_date,
            quantity, cost_price, request.form["mrp"], 
            request.form["supplier_id"], request.form["reorder_level"], 
            request.form["low_stock_threshold"], request.form["location"],
            medicine_id
        )

        try:
            # 1. Update the Medicine Table (Existing Logic)
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

            # 2. Update the associated Purchase Item (New Sync Logic)
            # This ensures your Purchase History stays accurate if you edit a batch
            cur.execute("""
                UPDATE purchase_items SET
                    batch_no=%s, expiry_date=%s, unit_cost=%s, quantity=%s
                WHERE medicine_id=%s
            """, (batch_no, expiry_date, cost_price, quantity, medicine_id))

            conn.commit()
            flash("Medicine and Procurement Records Updated Successfully!")
        except Exception as e:
            conn.rollback()
            flash(f"Error updating records: {str(e)}", "error")
        finally:
            cur.close()
            conn.close()
            return redirect(url_for('medicine.list_medicines'))

    # --- GET REQUEST LOGIC (Remains exactly the same) ---
    cur.execute("SELECT * FROM medicines WHERE medicine_id = %s", (medicine_id,))
    medicine = cur.fetchone()

    if medicine:
        if medicine.get('mfg_date'):
            medicine['mfg_date'] = medicine['mfg_date'].strftime('%Y-%m-%d')
        if medicine.get('expiry_date'):
            medicine['expiry_date'] = medicine['expiry_date'].strftime('%Y-%m-%d')

    cur.execute("SELECT supplier_id, name FROM suppliers ORDER BY name")
    suppliers = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("edit_medicine.html", medicine=medicine, suppliers=suppliers)
