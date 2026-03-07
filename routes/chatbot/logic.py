import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from .storage import get_db_connection, save_context, get_context
from .responses import generate_response, fmt

def execute_logic(intent, entity, user_id, text):
    print(f"🤖 LOGIC: Intent='{intent}', Entity='{entity}'")

    conn = None
    cur = None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. GLOBAL COMMANDS
        if intent == "SALES_TODAY":
            cur.execute("SELECT COALESCE(SUM(total_amount), 0) as revenue FROM sales WHERE DATE(created_at) = CURRENT_DATE")
            r = cur.fetchone()
            rev = r['revenue'] if r else 0
            return generate_response("sales_report", revenue=fmt(rev))

        if intent == "GREETING":
            return generate_response("greeting")

        # 2. TARGET RESOLUTION
        target_name = None
        target_type = None
        
        if entity:
            target_name = entity['value']
            target_type = entity['type']
            save_context(user_id, {'last_entity': target_name, 'last_type': target_type, 'last_intent': intent})
        else:
            ctx = get_context(user_id)
            if intent == "GENERAL_QUERY" and ctx.get('last_intent'): intent = ctx['last_intent']
            is_new = any(x in text.lower() for x in [" of ", " for ", " about "])
            if not is_new and ctx.get('last_entity'):
                target_name = ctx['last_entity']
                target_type = ctx.get('last_type', 'medicine')

        # 3. ENTITY COMMANDS
        
        # --- STOCK ---
        if intent == "CHECK_STOCK":
            if not target_name: return "❓ Which medicine?"
            # Use Wildcards for broader matching
            cur.execute("SELECT quantity, location FROM medicines WHERE brand_name ILIKE %s OR generic_name ILIKE %s", (f"%{target_name}%", f"%{target_name}%"))
            r = cur.fetchone()
            if r:
                return generate_response("stock_neutral", med=target_name, qty=r['quantity'], loc=r['location'])
            return f"❌ '{target_name}' not found."

        # --- PRICE ---
        if intent == "CHECK_PRICE":
            if not target_name: return "❓ Which medicine?"
            cur.execute("SELECT mrp FROM medicines WHERE brand_name ILIKE %s OR generic_name ILIKE %s", (f"%{target_name}%", f"%{target_name}%"))
            r = cur.fetchone()
            if r and r['mrp']:
                return generate_response("price_neutral", med=target_name, cost=fmt(r['mrp']))
            return f"❌ Price not available for {target_name}."

        # --- SUPPLIER (Smart Fallback) ---
        if intent == "CHECK_SUPPLIER":
            if not target_name: return "❓ Which supplier or medicine?"
            
            # 1. Try Supplier Table
            if target_type in ['supplier', 'unknown']:
                cur.execute("SELECT phone FROM suppliers WHERE name ILIKE %s", (f"%{target_name}%",))
                r = cur.fetchone()
                if r: 
                    return f"🚚 Supplier: {target_name} (Phone: {r['phone']})"
            
            # 2. Try Medicine Table (Find supplier via medicine)
            if target_type in ['medicine', 'unknown']:
                cur.execute("SELECT s.name, s.phone FROM suppliers s JOIN medicines m ON m.supplier_id = s.supplier_id WHERE m.brand_name ILIKE %s", (f"%{target_name}%",))
                r = cur.fetchone()
                if r: 
                    return generate_response("supplier_product", med=target_name, person=r['name'], phone=r['phone'])

            return f"❌ Could not find supplier information for '{target_name}'."
        if intent == "CHECK_DETAILS":
            if not target_name: return "❓ Which medicine do you want details for?"
            
            # Fetch EVERYTHING including Supplier Name
            cur.execute("""
                SELECT m.brand_name, m.generic_name, m.strength, m.form, m.mrp, m.quantity, m.location, m.expiry_date, s.name as supplier_name
                FROM medicines m
                LEFT JOIN suppliers s ON m.supplier_id = s.supplier_id
                WHERE m.brand_name ILIKE %s OR m.generic_name ILIKE %s
            """, (f"%{target_name}%", f"%{target_name}%"))
            
            r = cur.fetchone()
            
            if r:
                # 1. Define the data rows
                rows = [
                    ("💊 Brand Name", r['brand_name']),
                    ("🔬 Generic", r['generic_name']),
                    ("💪 Strength", r['strength'] or "N/A"),
                    ("💊 Form", r['form'] or "Tablet"),
                    ("💰 MRP", fmt(r['mrp'])),
                    ("📦 Stock", f"{r['quantity']} units"),
                    ("📍 Location", r['location'] or "General Rack"),
                    ("🚚 Supplier", r['supplier_name'] or "Unknown"),
                    ("📅 Expiry", str(r['expiry_date']))
                ]
                
                # 2. Build the HTML Table
                # Styles: standard simple table with borders
                table_html = """
                <br>
                <table style="width:100%; border-collapse: collapse; border: 1px solid #ddd; font-family: sans-serif; font-size: 14px;">
                    <tbody>
                """
                
                for label, value in rows:
                    table_html += f"""
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 8px; background-color: #f9f9f9; font-weight: bold; width: 40%;">{label}</td>
                        <td style="padding: 8px;">{value}</td>
                    </tr>
                    """
                
                table_html += "</tbody></table>"
                
                return f"📋 Here are the full details for <b>{target_name}</b>:{table_html}"
            
            return f"❌ I couldn't find detailed records for '{target_name}'."
        # --- CUSTOMER ---
        if intent == "CUSTOMER_INFO":
            cur.execute("SELECT loyalty_points, phone FROM customers WHERE name ILIKE %s", (f"%{target_name}%",))
            r = cur.fetchone()
            if r: return generate_response("customer_info", person=target_name, qty=r['loyalty_points'], phone=r['phone'])
            return f"❌ Customer '{target_name}' not found."
        # --- [NEW] FIND SUBSTITUTES ---
        if intent == "FIND_SUBSTITUTE":
            if not target_name: return "❓ Which medicine do you need a substitute for?"
            
            # 1. Find the generic name of the requested medicine
            cur.execute("SELECT generic_name FROM medicines WHERE brand_name ILIKE %s LIMIT 1", (f"%{target_name}%",))
            r = cur.fetchone()
            
            if not r or not r['generic_name']:
                return f"❌ I couldn't find the generic composition for '{target_name}'."
            
            generic = r['generic_name']
            
            # 2. Find OTHER medicines with the same generic name
            cur.execute("""
                SELECT brand_name, strength, mrp, quantity 
                FROM medicines 
                WHERE generic_name = %s AND brand_name NOT ILIKE %s
                ORDER BY quantity DESC 
                LIMIT 5
            """, (generic, f"%{target_name}%"))
            
            rows = cur.fetchall()
            
            if rows:
                msg = f"🔄 <b>Substitutes for {target_name} ({generic}):</b><br>"
                for row in rows:
                    stock_status = "✅ In Stock" if row['quantity'] > 0 else "❌ Out of Stock"
                    msg += f"• <b>{row['brand_name']}</b> ({row['strength']}) - {fmt(row['mrp'])} [{stock_status}]<br>"
                return msg
            else:
                return f"⚠️ No other brands found with generic: {generic}."

        # --- [NEW] SUPPLIER CATALOG ---
        if intent == "SUPPLIER_ITEMS":
            if not target_name: return "❓ Which supplier's products are you looking for?"
            
            # Find medicines linked to this supplier
            cur.execute("""
                SELECT m.brand_name, m.quantity 
                FROM medicines m
                JOIN suppliers s ON m.supplier_id = s.supplier_id
                WHERE s.name ILIKE %s
                LIMIT 10
            """, (f"%{target_name}%",))
            
            rows = cur.fetchall()
            
            if rows:
                items = [f"{r['brand_name']} (Qty: {r['quantity']})" for r in rows]
                return f"📦 <b>Products from {target_name}:</b><br>" + "<br>".join(items)
            
            return f"❌ No products found linked to supplier '{target_name}'."
        if intent == "SHOW_ANALYSIS":
            # Sub-intent: Check if user wants "Sales" or "Stock"
            is_sales = any(w in text.lower() for w in ["sales", "revenue", "trend", "income"])
            is_stock = any(w in text.lower() for w in ["stock", "inventory", "medicine", "item"])
            
            # DEFAULT: If vague (e.g., "Show me a graph"), default to Sales
            if not is_stock: 
                is_sales = True

            # --- GRAPH 1: SALES TREND (Last 7 Days) ---
            if is_sales:
                cur.execute("""
                    SELECT DATE(created_at) as sale_date, SUM(total_amount) as total 
                    FROM sales 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY DATE(created_at) 
                    ORDER BY sale_date ASC
                """)
                rows = cur.fetchall()
                
                if not rows: return "📉 No sales data found for the last 7 days."

                # logic to calculate bar widths
                max_val = max([r['total'] for r in rows])
                
                html_graph = "<br><b>📊 Sales Trend (Last 7 Days)</b><br><div style='width:100%; font-family: sans-serif; font-size: 12px;'>"
                
                for r in rows:
                    val = r['total']
                    date_str = r['sale_date'].strftime('%d %b')
                    width_percent = int((val / max_val) * 100)
                    
                    # Each bar is a colored div
                    html_graph += f"""
                    <div style="margin-bottom: 8px;">
                        <div style="margin-bottom: 2px;">{date_str}: <b>{fmt(val)}</b></div>
                        <div style="width: {width_percent}%; background-color: #4CAF50; height: 12px; border-radius: 4px;"></div>
                    </div>
                    """
                html_graph += "</div>"
                return html_graph

            # --- GRAPH 2: TOP STOCK LEVELS ---
            elif is_stock:
                cur.execute("""
                    SELECT brand_name, quantity 
                    FROM medicines 
                    ORDER BY quantity DESC 
                    LIMIT 5
                """)
                rows = cur.fetchall()
                
                if not rows: return "📉 No stock data available."

                max_qty = max([r['quantity'] for r in rows])
                
                html_graph = "<br><b>📊 Top 5 Stock Items</b><br><div style='width:100%; font-family: sans-serif; font-size: 12px;'>"
                
                for r in rows:
                    qty = r['quantity']
                    name = r['brand_name']
                    width_percent = int((qty / max_qty) * 100)
                    
                    # Color warning: Red if low, Blue if healthy
                    color = "#2196F3" if qty > 20 else "#FF9800"
                    
                    html_graph += f"""
                    <div style="margin-bottom: 8px;">
                        <div style="margin-bottom: 2px;">{name}: <b>{qty} units</b></div>
                        <div style="width: {width_percent}%; background-color: {color}; height: 12px; border-radius: 4px;"></div>
                    </div>
                    """
                html_graph += "</div>"
                return html_graph
        # --- [NEW] TOTAL INVENTORY VALUE ---
        if intent == "INVENTORY_VALUE":
            cur.execute("SELECT SUM(quantity * mrp) as total_val FROM medicines")
            r = cur.fetchone()
            val = r['total_val'] if r else 0
            return f"💰 <b>Total Inventory Value:</b> {fmt(val)}"
        # --- EXPIRY ---
        if intent == "CHECK_EXPIRY":
            if target_name:
                cur.execute("SELECT expiry_date FROM medicines WHERE brand_name ILIKE %s", (f"%{target_name}%",))
                r = cur.fetchone()
                if r: return generate_response("expiry_alert", med=target_name, date=r['expiry_date'])
                return f"❌ '{target_name}' not found."
            else:
                cur.execute("SELECT brand_name FROM medicines WHERE expiry_date < CURRENT_DATE + INTERVAL '60 days'")
                rows = cur.fetchall()
                if rows: return "⚠️ Expiring soon:\n" + "\n".join([r['brand_name'] for r in rows])
                return "✅ No medicines expiring soon."

    except Exception as e:
        print(f"Logic Error: {e}")
        return "⚠️ System Error."
    finally:
        if conn: conn.close()
    
    return "🤖 I'm listening."