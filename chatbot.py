import spacy
from spacy.matcher import Matcher
from db_config import get_db_connection
from fuzzywuzzy import process
from textblob import TextBlob  # pip install textblob
import random

# --- 1. INITIALIZATION ---
print("⏳ Loading Emotional NLP Engine...")
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Cache Medicines
medicine_list = []
def setup_cache():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT brand_name FROM medicines")
    rows = cur.fetchall()
    conn.close()
    global medicine_list
    medicine_list = [r['brand_name'] for r in rows if r['brand_name']]

setup_cache()

# --- 2. THE EMOTIONAL BRAIN (Tone Detection) ---

def analyze_tone(text):
    """
    Detects if the user is Urgent, Angry, Happy, or Neutral.
    """
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # -1.0 (Negative) to +1.0 (Positive)
    text_lower = text.lower()
    
    # 1. Check Urgency
    urgent_keywords = ["fast", "quick", "asap", "urgent", "emergency", "now", "hurry"]
    is_urgent = any(w in text_lower for w in urgent_keywords)
    
    # 2. Check Emotion
    if is_urgent:
        return "URGENT"
    elif polarity < -0.3 or any(w in text_lower for w in ["wrong", "bad", "stupid", "useless", "slow"]):
        return "FRUSTRATED"
    elif polarity > 0.5 or any(w in text_lower for w in ["great", "thanks", "good", "love"]):
        return "HAPPY"
    else:
        return "NEUTRAL"

def adapt_response_style(core_answer, tone):
    """
    Rewrites the answer based on the detected tone.
    """
    if tone == "URGENT":
        return f"🚀 **Quick Update:** {core_answer}"
    
    elif tone == "FRUSTRATED":
        return f"😓 I apologize if things are slow. Let me double-check that for you...<br>{core_answer}<br><i>I hope this helps resolve the issue.</i>"
    
    elif tone == "HAPPY":
        return f"✨ Happy to help! {core_answer} Let me know if you need anything else! 🌟"
    
    else: # Neutral
        return core_answer

# --- 3. NLU ENGINE (Intent Detection) ---

def parse_user_input(text):
    doc = nlp(text.lower())
    matcher = Matcher(nlp.vocab)

    # Define Intents
    matcher.add("COMPARE", [[{"LOWER": "compare"}], [{"LOWER": "vs"}], [{"LOWER": "better"}]])
    matcher.add("FILTER_PRICE", [[{"LOWER": "under"}, {"LIKE_NUM": True}], [{"LOWER": "cheaper"}, {"LOWER": "than"}]])
    matcher.add("CHECK_STOCK", [[{"LOWER": "stock"}], [{"LOWER": "qty"}], [{"LOWER": "have"}]])
    matcher.add("CHECK_PRICE", [[{"LOWER": "price"}], [{"LOWER": "cost"}], [{"LOWER": "rate"}]])
    
    matches = matcher(doc)
    intent = "UNKNOWN"
    if matches:
        match_id, _, _ = matches[-1]
        intent = nlp.vocab.strings[match_id]

    # Entity Extraction (Fuzzy)
    detected_drugs = []
    clean_text = text.lower()
    words = text.split()
    
    # 1. Check exact matches in our cache
    for med in medicine_list:
        if med.lower() in clean_text:
            detected_drugs.append(med)
            
    # 2. Fuzzy Fallback if no exact match
    if not detected_drugs:
        for w in words:
            if w.lower() in ["stock", "price", "of", "the", "compare", "fast", "urgent"]: continue
            match, score = process.extractOne(w, medicine_list)
            if score > 88: 
                detected_drugs.append(match)
                break
    
    entities = {"medicines": list(set(detected_drugs)), "number": None}
    
    for token in doc:
        if token.like_num:
            entities["number"] = float(token.text)

    return {"intent": intent, "entities": entities}

# --- 4. EXECUTION ENGINE (SQL) ---

def execute_logic(parsed_data):
    intent = parsed_data["intent"]
    meds = parsed_data["entities"]["medicines"]
    number = parsed_data["entities"]["number"]
    
    conn = get_db_connection()
    cur = conn.cursor()
    result_text = ""

    try:
        # LOGIC: COMPARE
        if intent == "COMPARE":
            if len(meds) < 2: return "I need two medicines to compare."
            placeholders = ', '.join(['%s'] * len(meds))
            cur.execute(f"SELECT brand_name, mrp, quantity FROM medicines WHERE brand_name IN ({placeholders})", tuple(meds))
            rows = cur.fetchall()
            if rows:
                result_text = "<b>Comparison Result:</b><br>"
                for r in rows: result_text += f"• {r['brand_name']}: ₹{r['mrp']} (Qty: {r['quantity']})<br>"
            else: result_text = "Could not find those items."

        # LOGIC: PRICE FILTER
        elif intent == "FILTER_PRICE":
            limit = number if number else 100
            cur.execute("SELECT brand_name, mrp FROM medicines WHERE mrp < %s LIMIT 5", (limit,))
            rows = cur.fetchall()
            if rows:
                result_text = f"Items under ₹{limit}:<br>" + "".join([f"• {r['brand_name']} - ₹{r['mrp']}<br>" for r in rows])
            else: result_text = "No cheap items found."

        # LOGIC: STANDARD QUERY
        elif intent in ["CHECK_STOCK", "CHECK_PRICE", "UNKNOWN"]:
            if not meds: return "Please specify a medicine name."
            target = meds[0]
            cur.execute("SELECT quantity, mrp, location FROM medicines WHERE brand_name = %s", (target,))
            res = cur.fetchone()
            
            if res:
                if intent == "CHECK_PRICE":
                    result_text = f"The price of **{target}** is ₹{res['mrp']}."
                else: # Default to Stock
                    status = "Healthy" if res['quantity'] > 10 else "Low"
                    result_text = f"**{target}**<br>Stock: {res['quantity']} ({status})<br>Rack: {res['location']}"
            else:
                result_text = f"I cannot find details for **{target}**."
        
        else:
            result_text = "I'm not sure how to answer that."

    except Exception as e:
        result_text = f"System Error: {str(e)}"
    finally:
        conn.close()
    
    return result_text

# --- 5. MAIN BOT HANDLER ---

def get_bot_response(text, user_id="guest"):
    # Step 1: Detect Tone
    tone = analyze_tone(text)
    
    # Step 2: Understand Intent
    parsed = parse_user_input(text)
    
    # Step 3: Get Raw Fact (SQL Result)
    raw_answer = execute_logic(parsed)
    
    # Step 4: Adapt Answer to Tone
    final_response = adapt_response_style(raw_answer, tone)
    
    return final_response