from flask import Blueprint, jsonify, request, session, url_for
from db_config import get_db_connection
from psycopg2.extras import RealDictCursor

notify_bp = Blueprint('notify_bp', __name__, url_prefix='/notifications')

# --- HELPER: Smart Link Generator ---
def get_link_for_type(type, related_id):
    """
    Generates a clickable URL based on the notification type.
    """
    try:
        if type == 'low_stock' or type == 'stock':
            return "/medicines" 
        elif type == 'expiry':
            return "/medicines?filter=expiry"
        elif type == 'sale':
            return f"/sales/invoice/{related_id}" if related_id else "/sales/billing"
        elif type == 'approval':
            return "/admin/approvals"
        
        # --- NEW: Fix for Milestone Error ---
        elif type == 'milestone':
            return "/admin/analytics"
        # ------------------------------------

        return "#"
    except:
        return "#"

# --- 1. API: Get Unread Notifications ---
@notify_bp.route('/get')
def get_notifications():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        user_id = session.get('pharmacist_id') 
        
        # 1. FETCH ALERTS
        query = """
            SELECT notification_id, message, type, related_id, created_at 
            FROM notifications 
            WHERE status = 'Unread'
        """
        params = []

        if user_id:
            query += " AND (pharmacist_id = %s OR pharmacist_id IS NULL)"
            params.append(user_id)
            
        # --- FIX: Increased Limit from 10 to 100 ---
        # This ensures all of your current notifications will show up.
        query += " ORDER BY created_at DESC LIMIT 100" 

        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        
        # Process alerts
        alerts = []
        for row in rows:
            alerts.append({
                "notification_id": row['notification_id'],
                "message": row['message'],
                "type": row['type'], 
                "link": get_link_for_type(row['type'], row['related_id']),
                "created_at": row['created_at']
            })
        
        # 2. COUNT TOTAL UNREAD (For the Red Badge)
        count_query = "SELECT COUNT(*) as count FROM notifications WHERE status = 'Unread'"
        if user_id:
            count_query += " AND (pharmacist_id = %s OR pharmacist_id IS NULL)"
        
        cur.execute(count_query, tuple(params))
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
        cur.execute("UPDATE notifications SET status = 'Read' WHERE notification_id = %s", (id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        cur.close()
        conn.close()

# --- 3. INTERNAL HELPER: Trigger Notification ---
def create_notification(message, type='info', related_id=None, pharmacist_id=None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Anti-Flood Check (Prevent duplicate spam)
        # UPDATED: Checks for ANY notification (Read or Unread) in last 24h
        if related_id:
            cur.execute("""
                SELECT 1 FROM notifications 
                WHERE type = %s AND related_id = %s
                AND created_at > NOW() - INTERVAL '24 hours'
            """, (type, related_id))
        else:
            cur.execute("""
                SELECT 1 FROM notifications 
                WHERE message = %s 
                AND created_at > NOW() - INTERVAL '24 hours'
            """, (message,))
        
        if cur.fetchone():
            return # Skip duplicate

        cur.execute("""
            INSERT INTO notifications (pharmacist_id, message, type, related_id, status, created_at) 
            VALUES (%s, %s, %s, %s, 'Unread', NOW())
        """, (pharmacist_id, message, type, related_id))
        
        conn.commit()
        print(f"🔔 Alert Logged: {message}")
        
    except Exception as e:
        print(f"Notification Creation Error: {e}")
    finally:
        cur.close()
        conn.close()