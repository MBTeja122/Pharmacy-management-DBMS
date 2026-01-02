from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from db_config import get_db_connection
from psycopg2.extras import RealDictCursor

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

# --- 1. APPROVALS DASHBOARD (With "All Employees" List) ---
@admin_bp.route("/approvals")
def list_approvals():
    if session.get("role") != "Admin":
        flash("Access Denied.", "error")
        return redirect(url_for("dash.load"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Fetch 1: Pending Approvals
        cur.execute("""
            SELECT * FROM pharmacists 
            WHERE active = FALSE 
            ORDER BY created_at DESC
        """)
        pending_users = cur.fetchall()

        # Fetch 2: Active Employees
        cur.execute("""
            SELECT * FROM pharmacists 
            WHERE active = TRUE 
            ORDER BY role ASC, name ASC
        """)
        active_employees = cur.fetchall()

        return render_template("admin_approvals.html", pending_users=pending_users, employees=active_employees)

    except Exception as e:
        print(f"Error loading staff: {e}")
        flash(f"Database Error: {e}", "error")
        return render_template("admin_approvals.html", pending_users=[], employees=[])
        
    finally:
        cur.close()
        conn.close()

# --- 2. APPROVE ACTION ---
@admin_bp.route("/approve/<int:user_id>", methods=['POST'])
def approve_user(user_id):
    if session.get("role") != "Admin": return redirect(url_for("dash.load"))
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE pharmacists SET active = TRUE WHERE pharmacist_id = %s", (user_id,))
        conn.commit()
        flash("User approved successfully.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for("admin_bp.list_approvals"))

# --- 3. REJECT ACTION (For Pending Users) ---
@admin_bp.route("/reject/<int:user_id>", methods=['POST'])
def reject_user(user_id):
    if session.get("role") != "Admin": return redirect(url_for("dash.load"))

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM pharmacists WHERE pharmacist_id = %s", (user_id,))
        conn.commit()
        flash("Request rejected.", "info")
    except Exception as e:
        flash(f"Error: {e}", "error")
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for("admin_bp.list_approvals"))

# --- 4. DELETE EMPLOYEE (New Feature) ---
@admin_bp.route("/delete_employee/<int:user_id>", methods=['POST'])
def delete_employee(user_id):
    if session.get("role") != "Admin": return redirect(url_for("dash.load"))

    # Security: Prevent deleting yourself
    if user_id == session.get("pharmacist_id"):
        flash("You cannot delete your own account!", "error")
        return redirect(url_for("admin_bp.list_approvals"))

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM pharmacists WHERE pharmacist_id = %s", (user_id,))
        conn.commit()
        flash("Employee removed successfully.", "success")
    except Exception as e:
        flash(f"Error deleting employee: {e}", "error")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("admin_bp.list_approvals"))