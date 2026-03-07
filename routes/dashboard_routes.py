from flask import Blueprint, render_template, session, redirect, url_for
from db_config import get_db_connection
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
from psycopg2.extras import RealDictCursor
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import NearestNeighbors
from datetime import date
from routes.notification_routes import create_notification 

dash_bp1 = Blueprint('dash_bp1', __name__, url_prefix='/admin')

@dash_bp1.route("/analytics")
def analytics_hub():
    if session.get("role") != "Admin":
        return redirect(url_for("dash.load"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    kpis = {'low_stock':0, 'expiring':0, 'today_revenue':0, 'total_customers':0}
    trend_msg = "Gathering data..."
    
    # Graphs
    graph_revenue = "{}"
    graph_profit = "{}"
    graph_top = "{}"
    graph_hour = "{}"
    
    reorder_alerts = []
    predicted_loss = 0
    risky_items = []
    dead_stock_list = []
    bundle_suggestions = [] 
    
    try:
        # --- 1. BASIC KPIs ---
        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM medicines WHERE quantity < 20) as low_stock,
                (SELECT COUNT(*) FROM medicines WHERE expiry_date < CURRENT_DATE + INTERVAL '60 days') as expiring,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE created_at::DATE = CURRENT_DATE) as today_revenue,
                (SELECT COUNT(*) FROM customers) as total_customers
        """)
        row = cur.fetchone()
        if row: kpis = row

        # 🔔 NOTIFICATION 1: REVENUE MILESTONE
        # FIXED: related_id is None (The system knows 'milestone' goes to analytics)
        if float(kpis['today_revenue']) > 10000:
            create_notification(
                f"🏆 Great job! Daily revenue crossed ₹{kpis['today_revenue']}.", 
                "milestone", 
                related_id=None 
            )

        # ==========================================
        # 📊 1. REVENUE CHART (Full 30-Day Timeline)
        # ==========================================
        cur.execute("""
            SELECT created_at::DATE as date, 
                   COALESCE(SUM(total_amount), 0) as revenue
            FROM sales 
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days' 
            GROUP BY date 
            ORDER BY date ASC
        """)
        rev_rows = cur.fetchall()
        
        # Create a full 30-day date range in Python
        all_dates = pd.date_range(end=date.today(), periods=30).normalize()
        df_full = pd.DataFrame({'date': all_dates})
        
        if rev_rows:
            df_db = pd.DataFrame(rev_rows)
            df_db['date'] = pd.to_datetime(df_db['date'])
            # Merge database results into the full calendar (fill missing days with 0)
            df_merged = pd.merge(df_full, df_db, on='date', how='left').fillna(0)
        else:
            df_merged = df_full
            df_merged['revenue'] = 0.0

        # Plot
        fig_r = go.Figure()
        fig_r.add_trace(go.Scatter(
            x=df_merged['date'], 
            y=df_merged['revenue'],
            mode='lines',
            fill='tozeroy',
            line=dict(color='#00C853', width=3),
            fillcolor="rgba(0, 200, 83, 0.1)",
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Revenue:</b> ₹%{y}<extra></extra>"
        ))
        fig_r.update_layout(title="Daily Revenue Trend", margin=dict(l=20,r=20,t=40,b=20), yaxis_title="Amount (₹)")
        graph_revenue = json.dumps(fig_r, cls=plotly.utils.PlotlyJSONEncoder)

        # ==========================================
        # 📊 2. PROFIT CHART (Full 30-Day Timeline)
        # ==========================================
        cur.execute("""
            SELECT s.created_at::DATE as date, 
                   COALESCE(SUM((si.quantity * si.unit_price) - (si.quantity * COALESCE(m.cost_price, 0))), 0) as profit
            FROM sales s 
            JOIN sale_items si ON s.sale_id = si.sale_id 
            LEFT JOIN medicines m ON si.medicine_id = m.medicine_id
            WHERE s.created_at >= CURRENT_DATE - INTERVAL '30 days' 
            GROUP BY date 
            ORDER BY date ASC
        """)
        prof_rows = cur.fetchall()
        
        if prof_rows:
            df_db_p = pd.DataFrame(prof_rows)
            df_db_p['date'] = pd.to_datetime(df_db_p['date'])
            df_merged_p = pd.merge(df_full, df_db_p, on='date', how='left').fillna(0)
        else:
            df_merged_p = df_full
            df_merged_p['profit'] = 0.0
            
        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(
            x=df_merged_p['date'], 
            y=df_merged_p['profit'],
            mode='lines',
            fill='tozeroy',
            line=dict(color='#6200EA', width=3),
            fillcolor="rgba(98, 0, 234, 0.1)",
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Net Profit:</b> ₹%{y}<extra></extra>"
        ))
        fig_p.update_layout(title="Net Profit Trend", margin=dict(l=20,r=20,t=40,b=20), yaxis_title="Amount (₹)")
        graph_profit = json.dumps(fig_p, cls=plotly.utils.PlotlyJSONEncoder)

        # ==========================================
        # 📊 3. TRAFFIC (Bar Chart)
        # ==========================================
        cur.execute("""
            SELECT EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as txns
            FROM sales GROUP BY hour ORDER BY hour ASC
        """)
        df_hour = pd.DataFrame(cur.fetchall())
        if not df_hour.empty:
            fig_h = px.bar(df_hour, x='hour', y='txns', template="plotly_white", height=350)
            fig_h.update_traces(marker_color='#FFAB00', hovertemplate="<b>Time:</b> %{x}:00<br><b>Transactions:</b> %{y}")
            fig_h.update_layout(title="Peak Hours (Traffic)", margin=dict(l=20,r=20,t=40,b=20), 
                                xaxis=dict(tickmode='linear', dtick=2, title="Hour of Day"), yaxis_title="Sales Count")
            graph_hour = json.dumps(fig_h, cls=plotly.utils.PlotlyJSONEncoder)

        # ==========================================
        # 📊 4. TOP ITEMS (Bar Chart)
        # ==========================================
        cur.execute("""
            SELECT m.brand_name, CAST(SUM(si.quantity * si.unit_price) AS FLOAT) as total_revenue
            FROM sale_items si JOIN medicines m ON si.medicine_id = m.medicine_id JOIN sales s ON si.sale_id = s.sale_id
            WHERE s.created_at >= CURRENT_DATE - INTERVAL '30 days' GROUP BY m.brand_name ORDER BY total_revenue DESC LIMIT 7
        """)
        df_top = pd.DataFrame(cur.fetchall())
        if not df_top.empty:
            fig_t = px.bar(df_top, x='total_revenue', y='brand_name', orientation='h', template="plotly_white", height=350)
            fig_t.update_traces(marker_color='#2962FF', hovertemplate="<b>Item:</b> %{y}<br><b>Revenue:</b> ₹%{x:.2f}")
            fig_t.update_layout(title="Top 7 Revenue Generators", margin=dict(l=20,r=20,t=40,b=20), 
                                yaxis=dict(autorange="reversed", title=None), xaxis=dict(title="Revenue (₹)"))
            graph_top = json.dumps(fig_t, cls=plotly.utils.PlotlyJSONEncoder)

        # ==========================================
        # 🧠 INSIGHTS (Forecast & Dead Stock)
        # ==========================================
        
        # 1. Demand Forecast
        cur.execute("""
            SELECT created_at::DATE as date, CAST(SUM(total_amount) AS FLOAT) as revenue 
            FROM sales WHERE created_at >= CURRENT_DATE - INTERVAL '30 days' 
            GROUP BY date ORDER BY date ASC
        """)
        data_trend = cur.fetchall()
        df_trend = pd.DataFrame(data_trend) if data_trend else pd.DataFrame(columns=['date', 'revenue'])

        if len(df_trend) >= 2:
            df_trend['day_num'] = range(len(df_trend))
            model = LinearRegression()
            model.fit(df_trend[['day_num']], df_trend['revenue'])
            future_days = pd.DataFrame({'day_num': range(len(df_trend), len(df_trend) + 7)})
            prediction = max(0, model.predict(future_days).sum())
            trend_msg = f"Predicted revenue for next week: <b>₹{prediction:,.0f}</b>"
        elif len(df_trend) == 1:
             trend_msg = "Need 1 more day of data to forecast."

        # 2. Smart Reorder + Notification
        cur.execute("""
            SELECT m.brand_name, m.quantity, SUM(si.quantity) as sold_30
            FROM sale_items si JOIN medicines m ON si.medicine_id = m.medicine_id JOIN sales s ON si.sale_id = s.sale_id
            WHERE s.created_at >= CURRENT_DATE - INTERVAL '30 days' GROUP BY m.brand_name, m.quantity HAVING SUM(si.quantity) > 0
        """)
        velocity = cur.fetchall()
        for v in velocity:
            sold_30 = float(v.get('sold_30') or 0); current_qty = float(v.get('quantity') or 0)
            daily_rate = sold_30 / 30; reorder_point = (daily_rate * 3) * 1.5 
            if current_qty < reorder_point:
                days_left = current_qty / daily_rate if daily_rate > 0 else 99
                
                # 🔔 NOTIFICATION 2: URGENT STOCK
                # FIXED: Type='low_stock' so it links to medicines. related_id=None.
                if days_left < 2: 
                    create_notification(
                        f"⚠️ Urgent: {v['brand_name']} will run out in {int(days_left)} days!", 
                        "low_stock", 
                        related_id=None 
                    )
                
                reorder_alerts.append({"name": v['brand_name'], "stock": int(current_qty), "days": int(days_left)})
        reorder_alerts = sorted(reorder_alerts, key=lambda x: x['days'])[:4]

        # 3. DEAD STOCK (Fixed Logic + Notification)
        cur.execute("""
            SELECT m.brand_name, m.quantity, (m.quantity * m.cost_price) as locked_cash
            FROM medicines m 
            WHERE m.quantity > 0 
            AND m.medicine_id NOT IN (
                SELECT DISTINCT si.medicine_id FROM sale_items si JOIN sales s ON si.sale_id = s.sale_id
                WHERE s.created_at >= CURRENT_DATE - INTERVAL '90 days'
            ) 
            AND m.created_at <= CURRENT_DATE - INTERVAL '90 days'
            ORDER BY locked_cash DESC LIMIT 5
        """)
        dead_stock_raw = cur.fetchall()
        
        if dead_stock_raw:
            top_dead = dead_stock_raw[0] 
            # 🔔 NOTIFICATION 3: DEAD STOCK
            # FIXED: Type='stock', related_id=None
            create_notification(
                f"💀 Dead Stock: {top_dead['brand_name']} unsold >90 days. ₹{top_dead['locked_cash']} stuck!", 
                "stock", 
                related_id=None 
            )

        for d in dead_stock_raw:
            dead_stock_list.append({"name": d['brand_name'], "qty": d['quantity'], "cash": int(d['locked_cash'])})

        # 4. Expiry Risk + Notification
        cur.execute("""
            SELECT m.brand_name, m.quantity, m.cost_price, m.expiry_date, SUM(si.quantity) as sold_30
            FROM medicines m LEFT JOIN sale_items si ON m.medicine_id = si.medicine_id
            LEFT JOIN sales s ON si.sale_id = s.sale_id AND s.created_at >= CURRENT_DATE - INTERVAL '30 days'
            WHERE m.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days' GROUP BY m.medicine_id
        """)
        expiry_data = cur.fetchall()
        for ex in expiry_data:
            sold_30 = float(ex.get('sold_30') or 0); current_qty = float(ex.get('quantity') or 0); cost_price = float(ex.get('cost_price') or 0)
            daily_rate = sold_30 / 30; days_to_exp = (ex['expiry_date'] - date.today()).days if ex['expiry_date'] else 0
            likely_sales = daily_rate * days_to_exp; unsalable = max(0, current_qty - likely_sales)
            if unsalable > 0:
                loss = unsalable * cost_price; predicted_loss += loss
                if loss > 500:
                    risky_items.append(f"{ex['brand_name']} (-₹{loss:.0f})")
                    # 🔔 NOTIFICATION 4: EXPIRY RISK
                    # FIXED: Type='expiry', related_id=None
                    create_notification(
                        f"🚨 Expiry Risk: {ex['brand_name']} expiring soon! Potential Loss: ₹{loss:.0f}", 
                        "expiry", 
                        related_id=None 
                    )

        # 5. Bundles
        cur.execute("""
            SELECT s.sale_id, m.brand_name FROM sale_items si JOIN sales s ON si.sale_id = s.sale_id
            JOIN medicines m ON si.medicine_id = m.medicine_id WHERE s.created_at >= CURRENT_DATE - INTERVAL '60 days' 
        """)
        raw_txns = cur.fetchall()
        if len(raw_txns) > 1:
            df_sales = pd.DataFrame(raw_txns)
            try:
                basket = df_sales.groupby(['sale_id', 'brand_name'])['brand_name'].count().unstack().reset_index().fillna(0).set_index('sale_id')
                basket_sets = basket.map(lambda x: 1 if x >= 1 else 0) 
                med_matrix = basket_sets.T 
                if len(med_matrix) > 2:
                    knn = NearestNeighbors(metric='cosine', algorithm='brute'); knn.fit(med_matrix)
                    targets = med_matrix.index[:3]
                    for target in targets:
                        distances, indices = knn.kneighbors(med_matrix.loc[target].values.reshape(1, -1), n_neighbors=2)
                        if len(distances.flatten()) > 1:
                            neighbor_idx = indices.flatten()[1]; score = 1 - distances.flatten()[1]
                            if score > 0.25:
                                partner = med_matrix.index[neighbor_idx]
                                bundle_suggestions.append({"item": target, "partner": partner, "score": int(score*100)})
            except: pass

        # 🔔 NOTIFICATION 5: PATIENT REFILL REMINDER
        cur.execute("""
            SELECT c.name, s.sale_id
            FROM sales s
            JOIN customers c ON s.customer_id = c.customer_id
            WHERE s.created_at::DATE = CURRENT_DATE - INTERVAL '30 days'
            LIMIT 1
        """)
        refill_cust = cur.fetchone()
        if refill_cust:
            # FIXED: Pass sale_id (Integer) if you want, or None. 
            # I used sale_id here because it's available and might be useful for future linking.
            create_notification(
                f"🔄 Refill Due: {refill_cust['name']} bought meds 30 days ago. Call them?", 
                "info", 
                related_id=refill_cust['sale_id'] 
            )

    except Exception as e:
        print(f"Analytics Error: {e}")
    finally:
        cur.close(); conn.close()
    
    return render_template("analytics.html", 
                           kpis=kpis, 
                           graph_revenue=graph_revenue, 
                           graph_profit=graph_profit,   
                           graph_top=graph_top,         
                           graph_hour=graph_hour,       
                           trend_text=trend_msg,
                           reorder_alerts=reorder_alerts, predicted_loss=predicted_loss, risky_items=risky_items,
                           dead_stock_list=dead_stock_list, bundle_suggestions=bundle_suggestions)