from flask import Blueprint, render_template
from models.pharmacist_model import get_all_pharmacists

home_bp = Blueprint('home_bp', __name__)

@home_bp.route("/")
def home():
    employees = get_all_pharmacists()
    return render_template("home.html", employees=employees)
