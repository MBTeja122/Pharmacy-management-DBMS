try:
    import tracery
    from tracery.modifiers import base_english
    HAS_TRACERY = True
except ImportError:
    HAS_TRACERY = False
    print("⚠️ Tracery not installed. Using fallback response system.")

import random

# STATIC Templates (The Vocabulary)
BASE_RULES = {
    # Default placeholders
    "med": ["MEDICINE"], "qty": ["0"], "cost": ["0"], "loc": ["rack"], "revenue": ["0"],
    "person": ["Name"], "phone": ["000"], "date": ["Date"],
    
    # --- Stock & Price ---
    "stock_neutral": [
        "📦 Inventory Check: We have #qty# units of #med# at #loc#.",
        "✅ System shows #qty# #med# available in #loc#.",
        "📊 Stock Status: #med# is in #loc# (Qty: #qty#)."
    ],
    "stock_low": [
        "⚠️ Low Stock Alert: Only #qty# units of #med# left!",
        "🚨 Urgent: #med# is running low (#qty# units). Reorder advised.",
        "⚠️ Stock Warning: #med# is down to #qty#."
    ],
    "price_neutral": [
        "💰 The MRP for #med# is #cost#.",
        "💵 Price Check: #med# sells for #cost#.",
        "💰 It costs #cost# for #med#."
    ],
    
    # --- Suppliers & Customers ---
    "supplier_info": [
        "🚚 Supplier Details: #person# (Phone: #phone#).",
        "📞 Contact #person# at #phone# for supplies.",
        "ℹ️ Supplier info for #person#: Call #phone#."
    ],
    "supplier_product": [
        "🚚 #med# is supplied by #person# (#phone#).",
        "📦 Source: #person# provides #med#. Call them at #phone#.",
        "ℹ️ #med# supplier: #person# | Phone: #phone#"
    ],
    "customer_info": [
        "👤 Customer: #person# | Points: #qty# | Phone: #phone#",
        "💳 Loyalty Check: #person# has #qty# points.",
        "✅ Found #person#: They have #qty# loyalty points."
    ],
    
    # --- Sales & Alerts ---
    "sales_report": [
        "💰 Today's Revenue: #revenue#.",
        "📊 Total sales recorded today: #revenue#.",
        "💼 Business Update: We have made #revenue# today."
    ],
    "expiry_alert": [
        "📅 Expiry Warning: #med# expires on #date#.",
        "⚠️ Shelf Life: #med# is valid until #date#. Check stock.",
        "🚨 Caution: #med# is nearing expiry (#date#)."
    ],
    "greeting": [
        "👋 Hi! I'm your Pharmacy Assistant. I can check Stock, Sales, Suppliers, and Expiry.",
        "Hello! Ask me about medicines ('Price of Dolo'), suppliers ('Who supplies this?'), or sales.",
        "👋 Welcome! I can help you with inventory, pricing, suppliers, and customer info."
    ]
}

def fmt(val):
    """Formats currency nicely (e.g. 1200 -> ₹1,200.00)"""
    if val is None: return "₹0.00"
    return f"₹{float(val):,.2f}"

def generate_response(template_key, **kwargs):
    """Fills the template with real data."""
    if HAS_TRACERY:
        try:
            rules_copy = BASE_RULES.copy()
            for key, value in kwargs.items():
                rules_copy[key] = [str(value)]
            grammar = tracery.Grammar(rules_copy)
            grammar.add_modifiers(base_english)
            return grammar.flatten(f"#{template_key}#")
        except:
            pass # Fall through to fallback
            
    # Fallback System
    templates = BASE_RULES.get(template_key, ["Response not found."])
    template = random.choice(templates)
    for key, value in kwargs.items():
        template = template.replace(f"#{key}#", str(value))
    return template