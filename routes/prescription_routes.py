from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret_key_for_flash_messages"

# --- CONFIGURATION ---
# 1. Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["pharmacy_db"]
collection = db["prescriptions"]

# 2. Configure Upload Folder
UPLOAD_FOLDER = 'static/uploads/prescriptions'
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Creates folder if it doesn't exist
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 3. Allowed Files (Images and PDFs)
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ROUTES ---

@app.route("/", methods=["GET"])
def show_upload_form():
    """Displays the upload form."""
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handles the file upload and MongoDB insertion."""
    
    # 1. Check if file is present
    if 'file' not in request.files:
        flash("No file part", "error")
        return redirect(url_for('show_upload_form'))
    
    file = request.files['file']
    patient_name = request.form.get("patient_name")
    doctor_name = request.form.get("doctor_name")

    # 2. Check if user actually selected a file
    if file.filename == '':
        flash("No selected file", "error")
        return redirect(url_for('show_upload_form'))

    # 3. Validate and Save
    if file and allowed_file(file.filename):
        # Secure the filename (prevents hacking via filenames)
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file to your hard drive
        file.save(file_path)

        # 4. Insert Metadata into MongoDB
        document = {
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "filename": filename,
            "file_path": file_path, # Path where the file is stored
            "upload_date": datetime.now(),
            "status": "stored"
        }
        collection.insert_one(document)

        flash("✅ Prescription Saved to Database Successfully!", "success")
        return redirect(url_for('show_upload_form'))
    
    else:
        flash("Invalid file type. Only PDF, JPG, PNG allowed.", "error")
        return redirect(url_for('show_upload_form'))

if __name__ == "__main__":
    app.run(debug=True, port=5000)