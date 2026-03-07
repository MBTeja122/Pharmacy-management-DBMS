from flask import Flask, render_template, session, redirect, url_for
from datetime import timedelta
import os
import socket

from routes.home_routes import home_bp
from routes.create_account import cre_acc_bp
from routes.medicines_routes import medicine_bp
from routes.auth_routes import auth_bp
from routes.dashboard_home import dash_bp
from routes.supplier_routes import suppliers_bp
from routes.cutomers_routes import customers_bp
from routes.billing_routes import sales_bp
from routes.admin_routes import admin_bp
from routes.dashboard_routes import dash_bp1
from routes.chatbot_routes import chatbot_bp
from routes.notification_routes import notify_bp
from routes.prescription_routes import prescriptions_bp
from routes.audit_routes import audit_bp

app = Flask(__name__)
app.secret_key = "PHARMA_SECRET_KEY_123"
app.permanent_session_lifetime = timedelta(minutes=30)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

app.register_blueprint(home_bp)
app.register_blueprint(cre_acc_bp)
app.register_blueprint(medicine_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(dash_bp)
app.register_blueprint(suppliers_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(sales_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(dash_bp1)
app.register_blueprint(chatbot_bp)
app.register_blueprint(notify_bp)
app.register_blueprint(prescriptions_bp, url_prefix='/prescriptions')
app.register_blueprint(audit_bp)
@app.route("/")
def index():
    return redirect(url_for('prescriptions_bp.show_upload_form'))

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    ip = get_local_ip()
    port = 5000
    
    print("\n-------------------------------------------------------")
    print("🚀 PHARMA SERVER STARTED (HTTP Mode)")
    print(f"📡 Mobile Upload Link: http://{ip}:{port}/prescriptions/remote_upload")
    print("-------------------------------------------------------")
    
    # SSL Removed! Now running on standard HTTP.
    app.run(debug=True, host='0.0.0.0', port=port)