from flask import Blueprint, render_template, session, redirect, url_for
from db_config import get_db_connection
from psycopg2.extras import RealDictCursor

audit_bp = Blueprint('audit_bp', __name__, url_prefix='/admin')

@audit_bp.route("/audit_logs")
def audit_hub():
    # 1. Security Check
    if session.get("role") != "Admin":
        return redirect(url_for("dash.load"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # --- SALES AUDIT ONLY (Who sold to whom) ---
    cur.execute("""
        SELECT 
            s.invoice_no, 
            s.created_at, 
            s.total_amount, 
            s.payment_method,
            p.name as staff_name,      -- The 'Who Sold'
            c.name as customer_name    -- The 'To Whom'
        FROM sales s
        LEFT JOIN pharmacists p ON s.pharmacist_id = p.pharmacist_id
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        ORDER BY s.created_at DESC 
        LIMIT 100
    """)
    sales_logs = cur.fetchall()

    cur.close()
    conn.close()

    # Removed 'bot_logs' from the return statement
    return render_template("audit_log.html", sales_logs=sales_logs)