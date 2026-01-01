from flask import Blueprint, render_template, redirect, url_for, session

dash_bp = Blueprint('dash', __name__,url_prefix='/dashboard')

@dash_bp.route("/")
def load():
    if "pharmacist_id" not in session:
        print("Session Missing!")
        return redirect(url_for("auth.home"))
    return render_template("dashboard.html")

@dash_bp.route("/inventory")
def load_inventory_management():
    return redirect(url_for("medicine.list_medicines"))

@dash_bp.route("/supplier")
def load_supplier_details():
    return redirect(url_for("suppliers_bp.list_suppliers"))
@dash_bp.route("/billing")
def load_billing_form():
    return redirect(url_for("sales_bp.billing"))