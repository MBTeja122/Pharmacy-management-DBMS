from flask import Blueprint, render_template, session, redirect, url_for
from db_config import get_db_connection
import pandas as pd
import numpy as np
import json
import plotly
import plotly.express as px
from psycopg2.extras import RealDictCursor
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import NearestNeighbors
from datetime import date
# Import the helper we just fixed
from routes.notification_routes import create_notification 

dash_bp1 = Blueprint('dash_bp1', __name__, url_prefix='/admin')

@dash_bp1.route("/analytics")
def analytics_hub():
    if session.get("role") != "Admin":
        return redirect(url_for("dash.load"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Defaults
    kpis = {'low_stock':0, 'expiring':0, 'today_revenue':0, 'total_customers':0}
    trend_msg = "Gathering data..."
    
    # Graphs
    graph_trend = "{}"
    graph_profit = "{}"
    graph_cat = "{}" 
    graph_hour = "{}"
    
    # Data Lists
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
        # If revenue crosses a target (e.g., 10,000), cheer the team!
        if float(kpis['today_revenue']) > 10000:
            create_notification(
                f"🏆 Great job! Daily revenue crossed ₹{kpis['today_revenue']}.", 
                "success", 
                "/admin/analytics"
            )

        # ==========================================
        # 🧠 INSIGHT 1: DEMAND FORECAST
        # ==========================================
        cur.execute("""
            SELECT TO_CHAR(created_at, 'YYYY-MM-DD') as date, 
                   CAST(SUM(total_amount) AS FLOAT) as revenue 
            FROM sales
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY date ORDER BY date ASC
        """)
        data_trend = cur.fetchall()
        df_trend = pd.DataFrame(data_trend) if data_trend else pd.DataFrame(columns=['date', 'revenue'])

        if len(df_trend) > 4:
            df_trend['day_num'] = range(len(df_trend))
            X = df_trend[['day_num']]
            y = df_trend['revenue']
            model = LinearRegression()
            model.fit(X, y)
            future_days = pd.DataFrame({'day_num': range(len(df_trend), len(df_trend) + 7)})
            prediction = max(0, model.predict(future_days).sum())
            trend_msg = f"Predicted revenue for next week: <b>₹{prediction:,.0f}</b>"
            
            fig_trend = px.line(df_trend, x='date', y='revenue', markers=True, template="plotly_white")
            fig_trend.update_traces(line_color='#6200EA', line_width=3)
            fig_trend.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(visible=False), yaxis=dict(visible=False), height=120
            )
            graph_trend = json.dumps(fig_trend, cls=plotly.utils.PlotlyJSONEncoder)

        # ==========================================
        # 🧠 INSIGHT 2: SMART REORDER + 🔔 NOTIFICATION 2 (Low Stock)
        # ==========================================
        cur.execute("""
            SELECT m.brand_name, m.quantity, SUM(si.quantity) as sold_30
            FROM sale_items si
            JOIN medicines m ON si.medicine_id = m.medicine_id
            JOIN sales s ON si.sale_id = s.sale_id
            WHERE s.created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY m.brand_name, m.quantity
            HAVING SUM(si.quantity) > 0
        """)
        velocity = cur.fetchall()

        for v in velocity:
            sold_30 = float(v.get('sold_30') or 0)
            current_qty = float(v.get('quantity') or 0)
            daily_rate = sold_30 / 30
            reorder_point = (daily_rate * 3) * 1.5 
            if current_qty < reorder_point:
                days_left = current_qty / daily_rate if daily_rate > 0 else 99
                
                # 🔔 Trigger Alert for very urgent items
                if days_left < 2: 
                    create_notification(
                        f"⚠️ Urgent: {v['brand_name']} will run out in {int(days_left)} days!", 
                        "warning", 
                        "/medicines"
                    )

                reorder_alerts.append({"name": v['brand_name'], "stock": int(current_qty), "days": int(days_left)})
        reorder_alerts = sorted(reorder_alerts, key=lambda x: x['days'])[:4]

        # ==========================================
        # 🧠 INSIGHT 3: DEAD STOCK + 🔔 NOTIFICATION 3 (Cash Stuck)
        # ==========================================
        cur.execute("""
            SELECT m.brand_name, m.quantity, (m.quantity * m.cost_price) as locked_cash
            FROM medicines m
            WHERE m.quantity > 0 
            AND m.medicine_id NOT IN (
                SELECT DISTINCT si.medicine_id FROM sale_items si
                JOIN sales s ON si.sale_id = s.sale_id
                WHERE s.created_at >= CURRENT_DATE - INTERVAL '90 days'
            )
            ORDER BY locked_cash DESC LIMIT 5
        """)
        dead_stock_raw = cur.fetchall()
        if dead_stock_raw:
            top_dead = dead_stock_raw[0] # Pick the biggest loser
            # 🔔 Trigger Alert
            create_notification(
                f"💀 Dead Stock: {top_dead['brand_name']} unsold >90 days. ₹{top_dead['locked_cash']} stuck!", 
                "info", 
                "/medicines"
            )

        for d in dead_stock_raw:
            dead_stock_list.append({"name": d['brand_name'], "qty": d['quantity'], "cash": int(d['locked_cash'])})

        # ==========================================
        # 🧠 INSIGHT 4: EXPIRY RISK + 🔔 NOTIFICATION 4 (Expiry)
        # ==========================================
        cur.execute("""
            SELECT m.brand_name, m.quantity, m.cost_price, m.expiry_date, SUM(si.quantity) as sold_30
            FROM medicines m
            LEFT JOIN sale_items si ON m.medicine_id = si.medicine_id
            LEFT JOIN sales s ON si.sale_id = s.sale_id AND s.created_at >= CURRENT_DATE - INTERVAL '30 days'
            WHERE m.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
            GROUP BY m.medicine_id
        """)
        expiry_data = cur.fetchall()
        for ex in expiry_data:
            sold_30 = float(ex.get('sold_30') or 0)
            current_qty = float(ex.get('quantity') or 0)
            cost_price = float(ex.get('cost_price') or 0)
            daily_rate = sold_30 / 30
            days_to_exp = (ex['expiry_date'] - date.today()).days if ex['expiry_date'] else 0
            likely_sales = daily_rate * days_to_exp
            unsalable = max(0, current_qty - likely_sales)
            if unsalable > 0:
                loss = unsalable * cost_price
                predicted_loss += loss
                if loss > 500:
                    risky_items.append(f"{ex['brand_name']} (-₹{loss:.0f})")
                    # 🔔 Trigger Alert (High Priority)
                    create_notification(
                        f"🚨 Expiry Risk: {ex['brand_name']} expiring soon! Potential Loss: ₹{loss:.0f}", 
                        "danger", 
                        "/medicines"
                    )

        # ==========================================
        # 🔔 NOTIFICATION 5: PATIENT REFILL REMINDER (New!)
        # ==========================================
        # Find customers who bought 30 days ago and might need a refill
        cur.execute("""
            SELECT c.name, s.sale_id
            FROM sales s
            JOIN customers c ON s.customer_id = c.customer_id
            WHERE s.created_at::DATE = CURRENT_DATE - INTERVAL '30 days'
            LIMIT 1
        """)
        refill_cust = cur.fetchone()
        if refill_cust:
            create_notification(
                f"🔄 Refill Due: {refill_cust['name']} bought meds 30 days ago. Call them?", 
                "info", 
                "/customers"
            )

        # ==========================================
        # 🧠 INSIGHT 5: KNN SMART BUNDLES
        # ==========================================
        cur.execute("""
            SELECT s.sale_id, m.brand_name
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.sale_id
            JOIN medicines m ON si.medicine_id = m.medicine_id
            WHERE s.created_at >= CURRENT_DATE - INTERVAL '60 days' 
        """)
        raw_txns = cur.fetchall()

        if len(raw_txns) > 1:
            df_sales = pd.DataFrame(raw_txns)
            try:
                basket = df_sales.groupby(['sale_id', 'brand_name'])['brand_name'].count().unstack().reset_index().fillna(0).set_index('sale_id')
                basket_sets = basket.map(lambda x: 1 if x >= 1 else 0) 
                med_matrix = basket_sets.T 
                if len(med_matrix) > 2:
                    knn = NearestNeighbors(metric='cosine', algorithm='brute')
                    knn.fit(med_matrix)
                    targets = med_matrix.index[:3]
                    for target in targets:
                        distances, indices = knn.kneighbors(med_matrix.loc[target].values.reshape(1, -1), n_neighbors=2)
                        if len(distances.flatten()) > 1:
                            neighbor_idx = indices.flatten()[1]
                            score = 1 - distances.flatten()[1]
                            if score > 0.25:
                                partner = med_matrix.index[neighbor_idx]
                                bundle_suggestions.append({"item": target, "partner": partner, "score": int(score*100)})
            except Exception as e:
                print(f"KNN Error: {e}")

        # ==========================================
        # 📊 GRAPHS (Standard Logic)
        # ==========================================
        cur.execute("""
            SELECT TO_CHAR(s.created_at, 'YYYY-MM-DD') as date, 
                   CAST(SUM(s.total_amount) AS FLOAT) as revenue,
                   CAST(SUM(s.total_amount - (si.quantity * COALESCE(m.cost_price, 0))) AS FLOAT) as profit
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            LEFT JOIN medicines m ON si.medicine_id = m.medicine_id
            WHERE s.created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY date ORDER BY date ASC
        """)
        df_profit = pd.DataFrame(cur.fetchall())
        if not df_profit.empty:
            fig_p = px.line(df_profit, x='date', y=['revenue', 'profit'], markers=True, template="plotly_white", height=350)
            fig_p.update_layout(title="Financial Health", margin=dict(l=20,r=20,t=40,b=20), yaxis=dict(rangemode='tozero'))
            graph_profit = json.dumps(fig_p, cls=plotly.utils.PlotlyJSONEncoder)

        cur.execute("""
            SELECT m.health_condition, CAST(SUM(si.quantity) AS FLOAT) as sold
            FROM sale_items si JOIN medicines m ON si.medicine_id = m.medicine_id
            WHERE m.health_condition IS NOT NULL
            GROUP BY m.health_condition ORDER BY sold DESC LIMIT 5
        """)
        df_cat = pd.DataFrame(cur.fetchall())
        graph_cat = "{}"
        if not df_cat.empty:
            fig_c = px.pie(df_cat, values='sold', names='health_condition', hole=0.5, template="plotly_white", height=300)
            fig_c.update_layout(margin=dict(l=20,r=20,t=40,b=20), showlegend=False, title="Top Categories")
            graph_cat = json.dumps(fig_c, cls=plotly.utils.PlotlyJSONEncoder)

        cur.execute("""
            SELECT EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as txns
            FROM sales GROUP BY hour ORDER BY hour ASC
        """)
        df_hour = pd.DataFrame(cur.fetchall())
        graph_hour = "{}"
        if not df_hour.empty:
            fig_h = px.bar(df_hour, x='hour', y='txns', template="plotly_white", height=300)
            fig_h.update_traces(marker_color='#FFAB00')
            fig_h.update_layout(margin=dict(l=20,r=20,t=40,b=20), title="Peak Hours")
            graph_hour = json.dumps(fig_h, cls=plotly.utils.PlotlyJSONEncoder)

    except Exception as e:
        print(f"Analytics Error: {e}")

    finally:
        cur.close()
        conn.close()
    
    return render_template("analytics.html", 
                           kpis=kpis, 
                           graph_trend=graph_trend, trend_text=trend_msg,
                           reorder_alerts=reorder_alerts,
                           predicted_loss=predicted_loss, risky_items=risky_items,
                           dead_stock_list=dead_stock_list, 
                           bundle_suggestions=bundle_suggestions, 
                           graph_profit=graph_profit, 
                           graph_cat=graph_cat, 
                           graph_hour=graph_hour)