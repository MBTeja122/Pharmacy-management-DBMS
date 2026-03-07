import spacy
from spacy.matcher import Matcher
from fuzzywuzzy import process, fuzz
import nltk
from nltk.corpus import wordnet
import os

# ==========================================
# 1. SETUP (Auto-Download NLTK & SpaCy)
# ==========================================
print("⏳ Initializing Hybrid Brain...")

# Auto-download NLTK data quietly
try:
    nltk.data.find('corpora/wordnet.zip')
except LookupError:
    print("   -> Downloading NLTK WordNet...")
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

# Load SpaCy
try:
    nlp = spacy.load("en_core_web_sm")
except:
    print("   -> Downloading SpaCy model...")
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# ==========================================
# 2. THE HYBRID LOGIC (NLTK + SpaCy)
# ==========================================
def get_synonyms(word):
    synonyms = {word}
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            clean_word = lemma.name().replace("_", " ").lower()
            synonyms.add(clean_word)
    return list(synonyms)

print("🧠 Generating Synonyms...")
# We use NLTK to find words, but we ALSO manually add specific pharmacy terms
sales_vocab = get_synonyms("sale") + ["revenue", "income", "turnover", "sold", "bill", "invoice", "transaction"]
price_vocab = get_synonyms("price") + ["cost", "mrp", "rate", "value", "charge", "amount", "worth"]
stock_vocab = get_synonyms("stock") + ["quantity", "inventory", "count", "available", "left", "have"]
expiry_vocab = get_synonyms("expire") + ["expiry", "expiration", "validity"]

# Feed patterns into SpaCy
matcher = Matcher(nlp.vocab)
patterns = {
    "SALES_INTENT": [
        [{"LOWER": {"IN": sales_vocab}}, {"LOWER": {"IN": ["today", "today's"]}}],
        [{"LOWER": {"IN": ["today", "today's"]}}, {"OP": "?"}, {"LOWER": {"IN": sales_vocab}}],
        [{"LOWER": "how"}, {"LOWER": "much"}, {"LOWER": {"IN": ["sold", "made", "earned"]}}]
    ],
    "CHECK_STOCK": [
        [{"LOWER": {"IN": stock_vocab}}, {"LOWER": {"IN": ["of", "for"]}, "OP": "?"}],
        [{"LOWER": "how"}, {"LOWER": "many"}]
    ],
    "CHECK_PRICE": [
        [{"LOWER": {"IN": price_vocab}}, {"LOWER": {"IN": ["of", "for"]}, "OP": "?"}]
    ],
    "EXPIRING_SOON": [
        [{"LOWER": {"IN": expiry_vocab}}, {"LOWER": "soon"}],
        [{"LOWER": "close"}, {"LOWER": "to"}, {"LOWER": {"IN": expiry_vocab}}]
    ]
}

for intent, pat in patterns.items():
    matcher.add(intent, pat)

# ==========================================
# 3. FAKE DATABASE (For Testing Only)
# ==========================================
# In the real app, this comes from your SQL DB
mock_medicine_list = ["Dolo 650", "Paracetamol", "Aspirin", "Crosin", "Metformin", "Amoxicillin"]

def extract_entities(text):
    found = []
    clean_text = text.lower()
    
    # 1. Exact Match
    for med in mock_medicine_list:
        if med.lower() in clean_text:
            found.append(med)
            
    # 2. Fuzzy Match (If user types "Doolo")
    if not found:
        words = text.split()
        for word in words:
            match, score = process.extractOne(word, mock_medicine_list, scorer=fuzz.token_sort_ratio)
            if score >= 80: # 80% similarity threshold
                found.append(match)
                break
    return list(set(found))

# ==========================================
# 4. MAIN TEST LOOP
# ==========================================
print("\n✅ TEST MODE READY!")
print("Try these queries to prove it works:")
print("  - 'What is the charge for Dolo?' (Tests NLTK synonyms)")
print("  - 'How much revenue today?' (Tests NLTK synonyms)")
print("  - 'How many Aspirin left?' (Tests Matcher Patterns)")
print("  - 'Any items close to expiry?' (Tests Expiry Logic)")
print("-" * 50)

while True:
    user_text = input("\nYou: ")
    if user_text.lower() in ['exit', 'quit']: break
    
    doc = nlp(user_text.lower())
    matches = matcher(doc)
    
    # Intent Detection
    intent = "UNKNOWN"
    if matches:
        match_id, _, _ = matches[-1] # Take the last (longest) match
        intent = nlp.vocab.strings[match_id]
    
    # Entity Detection
    entities = extract_entities(user_text)
    
    print(f"🤖 Bot Detected -> Intent: [{intent}] | Entities: {entities}")
    
    if intent == "UNKNOWN":
        print("   (Debug: Check if your word is in the NLTK lists above)")