import spacy
from spacy.matcher import Matcher
from db_config import get_db_connection
from fuzzywuzzy import process
from textblob import TextBlob
import json
import datetime

# --- 1. INITIALIZATION ---
print("⏳ Loading Emotional NLP Engine...")
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Cache Medicines (Run this on startup)
medicine_list = []
def setup_cache():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT brand_name FROM medicines")
        rows = cur.fetchall()
        conn.close()
        global medicine_list
        medicine_list = [r['brand_name'] for r in rows if r['brand_name']]
        print(f"✅ Cached {len(medicine_list)} medicines.")
    except Exception as e:
        print(f"⚠️ Cache Error: {e}")

setup_cache()

# --- 2. CONTEXT MANAGER (MEMORY) ---

def save_context(user_id, medicine_name):
    """Save the current medicine to DB for follow-up questions."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        context_json = json.dumps({"last_medicine": medicine_name})
        
        # This SQL requires the UNIQUE constraint on user_identifier
        cur.execute("""
            INSERT INTO bot_sessions (user_identifier, context_data, last_active) 
            VALUES (%s, %s, NOW())
            ON CONFLICT (user_identifier) 
            DO UPDATE SET context_data = %s, last_active = NOW();
        """, (str(user_id), context_json, context_json))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Memory Error (Non-fatal): {e}")

def get_context(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT context_data FROM bot_sessions WHERE user_identifier = %s", (str(user_id),))
        row = cur.fetchone()
        conn.close()
        if row and row['context_data']:
            return row['context_data'].get('last_medicine')
    except:
        return None
    return None

# --- 3. NLP ENGINE ---

def parse_user_input(text, user_id):
    doc = nlp(text.lower())
    matcher = Matcher(nlp.vocab)

    # Define Intents
    matcher.add("COMPARE", [[{"LOWER": "compare"}], [{"LOWER": "vs"}]])
    matcher.add("CHECK_STOCK", [[{"LOWER": "stock"}], [{"LOWER": "qty"}], [{"LOWER": "have"}]])
    matcher.add("CHECK_PRICE", [[{"LOWER": "price"}], [{"LOWER": "cost"}], [{"LOWER": "rate"}]])
    matcher.add("FIND_GENERIC", [[{"LOWER": "generic"}], [{"LOWER": "substitute"}]])
    matcher.add("CHECK_EXPIRY", [[{"LOWER": "expiry"}], [{"LOWER": "expire"}]])
    matcher.add("CHECK_PROFIT", [[{"LOWER": "profit"}], [{"LOWER": "margin"}], [{"LOWER": "benefit"}]])
    matcher.add("FIND_SUPPLIER", [[{"LOWER": "supplier"}], [{"LOWER": "who"}, {"LOWER": "supplies"}], [{"LOWER": "distributor"}]])
    matcher.add("LOW_STOCK_LIST", [[{"LOWER": "reorder"}], [{"LOWER": "low"}, {"LOWER": "stock"}], [{"LOWER": "running"}, {"LOWER": "out"}]])
    # ---------------------------
    # NEW: SALES INTENT
    matcher.add("CHECK_SALES", [[{"LOWER": "sales"}], [{"LOWER": "revenue"}], [{"LOWER": "income"}], [{"LOWER": "sold"}]])
    
    matches = matcher(doc)
    intent = "UNKNOWN"
    if matches:
        match_id, _, _ = matches[-1]
        intent = nlp.vocab.strings[match_id]

    # Entity Extraction (Improved)
    detected_drugs = []
    clean_text = text.lower()
    
    # 1. Exact Match (Case Insensitive)
    for med in medicine_list:
        if med.lower() in clean_text:
            detected_drugs.append(med)
            
    # 2. Fuzzy Fallback
    if not detected_drugs:
        words = text.split()
        for w in words:
            if len(w) > 3: # Ignore small words
                # Lower threshold slightly to 80 to catch 'dolo' vs 'Dolo 650'
                match, score = process.extractOne(w, medicine_list)
                if score >= 80: 
                    detected_drugs.append(match)
                    break
    
    # 3. Context Retrieval
    if not detected_drugs and intent in ["CHECK_STOCK", "CHECK_PRICE", "FIND_GENERIC"]:
        prior_med = get_context(user_id)
        if prior_med: detected_drugs.append(prior_med)

    return {"intent": intent, "entities": {"medicines": list(set(detected_drugs))}}

# --- 4. EXECUTION ENGINE ---

def execute_logic(parsed_data, user_id):
    intent = parsed_data["intent"]
    meds = parsed_data["entities"]["medicines"]
    
    conn = get_db_connection()
    cur = conn.cursor()
    result_text = ""

    try:
        if meds: save_context(user_id, meds[0])

        # --- LOGIC: SALES REPORT ---
        if intent == "CHECK_SALES":
            # Assuming you have a 'sales' or 'bills' table. Adjust table name if needed.
            # Example: Calculating total for today
            cur.execute("SELECT SUM(total_amount) as total FROM sales WHERE date(created_at) = CURRENT_DATE")
            row = cur.fetchone()
            total = row['total'] if row and row['total'] else 0
            result_text = f"💰 <b>Sales Today:</b> ₹{total}"
        elif intent == "CHECK_PROFIT":
            if not meds: return "Which medicine's profit margin do you want to check?"
            target = meds[0]
            cur.execute("SELECT mrp, cost_price FROM medicines WHERE brand_name = %s", (target,))
            res = cur.fetchone()
            
            if res and res['cost_price'] > 0:
                profit = float(res['mrp']) - float(res['cost_price'])
                margin = (profit / float(res['cost_price'])) * 100
                result_text = f"""
                <div class='bot-card' style='border-left: 4px solid #4CAF50;'>
                    <b>💰 Profit Analysis: {target}</b><br>
                    MRP: ₹{res['mrp']}<br>
                    Cost: ₹{res['cost_price']}<br>
                    Profit: <b>₹{profit:.2f}</b> <span style='color:green'>({margin:.1f}%)</span>
                </div>
                """
            else:
                result_text = f"⚠️ Cost price missing for {target}. Cannot calculate margin."

        # 2. SUPPLIER FINDER
        # 2. SUPPLIER FINDER (Updated for supplier_id)
        elif intent == "FIND_SUPPLIER":
            if not meds: return "Which medicine's supplier are you looking for?"
            target = meds[0]
            
            # Using 's.name' because your table defines 'name VARCHAR(100)'
            query = """
                SELECT s.name, s.phone 
                FROM medicines m 
                JOIN suppliers s ON m.supplier_id = s.supplier_id 
                WHERE m.brand_name = %s
            """
            
            try:
                cur.execute(query, (target,))
                res = cur.fetchone()
                
                if res and res['name']:
                    # Added phone number for extra utility
                    contact_info = f" (📞 {res['phone']})" if res['phone'] else ""
                    result_text = f"🚛 The supplier for <b>{target}</b> is <b>{res['name']}</b>{contact_info}."
                else:
                    result_text = f"No supplier linked for <b>{target}</b>."
            except Exception as e:
                result_text = f"Error finding supplier: {str(e)}"

        # 3. LOW STOCK (REORDER) LIST
        elif intent == "LOW_STOCK_LIST":
            cur.execute("SELECT brand_name, quantity FROM medicines WHERE quantity < 15 ORDER BY quantity ASC LIMIT 5")
            rows = cur.fetchall()
            if rows:
                result_text = "<b>⚠️ Reorder Alert (Low Stock):</b><br>"
                for r in rows:
                    result_text += f"• <b>{r['brand_name']}</b>: Only {r['quantity']} left!<br>"
            else:
                result_text = "✅ Stock levels look healthy. Nothing below 15 units."
        
        # ---------------------------
        
        # ... existing elif intent == "CHECK_SALES"

        # --- LOGIC: STOCK / PRICE / UNKNOWN ---
        elif intent in ["CHECK_STOCK", "CHECK_PRICE", "UNKNOWN"]:
            if not meds: 
                # Only return this error if we REALLY don't know the intent
                if intent == "UNKNOWN":
                     return "I didn't understand. Try asking about stock, price, or sales."
                return "Please specify a medicine name."

            target = meds[0]
            cur.execute("SELECT quantity, mrp, location FROM medicines WHERE brand_name = %s", (target,))
            res = cur.fetchone()
            
            if res:
                color = "green" if res['quantity'] > 10 else "red"
                result_text = f"""
                <div class='bot-card'>
                    <b>💊 {target}</b><br>
                    Stock: <span style='color:{color}'><b>{res['quantity']}</b></span> | Rack: {res['location']}<br>
                    Price: ₹{res['mrp']}
                </div>"""
            else:
                result_text = f"🚫 <b>{target}</b> not found in inventory."
        
        # --- LOGIC: GENERIC ---
        elif intent == "FIND_GENERIC":
            target = meds[0]
            cur.execute("SELECT generic_name FROM medicines WHERE brand_name = %s", (target,))
            gen = cur.fetchone()
            if gen and gen['generic_name']:
                cur.execute("SELECT brand_name, mrp FROM medicines WHERE generic_name = %s AND brand_name != %s LIMIT 3", (gen['generic_name'], target))
                subs = cur.fetchall()
                if subs:
                    result_text = f"<b>Substitutes ({gen['generic_name']}):</b><br>" + "".join([f"• {s['brand_name']} (₹{s['mrp']})<br>" for s in subs])
                else: result_text = "No other brands found."
            else: result_text = "No generic info available."

    except Exception as e:
        result_text = f"System Error: {str(e)}"
    finally:
        conn.close()
    
    return result_text

# --- 5. MAIN HANDLER ---
def get_bot_response(text, user_id):
    parsed = parse_user_input(text, user_id)
    return execute_logic(parsed, user_id)