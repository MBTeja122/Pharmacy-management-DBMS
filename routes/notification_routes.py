from flask import Blueprint, jsonify, request
from db_config import get_db_connection
from psycopg2.extras import RealDictCursor

notify_bp = Blueprint('notify_bp', __name__, url_prefix='/notifications')

# --- 1. API: Get Unread Notifications ---
@notify_bp.route('/get')
def get_notifications():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Fetches notifications. Works with both 'status' or 'is_read' columns
        # We assume you settled on 'is_read' based on previous context
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
        cur.close()
        conn.close()

# --- 2. API: Mark as Read ---
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
        cur.close()
        conn.close()

# --- 3. INTERNAL HELPER: Smart Notification Trigger (ANT-SPAM ADDED) ---
def create_notification(message, type='info', link='#'):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 🛡️ ANTI-SPAM CHECK:
        # Only insert if this exact message wasn't sent in the last 24 hours
        cur.execute("""
            SELECT 1 FROM notifications 
            WHERE message = %s 
            AND created_at > NOW() - INTERVAL '24 hours'
        """, (message,))
        
        if cur.fetchone():
            return # Skip! We already sent this today.

        cur.execute("""
            INSERT INTO notifications (message, type, link, is_read) 
            VALUES (%s, %s, %s, FALSE)
        """, (message, type, link))
        conn.commit()
        print(f"🔔 Alert Sent: {message}")
        
    except Exception as e:
        print(f"Notification Error: {e}")
    finally:
        cur.close()
        conn.close()