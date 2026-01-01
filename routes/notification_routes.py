from flask import Blueprint, jsonify, request
from db_config import get_db_connection
from psycopg2.extras import RealDictCursor

notify_bp = Blueprint('notify_bp', __name__, url_prefix='/notifications')

# --- 1. API: Get Unread Notifications (For Frontend Polling) ---
@notify_bp.route('/get')
def get_notifications():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT * FROM notifications 
            WHERE is_read = FALSE 
            ORDER BY created_at DESC LIMIT 5
        """)
        alerts = cur.fetchall()
        
        cur.execute("SELECT COUNT(*) as count FROM notifications WHERE is_read = FALSE")
        res = cur.fetchone()
        count = res['count'] if res else 0
        
        return jsonify({"alerts": alerts, "count": count})
    except Exception as e:
        print(f"Notify Get Error: {e}")
        return jsonify({"alerts": [], "count": 0})
    finally:
        conn.close()

# --- 2. API: Mark as Read (When clicked) ---
@notify_bp.route('/read/<int:id>', methods=['POST'])
def mark_read(id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE notifications SET is_read = TRUE WHERE notification_id = %s", (id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        conn.close()

# --- 3. INTERNAL HELPER: Trigger Notification (Used by Python) ---
def create_notification(message, type='info', link='#'):
    """
    Types: 'info' (Blue), 'success' (Green), 'warning' (Yellow), 'danger' (Red)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO notifications (message, type, link) 
            VALUES (%s, %s, %s)
        """, (message, type, link))
        conn.commit()
    except Exception as e:
        print(f"Notification Error: {e}")
    finally:
        conn.close()