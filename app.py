from flask import Flask  , render_template, session, redirect, url_for
from datetime import timedelta
import os
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
@app.route("/")
def index():
    return redirect(url_for('prescriptions_bp.show_upload_form'))

if __name__ == "__main__":
    print("\n-------------------------------------------------------")
    print("🚀 PHARMA SERVER STARTING (OFFLINE HOTSPOT MODE)")
    print("-------------------------------------------------------")
    print("1. Ensure Laptop Hotspot is ON.")
    print("2. Connect Phone to Laptop Hotspot.")
    print("3. IGNORE 'Not Secure' warnings on the phone.")
    print("-------------------------------------------------------\n")

    # host='0.0.0.0' -> Allows connection from external devices (Phone)
    # ssl_context='adhoc' -> Enables HTTPS (Required for Camera access)
    
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context='adhoc')