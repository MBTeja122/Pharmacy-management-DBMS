from db_config import get_db_connection
from werkzeug.security import generate_password_hash

# 1. FETCH ONLY ACTIVE STAFF (For Login Screen)
def get_all_pharmacists():
    conn = get_db_connection()
    cur = conn.cursor()
    # QUERY UPDATED: Only show users where active = TRUE
    cur.execute("""
        SELECT pharmacist_id, name, role 
        FROM pharmacists 
        WHERE active = TRUE 
        ORDER BY CASE WHEN role='Admin' THEN 0 ELSE 1 END, pharmacist_id;
    """)
    employees = cur.fetchall()
    cur.close()
    conn.close()
    return employees

# 2. CREATE ACCOUNT (Set Active = FALSE by default)
def create_pharmacist(name, email, phone, password, role):
    conn = get_db_connection()
    cur = conn.cursor()
    
    hashed_pw = generate_password_hash(password)

    try:
        # QUERY UPDATED: Explicitly insert 'active' as FALSE
        cur.execute("""
            INSERT INTO pharmacists (name, email, phone, password_hash, role, active)
            VALUES (%s, %s, %s, %s, %s, FALSE);
        """, (name, email, phone, hashed_pw, role))
        
        conn.commit()
        # Updated success message
        return True, "Account created! Please wait for Admin approval to access the system."

    except Exception as err:
        conn.rollback()
        return False, f"Error: {err}"

    finally:
        cur.close()
        conn.close()