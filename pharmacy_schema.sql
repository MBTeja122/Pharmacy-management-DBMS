-- Schema extraction for database: Pharmacy

CREATE TABLE pharmacists (
    pharmacist_id integer NOT NULL DEFAULT nextval('pharmacists_pharmacist_id_seq'::regclass),
    name character varying(100) NOT NULL,
    email character varying(120) NOT NULL,
    phone numeric,
    password_hash character varying(255) NOT NULL,
    role character varying(20) DEFAULT 'Staff'::character varying,
    active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (pharmacist_id)
);

CREATE TABLE customers (
    customer_id integer NOT NULL DEFAULT nextval('customers_customer_id_seq'::regclass),
    name character varying(100) NOT NULL,
    phone character varying(15),
    email character varying(120),
    address text,
    loyalty_points integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customer_id)
);

CREATE TABLE sales (
    sale_id integer NOT NULL DEFAULT nextval('sales_sale_id_seq'::regclass),
    invoice_no character varying(20),
    pharmacist_id integer,
    customer_id integer,
    total_amount numeric,
    discount numeric DEFAULT 0,
    tax numeric DEFAULT 0,
    payment_method character varying(50),
    loyalty_points_earned integer DEFAULT 0,
    loyalty_points_used integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (sale_id)
);

CREATE TABLE medicines (
    medicine_id integer NOT NULL DEFAULT nextval('medicines_medicine_id_seq'::regclass),
    generic_name character varying(100) NOT NULL,
    brand_name character varying(100),
    form character varying(50),
    strength character varying(50),
    primary_ingredient character varying(100),
    description text,
    health_condition character varying(100),
    is_otc boolean DEFAULT false,
    batch_no character varying(50) NOT NULL,
    mfg_date date,
    expiry_date date,
    quantity integer DEFAULT 0,
    cost_price numeric,
    mrp numeric,
    supplier_id integer,
    reorder_level integer DEFAULT 10,
    low_stock_threshold integer DEFAULT 5,
    location character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (medicine_id)
);

CREATE TABLE suppliers (
    supplier_id integer NOT NULL DEFAULT nextval('suppliers_supplier_id_seq'::regclass),
    name character varying(100) NOT NULL,
    contact_person character varying(100),
    phone numeric,
    email character varying(120),
    address text,
    gst_no character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (supplier_id)
);

CREATE TABLE purchases (
    purchase_id integer NOT NULL DEFAULT nextval('purchases_purchase_id_seq'::regclass),
    supplier_id integer,
    pharmacist_id integer,
    total_amount numeric,
    status character varying(50) DEFAULT 'Pending'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (purchase_id)
);

CREATE TABLE sale_items (
    sale_item_id integer NOT NULL DEFAULT nextval('sale_items_sale_item_id_seq'::regclass),
    sale_id integer,
    medicine_id integer,
    quantity integer NOT NULL,
    unit_price numeric,
    PRIMARY KEY (sale_item_id)
);

CREATE TABLE notifications (
    notification_id integer NOT NULL DEFAULT nextval('notifications_notification_id_seq'::regclass),
    message text NOT NULL,
    type character varying(20) DEFAULT 'info'::character varying,
    link character varying(200),
    is_read boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    status character varying(20) DEFAULT 'Unread'::character varying,
    related_id integer,
    pharmacist_id integer,
    PRIMARY KEY (notification_id)
);

CREATE TABLE purchase_items (
    purchase_item_id integer NOT NULL DEFAULT nextval('purchase_items_purchase_item_id_seq'::regclass),
    purchase_id integer,
    medicine_id integer,
    batch_no character varying(50),
    expiry_date date,
    quantity integer,
    unit_cost numeric,
    PRIMARY KEY (purchase_item_id)
);

CREATE TABLE bot_sessions (
    session_id integer NOT NULL DEFAULT nextval('bot_sessions_session_id_seq'::regclass),
    user_identifier character varying(100) NOT NULL,
    context_data jsonb DEFAULT '{}'::jsonb,
    message_count integer DEFAULT 0,
    started_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_active timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id)
);

CREATE TABLE bot_logs (
    log_id integer NOT NULL DEFAULT nextval('bot_logs_log_id_seq'::regclass),
    session_id integer,
    user_identifier character varying(100) NOT NULL,
    user_message text NOT NULL,
    bot_response text NOT NULL,
    detected_intent character varying(50),
    confidence_score double precision,
    execution_time_ms integer,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (log_id)
);

