-- PostgreSQL initialization script for Pharmacy-management-DBMS
-- Usage:
--   psql -h <host> -U <user> -d <database> -f db/init_schema.sql

BEGIN;

CREATE TABLE IF NOT EXISTS pharmacists (
    pharmacist_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone NUMERIC,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'Staff',
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15),
    email VARCHAR(120),
    address TEXT,
    loyalty_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    phone NUMERIC,
    email VARCHAR(120),
    address TEXT,
    gst_no VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS medicines (
    medicine_id SERIAL PRIMARY KEY,
    generic_name VARCHAR(100) NOT NULL,
    brand_name VARCHAR(100),
    form VARCHAR(50),
    strength VARCHAR(50),
    primary_ingredient VARCHAR(100),
    description TEXT,
    health_condition VARCHAR(100),
    is_otc BOOLEAN DEFAULT false,
    batch_no VARCHAR(50) NOT NULL,
    mfg_date DATE,
    expiry_date DATE,
    quantity INTEGER DEFAULT 0,
    cost_price NUMERIC,
    mrp NUMERIC,
    supplier_id INTEGER,
    reorder_level INTEGER DEFAULT 10,
    low_stock_threshold INTEGER DEFAULT 5,
    location VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_medicines_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers (supplier_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sales (
    sale_id SERIAL PRIMARY KEY,
    invoice_no VARCHAR(20),
    pharmacist_id INTEGER,
    customer_id INTEGER,
    total_amount NUMERIC,
    discount NUMERIC DEFAULT 0,
    tax NUMERIC DEFAULT 0,
    payment_method VARCHAR(50),
    loyalty_points_earned INTEGER DEFAULT 0,
    loyalty_points_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sales_pharmacist
        FOREIGN KEY (pharmacist_id)
        REFERENCES pharmacists (pharmacist_id)
        ON DELETE SET NULL,
    CONSTRAINT fk_sales_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers (customer_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS purchases (
    purchase_id SERIAL PRIMARY KEY,
    supplier_id INTEGER,
    pharmacist_id INTEGER,
    total_amount NUMERIC,
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_purchases_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers (supplier_id)
        ON DELETE SET NULL,
    CONSTRAINT fk_purchases_pharmacist
        FOREIGN KEY (pharmacist_id)
        REFERENCES pharmacists (pharmacist_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sale_items (
    sale_item_id SERIAL PRIMARY KEY,
    sale_id INTEGER,
    medicine_id INTEGER,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC,
    CONSTRAINT fk_sale_items_sale
        FOREIGN KEY (sale_id)
        REFERENCES sales (sale_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_sale_items_medicine
        FOREIGN KEY (medicine_id)
        REFERENCES medicines (medicine_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS purchase_items (
    purchase_item_id SERIAL PRIMARY KEY,
    purchase_id INTEGER,
    medicine_id INTEGER,
    batch_no VARCHAR(50),
    expiry_date DATE,
    quantity INTEGER,
    unit_cost NUMERIC,
    CONSTRAINT fk_purchase_items_purchase
        FOREIGN KEY (purchase_id)
        REFERENCES purchases (purchase_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_purchase_items_medicine
        FOREIGN KEY (medicine_id)
        REFERENCES medicines (medicine_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    type VARCHAR(20) DEFAULT 'info',
    link VARCHAR(200),
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'Unread',
    related_id INTEGER,
    pharmacist_id INTEGER,
    CONSTRAINT fk_notifications_pharmacist
        FOREIGN KEY (pharmacist_id)
        REFERENCES pharmacists (pharmacist_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS bot_sessions (
    session_id SERIAL PRIMARY KEY,
    user_identifier VARCHAR(100) NOT NULL UNIQUE,
    context_data JSONB DEFAULT '{}'::jsonb,
    message_count INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bot_logs (
    log_id SERIAL PRIMARY KEY,
    session_id INTEGER,
    user_identifier VARCHAR(100) NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    detected_intent VARCHAR(50),
    confidence_score DOUBLE PRECISION,
    execution_time_ms INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bot_logs_session
        FOREIGN KEY (session_id)
        REFERENCES bot_sessions (session_id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_medicines_brand_name ON medicines (brand_name);
CREATE INDEX IF NOT EXISTS idx_medicines_generic_name ON medicines (generic_name);
CREATE INDEX IF NOT EXISTS idx_medicines_expiry_date ON medicines (expiry_date);
CREATE INDEX IF NOT EXISTS idx_sales_created_at ON sales (created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications (is_read);
CREATE INDEX IF NOT EXISTS idx_bot_logs_user_identifier ON bot_logs (user_identifier);

COMMIT;
