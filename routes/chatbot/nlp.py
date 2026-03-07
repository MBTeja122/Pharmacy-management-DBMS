import spacy
from fuzzywuzzy import process, fuzz
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from .storage import get_cache

# 1. LOAD SPACY MODEL
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    print("📥 Downloading spaCy model...")
    os.system("python -m spacy download en_core_web_md")
    nlp = spacy.load("en_core_web_md")

# 2. SLANG MAPPING
SLANG_MAP = {
    "chk": "check", "stck": "stock", "stk": "stock",
    "amt": "amount", "qty": "quantity", "exp": "expiry",
    "dt": "date", "wht": "what", "whr": "where",
    "med": "medicine", "sup": "supplier", "cust": "customer",
    "hav": "have", "sub": "substitute", "alt": "alternative"
}

def normalize_text(text):
    if not text: return ""
    words = text.lower().split()
    fixed_words = [SLANG_MAP.get(w, w) for w in words]
    return " ".join(fixed_words)

# 3. KEYWORD RULES (CRITICAL: Specific -> Generic)
KEYWORD_OVERRIDES = {
    # --- [TIER 1] ANALYTICS & VISUALS ---
    "SHOW_ANALYSIS": ["graph", "chart", "plot", "trend", "analysis", "statistics", "performance", "top selling"],
    
    # [FIXED] BROADER KEYWORDS FOR VALUE
    "INVENTORY_VALUE": [
        "total value", "stock value", "inventory worth", "total asset", "stock cost", 
        "value of stock", "inventory value", "total inventory", "how much is stock"
    ],
    
    # --- [TIER 2] SPECIFIC ACTIONS ---
    "FIND_SUBSTITUTE": ["substitute", "alternative", "replacement", "generic of", "instead of", "replace", "sub for"],
    "SUPPLIER_ITEMS": ["products by", "items from", "list medicines from", "catalog", "sold by", "supplied by"],
    "CHECK_DETAILS": ["details", "info", "information", "specs", "specification", "full info"],

    # --- [TIER 3] GENERIC QUERIES ---
    "SALES_TODAY": ["sales", "revenue", "income", "collection", "today"], 
    "CHECK_SUPPLIER": ["supplier", "distributor", "vendor", "manufacturer", "who supplies"], 
    "CHECK_EXPIRY": ["expire", "expiry", "validity", "shelf life", "date", "when does"],
    "CHECK_PRICE": ["price", "cost", "mrp", "how much", "rate", "bill"],
    "CUSTOMER_INFO": ["customer", "client", "points", "loyalty"],
    "LOW_STOCK": ["low stock", "running out", "shortage"],
    "GREETING": ["hi", "hello", "hey", "greetings"],
    
    "CHECK_STOCK": ["stock", "available", "have", "quantity", "inventory", "do you have"],
}
# (Intent Refs for Vectors)
intent_refs = {
    "CHECK_PRICE": nlp("price cost mrp charge how much"),
    "CHECK_STOCK": nlp("stock quantity available count left have inventory"),
    "SALES_TODAY": nlp("sales revenue sold income bill invoice today"),
    "CHECK_SUPPLIER": nlp("supplier distributor vendor who supplies"),
    "CHECK_EXPIRY": nlp("expire expiry date validity rotting"),
    "CUSTOMER_INFO": nlp("customer client patient loyalty points"),
    "GREETING": nlp("hi hello hey greetings good morning"),
    "FIND_SUBSTITUTE": nlp("substitute alternative replacement generic"),
    "INVENTORY_VALUE": nlp("total value worth assets cost"),
    "SUPPLIER_ITEMS": nlp("products items catalog list"),
    "SHOW_ANALYSIS": nlp("graph chart trend plot statistics analysis")
}

def get_hybrid_intent(text, doc):
    text_lower = text.lower()
    
    # 1. Keywords
    for intent, keywords in KEYWORD_OVERRIDES.items():
        if any(k in text_lower for k in keywords):
            if intent == "SALES_TODAY" and "today" not in text_lower: continue
            return intent
            
    # 2. Vectors
    if not doc.has_vector or doc.vector_norm == 0: return "GENERAL_QUERY"
    best_intent = "GENERAL_QUERY"
    best_score = 0.0
    for intent, ref_doc in intent_refs.items():
        score = doc.similarity(ref_doc)
        if score > best_score:
            best_score = score
            best_intent = intent
    if best_score > 0.40: return best_intent
    return "GENERAL_QUERY"

def extract_smart_entities(text, doc):
    clean_text = text.replace("?", "").replace(".", "")
    words = clean_text.split()
    chunks = words + [" ".join(pair) for pair in zip(words, words[1:])]
    
    ignore_list = [
        "price", "stock", "sales", "supplier", "check", "expiry", "customer", 
        "who", "what", "is", "the", "of", "for", "in", "details", "does", "do",
        "value", "total", "substitute", "alternative", "products", "by", "from", 
        "items", "graph", "chart", "trend", "analysis"
    ]

    # --- PHASE 1: DATABASE MATCHING ---
    def search_category(category_name, type_label):
        data_list = get_cache(category_name)
        if not data_list: return None
        
        best_match = None
        best_score = 0
        
        for chunk in chunks:
            if chunk.lower() in ignore_list or len(chunk) < 2: continue
            match, score = process.extractOne(chunk, data_list, scorer=fuzz.WRatio)
            if score > best_score:
                best_score = score
                best_match = match
        
        if best_score >= 60:
            return {'value': best_match, 'type': type_label, 'confidence': best_score}
        return None

    med_match = search_category('medicines', 'medicine')
    if med_match: return med_match
    
    sup_match = search_category('suppliers', 'supplier')
    if sup_match: return sup_match
    
    cust_match = search_category('customers', 'customer')
    if cust_match: return cust_match

    # --- PHASE 2: GRAMMAR FALLBACK ---
    candidates = []
    for token in doc:
        if token.pos_ in ["PROPN", "NOUN"] and len(token.text) > 2:
            if token.text.lower() not in ignore_list and token.text.lower() not in SLANG_MAP.keys():
                candidates.append(token.text)
    
    if candidates:
        return {'value': candidates[-1], 'type': 'unknown', 'confidence': 50}
    
    return None

def parse_input(text):
    norm_text = normalize_text(text)
    doc = nlp(norm_text.lower())
    intent = get_hybrid_intent(norm_text, doc)
    entity = extract_smart_entities(norm_text, doc)
    return intent, entity