from flask import Blueprint, render_template, request
from models.pharmacist_model import create_pharmacist
cre_acc_bp = Blueprint('cre_acc_bp',__name__)
@cre_acc_bp.route("/create_account", methods=["GET", "POST"])
def create_account():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        role = request.form["role"]

        success, msg = create_pharmacist(name, email, phone, password, role)

        return render_template("create_account.html", message=msg, error=not success)

    return render_template("create_account.html")