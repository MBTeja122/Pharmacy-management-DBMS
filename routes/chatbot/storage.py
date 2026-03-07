import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
try:
    from db_config import get_db_connection
except ImportError:
    from ...db_config import get_db_connection

# --- INTERNAL CACHE ---
_cache = {
    'medicines': [],
    'suppliers': [],
    'customers': []
}

def setup_cache():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Medicines
        cur.execute("""
            SELECT DISTINCT brand_name FROM medicines 
            WHERE brand_name IS NOT NULL AND brand_name != ''
            UNION
            SELECT DISTINCT generic_name FROM medicines 
            WHERE generic_name IS NOT NULL AND generic_name != ''
        """)
        rows = cur.fetchall()
        _cache['medicines'] = [r['brand_name'] if isinstance(r, dict) and 'brand_name' in r else r[0] for r in rows]

        # 2. Suppliers
        cur.execute("SELECT DISTINCT name FROM suppliers WHERE name IS NOT NULL AND name != ''")
        rows = cur.fetchall()
        _cache['suppliers'] = [r['name'] if isinstance(r, dict) and 'name' in r else r[0] for r in rows]

        # 3. Customers
        cur.execute("SELECT DISTINCT name FROM customers WHERE name IS NOT NULL AND name != ''")
        rows = cur.fetchall()
        _cache['customers'] = [r['name'] if isinstance(r, dict) and 'name' in r else r[0] for r in rows]

        cur.close()
        conn.close()
        print(f"✅ Brain Loaded: {len(_cache['medicines'])} Meds, {len(_cache['suppliers'])} Suppliers.")
    except Exception as e:
        print(f"⚠️ Cache Error: {e}")
        if conn: conn.close()

def get_cache(key):
    return _cache.get(key, [])

def save_context(user_id, context_data):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        context_json = json.dumps(context_data)
        
        cur.execute("""
            INSERT INTO bot_sessions (user_identifier, context_data, last_active, message_count) 
            VALUES (%s, %s, CURRENT_TIMESTAMP, 1)
            ON CONFLICT (user_identifier) 
            DO UPDATE SET 
                context_data = %s, 
                last_active = CURRENT_TIMESTAMP, 
                message_count = bot_sessions.message_count + 1
        """, (str(user_id), context_json, context_json))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Context Save Error: {e}")
        if conn: conn.close()

def get_context(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT context_data FROM bot_sessions WHERE user_identifier = %s", (str(user_id),))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            data = row['context_data'] if isinstance(row, dict) else row[0]
            return data if isinstance(data, dict) else json.loads(data)
        return {}
    except Exception as e:
        if conn: conn.close()
        return {}

def log_interaction(user_id, user_msg, bot_reply, intent, confidence=0.0, exec_time=0):
    conn = None
    try:
        # CRITICAL FIX: Normalize confidence score (50 -> 0.5)
        if confidence > 1.0:
            confidence = confidence / 100.0
            
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO bot_logs 
            (user_identifier, user_message, bot_response, detected_intent, confidence_score, execution_time_ms, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (str(user_id), user_msg, bot_reply, intent, confidence, exec_time))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Log Error: {e}")
        if conn: conn.close()