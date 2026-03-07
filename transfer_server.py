import os
import io
import base64
import socket
import qrcode
import uvicorn
from fastapi import FastAPI, APIRouter, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# --- CONFIGURATION ---
# IMPORTANT: This points to your Flask static folder!
UPLOAD_DIR = "static/uploads/prescriptions"
PORT = 8000
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/transfer", tags=["File Transfer"])

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# --- HTML TEMPLATES (Your working templates) ---
MOBILE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta charset="UTF-8">
    <title>Upload to Pharmacy</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #e0f2f1; min-height: 100vh; padding: 20px; display: flex; align-items: center; justify-content: center; }
        .card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); width: 100%; max-width: 400px; text-align: center; }
        h2 { color: #00695c; margin-bottom: 10px; }
        .file-label { display: block; padding: 20px; background: #f5f5f5; border: 2px dashed #00695c; border-radius: 10px; margin: 20px 0; cursor: pointer; }
        .file-label.has-file { background: #e0f2f1; border-style: solid; }
        button { background: #00695c; color: white; padding: 15px; width: 100%; border: none; border-radius: 10px; font-size: 18px; font-weight: bold; cursor: pointer; }
        button:disabled { background: #ccc; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🏥 Pharmacy Upload</h2>
        <p>Select prescription from Gallery</p>
        <form id="uploadForm" action="/transfer/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" id="fileInput" accept="image/*" required style="display:none">
            <label for="fileInput" class="file-label" id="fileLabel">📁 Tap to Select File</label>
            <button type="submit" id="submitBtn" disabled>Send to PC</button>
        </form>
    </div>
    <script>
        document.getElementById('fileInput').addEventListener('change', function(e) {
            if(e.target.files[0]) {
                document.getElementById('fileLabel').classList.add('has-file');
                document.getElementById('fileLabel').innerText = '✅ ' + e.target.files[0].name;
                document.getElementById('submitBtn').disabled = false;
            }
        });
    </script>
</body>
</html>
"""

SUCCESS_HTML = """
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Done</title></head>
<body style="background:#e0f2f1; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh;">
    <div style="background:white; padding:40px; border-radius:20px; text-align:center; box-shadow:0 10px 20px rgba(0,0,0,0.1);">
        <div style="font-size:60px;">✅</div>
        <h1 style="color:#00695c;">Upload Complete!</h1>
        <p>You can close this tab now.</p>
    </div>
</body>
</html>
"""

# --- ROUTES ---
@router.get("/mobile", response_class=HTMLResponse)
async def mobile_page():
    return HTMLResponse(MOBILE_HTML)

@router.post("/upload")
async def handle_upload(file: UploadFile = File(...)):
    # Create a unique filename so we don't overwrite existing ones
    filename = f"mobile_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create a signal file for Flask
    with open(f"signal_latest_upload.txt", "w") as f:
        f.write(filename)

    return HTMLResponse(SUCCESS_HTML)

app.include_router(router)

if __name__ == "__main__":
    ip = get_local_ip()
    print(f"\n🚀 TRANSFER SERVER RUNNING: http://{ip}:{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)