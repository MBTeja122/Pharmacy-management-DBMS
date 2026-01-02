from flask import Blueprint, render_template, request, jsonify, send_file, url_for, flash, redirect, current_app
from pymongo import MongoClient
import os
import qrcode
import uuid
import socket
import time
from io import BytesIO
from datetime import datetime
from werkzeug.utils import secure_filename

# --- 1. Define Blueprint ---
prescriptions_bp = Blueprint('prescriptions_bp', __name__)

# --- 2. Database & Config ---
client = MongoClient("mongodb://localhost:27017/")
db = client["pharmacy_db"]
collection = db["prescriptions"]

UPLOAD_FOLDER = 'static/uploads/prescriptions'
# Note: We use current_app to get the absolute path later
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

active_sessions = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- 3. Offline Hotspot IP Logic ---
def get_offline_ip():
    """Finds the Laptop's Hotspot IP (usually 192.168.137.1)"""
    try:
        hostname = socket.gethostname()
        all_ips = socket.gethostbyname_ex(hostname)[2]
        
        # Priority 1: Windows Hotspot Default
        if "192.168.137.1" in all_ips: return "192.168.137.1"
        
        # Priority 2: Any 192.168.x.x (excluding localhost)
        for ip in all_ips:
            if ip.startswith("192.168.") and ip != "127.0.0.1": return ip
            
        # Priority 3: Fallback to 172.x (Mobile Hotspots)
        for ip in all_ips:
            if ip.startswith("172."): return ip
            
    except: pass
    return "192.168.137.1" # Default fallback

# ==========================================
#  PART A: MANUAL UPLOAD ROUTES (Laptop)
# ==========================================

@prescriptions_bp.route("/upload", methods=["GET"])
def show_upload_form():
    return render_template("upload_prescription.html")

@prescriptions_bp.route("/upload_file", methods=["POST"])
def upload_file():
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
        
        # Ensure directory exists using absolute path
        abs_folder = os.path.join(current_app.root_path, UPLOAD_FOLDER)
        os.makedirs(abs_folder, exist_ok=True)
        
        file.save(os.path.join(abs_folder, filename))

        collection.insert_one({
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "filename": filename,
            "file_path": os.path.join(UPLOAD_FOLDER, filename),
            "upload_date": datetime.now(),
            "status": "stored",
            "source": "manual"
        })

        flash("✅ Prescription Saved Successfully!", "success")
        return redirect(url_for('prescriptions_bp.show_upload_form'))
    
    return redirect(url_for('prescriptions_bp.show_upload_form'))


# ==========================================
#  PART B: REMOTE CAMERA ROUTES (Mobile)
# ==========================================

@prescriptions_bp.route("/remote_upload", methods=["GET"])
def remote_upload_page():
    token = str(uuid.uuid4())
    active_sessions[token] = {'status': 'waiting', 'filename': None}

    local_ip = get_offline_ip()
    
    # Must use HTTPS for Camera to work on mobile
    mobile_url = f"https://{local_ip}:5000/prescriptions/mobile/{token}"
    
    print(f"🚀 QR Link: {mobile_url}")
    return render_template("remote_upload_pc.html", token=token, mobile_url=mobile_url)

@prescriptions_bp.route("/qr_code")
def generate_qr():
    url = request.args.get('url')
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@prescriptions_bp.route("/check_status/<token>")
def check_status(token):
    session = active_sessions.get(token)
    if not session: return jsonify({"status": "expired"})
    if session['status'] == 'done':
        del active_sessions[token]
        return jsonify({"status": "done", "filename": session['filename']})
    return jsonify({"status": "waiting"})

@prescriptions_bp.route("/mobile/<token>", methods=["GET"])
def mobile_camera_page(token):
    return render_template("remote_upload_mobile.html", token=token)

@prescriptions_bp.route("/mobile_upload/<token>", methods=["POST"])
def mobile_upload(token):
    if token not in active_sessions: return jsonify({"error": "Expired"}), 403
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        filename = secure_filename(f"mobile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
        
        abs_folder = os.path.join(current_app.root_path, UPLOAD_FOLDER)
        os.makedirs(abs_folder, exist_ok=True)
        file.save(os.path.join(abs_folder, filename))
        
        active_sessions[token]['status'] = 'done'
        active_sessions[token]['filename'] = filename
        
        collection.insert_one({
            "filename": filename,
            "file_path": os.path.join(UPLOAD_FOLDER, filename),
            "source": "mobile_camera",
            "upload_date": datetime.now(),
            "status": "draft"
        })
        return render_template("remote_upload_success.html")
    return "Invalid File", 400