from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from db_config import get_db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime
from routes.notification_routes import create_notification  # <--- IMPORTED NOTIFICATION HELPER

sales_bp = Blueprint("sales_bp", __name__, url_prefix="/sales")

# =========================================================
# 🔹 1. SMART CUSTOMER SEARCH (Name OR Last 5 Digits)
# =========================================================
@sales_bp.route("/customer_search/<query>")
def customer_search(query):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if query.isdigit():
        sql = """
            SELECT customer_id, name, phone, loyalty_points 
            FROM customers 
            WHERE RIGHT(phone, 5) = %s OR CAST(customer_id AS TEXT) = %s
            LIMIT 5
        """
        cur.execute(sql, (query, query))
    else:
        sql = """
            SELECT customer_id, name, phone, loyalty_points 
            FROM customers 
            WHERE name ILIKE %s 
            ORDER BY name ASC LIMIT 5
        """
        cur.execute(sql, (f"%{query}%",))
    
    results = cur.fetchall()
    conn.close()
    return jsonify(results)

# =========================================================
# 🔹 2. MEDICINE SEARCH & ALTERNATE FINDER
# =========================================================
@sales_bp.route("/medicine_search/<query>")
def medicine_search(query):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT medicine_id, brand_name, generic_name, quantity, mrp 
        FROM medicines 
        WHERE brand_name ILIKE %s OR generic_name ILIKE %s
        ORDER BY (brand_name ILIKE %s) DESC, brand_name ASC LIMIT 10
    """, (f"%{query}%", f"%{query}%", f"{query}%"))
    
    results = cur.fetchall()
    conn.close()
    
    data = []
    for r in results:
        data.append({
            "medicine_id": r['medicine_id'],
            "name": f"{r['brand_name']} ({r['generic_name']})",
            "mrp": float(r['mrp']),
            "quantity": r['quantity']
        })
    return jsonify(data)

@sales_bp.route("/check_alternates", methods=["POST"])
def check_alternates():
    try:
        data = request.json
        medicine_id = data.get("medicine_id")
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT generic_name, form, strength, brand_name FROM medicines WHERE medicine_id = %s", (medicine_id,))
        target = cur.fetchone()

        if not target:
            return jsonify({"status": "error", "message": "Item not found"})

        cur.execute("""
            SELECT medicine_id, brand_name, generic_name, quantity, mrp, location
            FROM medicines
            WHERE generic_name ILIKE %s AND form = %s AND strength = %s
            AND quantity > 0 AND medicine_id != %s
            ORDER BY mrp ASC
        """, (target['generic_name'], target['form'], target['strength'], medicine_id))
        
        alternates = cur.fetchall()
        return jsonify({
            "status": "success",
            "target_name": target['brand_name'],
            "criteria": f"{target['generic_name']} | {target['strength']} | {target['form']}",
            "alternates": [dict(row) for row in alternates]
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        if 'conn' in locals(): conn.close()

# =========================================================
# 🔹 3. AI RECOMMENDATION ENGINE
# =========================================================
@sales_bp.route("/recommend", methods=["POST"])
def get_recommendations():
    data = request.json
    customer_id = data.get("customer_id")
    cart_items = data.get("medicine_ids", [])
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    recommendations = []
    seen_ids = set(map(int, cart_items))

    try:
        # Market Basket
        if cart_items:
            cart_tuple = tuple(cart_items)
            cur.execute("""
                SELECT m.medicine_id, m.brand_name, m.generic_name, m.mrp, COUNT(*) as score
                FROM sale_items source
                JOIN sale_items target ON source.sale_id = target.sale_id
                JOIN medicines m ON target.medicine_id = m.medicine_id
                WHERE source.medicine_id IN %s AND target.medicine_id NOT IN %s AND m.quantity > 0
                GROUP BY m.medicine_id, m.brand_name, m.generic_name, m.mrp
                ORDER BY score DESC LIMIT 3;
            """, (cart_tuple, cart_tuple))
            for r in cur.fetchall():
                if r['medicine_id'] not in seen_ids:
                    r['reason'] = "Frequently bought together"
                    recommendations.append(r)
                    seen_ids.add(r['medicine_id'])

        # Personalized History
        if customer_id and len(recommendations) < 5:
            cur.execute("""
                SELECT m.medicine_id, m.brand_name, m.generic_name, m.mrp, COUNT(*) as score
                FROM sales s
                JOIN sale_items si ON s.sale_id = si.sale_id
                JOIN medicines m ON si.medicine_id = m.medicine_id
                WHERE s.customer_id = %s AND m.quantity > 0
                GROUP BY m.medicine_id, m.brand_name, m.generic_name, m.mrp
                ORDER BY score DESC LIMIT 3;
            """, (customer_id,))
            for r in cur.fetchall():
                if r['medicine_id'] not in seen_ids:
                    r['reason'] = "Buy Again"
                    recommendations.append(r)
                    seen_ids.add(r['medicine_id'])

    finally:
        conn.close()
    return jsonify(recommendations)

# =========================================================
# 🔹 4. TRANSACTION SUBMISSION (With Notifications)
# =========================================================
@sales_bp.route("/billing", methods=["GET", "POST"])
def billing():
    if request.method == "POST":
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            customer_id = request.form.get("customer_id") or None
            total_amount = float(request.form.get("total_amount", 0))
            loyalty_used = int(request.form.get("loyalty_points_used", 0))
            payment_method = request.form.get("payment_method", "Cash")
            pharmacist_id = session.get("pharmacist_id")

            med_ids = request.form.getlist("medicine_id")
            quantities = request.form.getlist("quantity")
            prices = request.form.getlist("unit_price")

            if not med_ids: raise Exception("Cart is empty.")

            invoice_no = f"INV{datetime.now().strftime('%y%m%d%H%M%S')}"
            points_earned = int(total_amount // 100)

            # 1. Insert Sale Header
            cur.execute("""
                INSERT INTO sales (invoice_no, customer_id, pharmacist_id, total_amount, payment_method, loyalty_points_earned, loyalty_points_used)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING sale_id
            """, (invoice_no, customer_id, pharmacist_id, total_amount, payment_method, points_earned, loyalty_used))
            sale_id = cur.fetchone()['sale_id']

            # 2. Process Items & Trigger Low Stock Alerts
            for mid, qty, price in zip(med_ids, quantities, prices):
                cur.execute("SELECT quantity FROM medicines WHERE medicine_id=%s FOR UPDATE", (mid,)) # Lock row
                
                cur.execute("INSERT INTO sale_items (sale_id, medicine_id, quantity, unit_price) VALUES (%s, %s, %s, %s)", (sale_id, mid, qty, price))
                
                # UPDATE STOCK AND RETURN INFO FOR ALERT
                cur.execute("""
                    UPDATE medicines 
                    SET quantity = quantity - %s 
                    WHERE medicine_id = %s 
                    RETURNING brand_name, quantity, low_stock_threshold
                """, (qty, mid))
                
                row = cur.fetchone()
                
                # 🔥 TRIGGER 1: LOW STOCK ALERT
                if row:
                    brand_name, new_qty, threshold = row['brand_name'], row['quantity'], row['low_stock_threshold']
                    if new_qty <= threshold:
                        create_notification(
                            message=f"📉 Low Stock: {brand_name} dropped to {new_qty} units.",
                            type="danger",
                            link=f"/medicines/edit/{mid}"
                        )

            # 3. Update Loyalty
            if customer_id:
                cur.execute("UPDATE customers SET loyalty_points = loyalty_points + %s - %s WHERE customer_id = %s", (points_earned, loyalty_used, customer_id))

            # 🔥 TRIGGER 2: DAILY REVENUE MILESTONE
            cur.execute("SELECT SUM(total_amount) as total FROM sales WHERE created_at >= CURRENT_DATE")
            res = cur.fetchone()
            today_rev = float(res['total']) if res and res['total'] else 0.0
            
            # Check if we just crossed the milestone with this specific transaction
            prev_rev = today_rev - total_amount
            if today_rev >= 10000 and prev_rev < 10000:
                create_notification(
                    message="🎉 Milestone: Daily sales just crossed ₹10,000!",
                    type="success",
                    link="/admin/analytics"
                )

            conn.commit()
            return redirect(url_for('sales_bp.view_invoice', invoice_no=invoice_no))

        except Exception as e:
            conn.rollback()
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("sales_bp.billing"))
        finally:
            conn.close()

    return render_template("billing.html")

@sales_bp.route("/invoice/<invoice_no>")
def view_invoice(invoice_no):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT s.*, c.name as customer_name, c.phone as customer_phone, c.address as customer_address, p.name as pharmacist_name
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.customer_id
            LEFT JOIN pharmacists p ON s.pharmacist_id = p.pharmacist_id
            WHERE s.invoice_no = %s
        """, (invoice_no,))
        sale = cur.fetchone()
        if not sale: return "Invoice not found", 404

        cur.execute("""
             SELECT si.*, m.brand_name, m.generic_name
            FROM sale_items si
            JOIN medicines m ON si.medicine_id = m.medicine_id
            WHERE si.sale_id = %s
        """, (sale['sale_id'],))
        items = cur.fetchall()
    finally:
        conn.close()
    return render_template("reciept.html", sale=sale, items=items)