from flask import Blueprint, render_template, request, jsonify
from db_config import get_db_connection

suppliers_bp = Blueprint("suppliers_bp", __name__, url_prefix="/suppliers")


# View suppliers page
@suppliers_bp.route("/")
def list_suppliers():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT supplier_id, name, contact_person, phone, email, address, gst_no
        FROM suppliers ORDER BY supplier_id ASC
    """)
    suppliers = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("suppliers.html", suppliers=suppliers)


# Update a single field inline
@suppliers_bp.route("/update/<int:supplier_id>", methods=["POST"])
def update_supplier(supplier_id):
    data = request.json
    field = data.get("field")
    value = data.get("value")

    allowed_fields = ["name", "contact_person", "phone", "email", "address", "gst_no"]
    if field not in allowed_fields:
        return jsonify({"error": "Invalid field name"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(f"""
        UPDATE suppliers
        SET {field} = %s
        WHERE supplier_id = %s
    """, (value, supplier_id))

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})


# Add new supplier inline
@suppliers_bp.route("/add", methods=["POST"])
def add_supplier():
    data = request.json

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO suppliers (name, contact_person, phone, email, address, gst_no)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data.get("name"),
        data.get("contact_person"),
        data.get("phone"),
        data.get("email"),
        data.get("address"),
        data.get("gst_no"),
    ))

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})


# Delete supplier inline
@suppliers_bp.route("/delete/<int:supplier_id>", methods=["POST"])
def delete_supplier(supplier_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM suppliers WHERE supplier_id = %s", (supplier_id,))

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})
