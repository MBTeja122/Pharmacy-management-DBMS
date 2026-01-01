from flask import Blueprint, render_template, request, redirect, url_for, session
from db_config import get_db_connection
from werkzeug.security import check_password_hash, generate_password_hash
import psycopg2.extras
from routes.notification_routes import create_notification 

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Helper: Fetch employees list (Needed for both GET and POST failure)
    def get_employees():
        cur.execute("SELECT pharmacist_id, name FROM pharmacists ORDER BY name ASC")
        return cur.fetchall()

    if request.method == "GET":
        employees = get_employees()
        conn.close()
        return render_template("login.html", employees=employees)

    # --- POST LOGIC ---
    employee_id = request.form.get("employee_id")
    password = request.form.get("password")

    # 1. Fetch User Data
    cur.execute("""
        SELECT pharmacist_id, name, role, password_hash 
        FROM pharmacists 
        WHERE pharmacist_id = %s
    """, (employee_id,))
    
    user = cur.fetchone()

    # 2. Verify Password
    if user and check_password_hash(user["password_hash"], password):
        # ✅ SUCCESS: Set Session
        session["pharmacist_id"] = user["pharmacist_id"]
        session["name"] = user["name"]
        session["role"] = user["role"]
        
        # (Expiry Trigger Logic - Kept same as before)
        if user['role'] == 'Admin':
            try:
                cur.execute("SELECT COUNT(*) as cnt FROM medicines WHERE expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'")
                res = cur.fetchone()
                if res and res['cnt'] > 0:
                    create_notification(f"⏳ Warning: {res['cnt']} medicines expire soon.", "warning", "/admin/analytics")
            except: pass

        conn.close()
        return redirect(url_for("dash.load"))
    
    else:
        # ❌ FAILURE: Render SAME Page with Error Flag
        # We must fetch employees again so the list doesn't vanish
        employees = get_employees()
        conn.close()
        
        # Instead of redirecting, we render the template directly
        # We pass 'login_error=True' to trigger the JS alert
        return render_template("home.html", employees=employees, login_error=True)