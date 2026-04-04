from flask import Blueprint, render_template, request, jsonify, send_file, url_for, flash, redirect, current_app
from pymongo import MongoClient
import os
import qrcode
import uuid
import socket
from io import BytesIO
from datetime import datetime
from werkzeug.utils import secure_filename

prescriptions_bp = Blueprint('prescriptions_bp', __name__)

# --- CONFIG ---
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client[os.getenv("MONGO_DB_NAME", "pharmacy_db")]
collection = db["prescriptions"]
UPLOAD_FOLDER = 'static/uploads/prescriptions'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'heic'}

active_sessions = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_wifi_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# =======================
# 1. UPLOAD CHOICE PAGE
# =======================

@prescriptions_bp.route("/upload", methods=["GET"])
def show_upload_form():
    """Shows the page with two options: Computer or Phone"""
    return render_template("upload_prescription.html")

@prescriptions_bp.route("/upload_file", methods=["POST"])
def upload_file():
    """OPTION A: Handle Manual File Upload from Computer"""
    if 'file' not in request.files:
        flash("No file part", "error")
        return redirect(url_for('prescriptions_bp.show_upload_form'))
    
    file = request.files['file']
    patient_name = request.form.get("patient_name")
    doctor_name = request.form.get("doctor_name")

    if file.filename == '':
        flash("No selected file", "error")
        return redirect(url_for('prescriptions_bp.show_upload_form'))

    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        abs_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
        os.makedirs(abs_path, exist_ok=True)
        file.save(os.path.join(abs_path, filename))

        # Save directly as confirmed
        collection.insert_one({
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "filename": filename,
            "file_path": os.path.join(UPLOAD_FOLDER, filename),
            "upload_date": datetime.now(),
            "status": "confirmed", 
            "source": "manual"
        })

        flash("✅ Prescription Saved Successfully!", "success")
        return redirect(url_for('prescriptions_bp.list_prescriptions'))
    
    return redirect(url_for('prescriptions_bp.show_upload_form'))


# =======================
# 2. REMOTE UPLOAD (PHONE)
# =======================

@prescriptions_bp.route("/remote_upload", methods=["GET"])
def remote_upload_page():
    """OPTION B: Generate QR Code for Phone"""
    token = str(uuid.uuid4())
    active_sessions[token] = {'status': 'waiting'}
    ip = get_wifi_ip()
    mobile_url = f"http://{ip}:5000/prescriptions/mobile/{token}"
    return render_template("remote_upload_pc.html", token=token, mobile_url=mobile_url)

@prescriptions_bp.route("/check_status/<token>")
def check_status(token):
    session = active_sessions.get(token)
    if not session: return jsonify({"status": "expired"})
    
    if session.get('status') == 'done':
        filename = session.get('filename')
        del active_sessions[token]
        return jsonify({"status": "done", "filename": filename})
        
    return jsonify({"status": "waiting"})

# =======================
# 3. REVIEW, LIST & DELETE
# =======================

@prescriptions_bp.route("/review/<filename>")
def review_upload(filename):
    return render_template("review_upload.html", filename=filename)

@prescriptions_bp.route("/save_details", methods=["POST"])
def save_details():
    filename = request.form.get("filename")
    patient = request.form.get("patient_name")
    doctor = request.form.get("doctor_name")
    
    collection.update_one(
        {"filename": filename},
        {"$set": {
            "patient_name": patient,
            "doctor_name": doctor,
            "status": "confirmed"
        }}
    )
    flash("✅ Details Saved!", "success")
    return redirect(url_for('prescriptions_bp.list_prescriptions'))

@prescriptions_bp.route("/list")
def list_prescriptions():
    items = list(collection.find({"status": "confirmed"}).sort("upload_date", -1))
    return render_template("prescriptions_list.html", prescriptions=items)

@prescriptions_bp.route("/delete/<filename>")
def delete_prescription(filename):
    """Delete logic"""
    try:
        # 1. Delete file
        abs_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, filename)
        if os.path.exists(abs_path):
            os.remove(abs_path)
        
        # 2. Delete DB entry
        collection.delete_one({"filename": filename})
        flash("🗑️ Deleted Successfully", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        
    return redirect(url_for('prescriptions_bp.list_prescriptions'))

# =======================
# 4. MOBILE UI ROUTES
# =======================

@prescriptions_bp.route("/mobile/<token>", methods=["GET"])
def mobile_camera_page(token):
    return render_template("remote_upload_mobile.html", token=token)

@prescriptions_bp.route("/mobile_upload/<token>", methods=["POST"])
def mobile_upload(token):
    if token not in active_sessions: return "Session expired", 403
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        filename = secure_filename(f"mobile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
        abs_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
        os.makedirs(abs_path, exist_ok=True)
        file.save(os.path.join(abs_path, filename))
        
        # Create Draft
        collection.insert_one({
            "filename": filename,
            "file_path": os.path.join(UPLOAD_FOLDER, filename),
            "source": "mobile_upload",
            "upload_date": datetime.now(),
            "status": "draft",
            "patient_name": "Pending...",
            "doctor_name": "Pending..."
        })
        
        active_sessions[token]['status'] = 'done'
        active_sessions[token]['filename'] = filename
        return render_template("remote_upload_success.html")
    return "Invalid File", 400

@prescriptions_bp.route("/qr_code")
def generate_qr():
    url = request.args.get('url')
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')