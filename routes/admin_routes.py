from flask import Blueprint, render_template, redirect, url_for, session, flash
from db_config import get_db_connection
from psycopg2.extras import RealDictCursor

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

# --- 1. THE ROUTE THAT OPENS THE HTML ---
@admin_bp.route("/approvals")
def list_approvals():
    # Security: Kick out non-admins
    if "role" not in session or session["role"] != "Admin":
        flash("Access Denied.")
        return redirect(url_for("dash.load"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Fetch pending users
    cur.execute("SELECT * FROM pharmacists WHERE active = FALSE ORDER BY created_at DESC")
    pending_users = cur.fetchall()
    conn.close()

    # Renders the specific HTML file you asked for
    return render_template("admin_approvals.html", pending_users=pending_users)

# --- 2. APPROVE ACTION ---
@admin_bp.route("/approve/<int:user_id>")
def approve_user(user_id):
    if session.get("role") != "Admin": return redirect(url_for("dash.load"))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE pharmacists SET active = TRUE WHERE pharmacist_id = %s", (user_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for("admin_bp.list_approvals"))

# --- 3. REJECT ACTION ---
@admin_bp.route("/reject/<int:user_id>")
def reject_user(user_id):
    if session.get("role") != "Admin": return redirect(url_for("dash.load"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM pharmacists WHERE pharmacist_id = %s", (user_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for("admin_bp.list_approvals"))