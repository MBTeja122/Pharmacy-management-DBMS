-- PostgreSQL seed data for Pharmacy-management-DBMS
-- Usage:
--   psql -h <host> -U <user> -d <database> -f db/seed.sql
--
-- Note:
--   Password hashes below use Werkzeug's legacy plain format for easy local testing:
--   Admin user password: Admin@123
--   Staff users password: Staff@123

BEGIN;

-- -----------------------------------------------------------------------------
-- PHARMACISTS
-- -----------------------------------------------------------------------------
INSERT INTO pharmacists (pharmacist_id, name, email, phone, password_hash, role, active, created_at)
VALUES
    (1, 'Admin User', 'admin@pharmatrust.local', 9876500001, 'plain$$Admin@123', 'Admin', true, NOW() - INTERVAL '30 days'),
    (2, 'Teja Reddy', 'teja@pharmatrust.local', 9876500002, 'plain$$Staff@123', 'Staff', true, NOW() - INTERVAL '20 days'),
    (3, 'Ananya Rao', 'ananya@pharmatrust.local', 9876500003, 'plain$$Staff@123', 'Staff', true, NOW() - INTERVAL '10 days')
ON CONFLICT (email) DO NOTHING;

-- -----------------------------------------------------------------------------
-- CUSTOMERS
-- -----------------------------------------------------------------------------
INSERT INTO customers (customer_id, name, phone, email, address, loyalty_points, created_at)
VALUES
    (1, 'Rahul Kumar', '9000000001', 'rahul.kumar@example.com', 'Banjara Hills, Hyderabad', 45, NOW() - INTERVAL '18 days'),
    (2, 'Sneha Iyer', '9000000002', 'sneha.iyer@example.com', 'Madhapur, Hyderabad', 120, NOW() - INTERVAL '12 days'),
    (3, 'Arjun Nair', '9000000003', 'arjun.nair@example.com', 'Kondapur, Hyderabad', 10, NOW() - INTERVAL '6 days'),
    (4, 'Walk-in Customer', '9000000004', NULL, 'In-store', 0, NOW() - INTERVAL '2 days')
ON CONFLICT (customer_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- SUPPLIERS
-- -----------------------------------------------------------------------------
INSERT INTO suppliers (supplier_id, name, contact_person, phone, email, address, gst_no, created_at)
VALUES
    (1, 'Medline Distributors', 'Vikram Singh', 9988000001, 'sales@medline.example', 'Secunderabad, Telangana', '36ABCDE1234F1Z1', NOW() - INTERVAL '60 days'),
    (2, 'HealthBridge Pharma', 'Pooja Menon', 9988000002, 'orders@healthbridge.example', 'Gachibowli, Hyderabad', '36ABCDE5678F1Z1', NOW() - INTERVAL '45 days')
ON CONFLICT (supplier_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- MEDICINES
-- -----------------------------------------------------------------------------
INSERT INTO medicines (
    medicine_id, generic_name, brand_name, form, strength, primary_ingredient, description,
    health_condition, is_otc, batch_no, mfg_date, expiry_date, quantity,
    cost_price, mrp, supplier_id, reorder_level, low_stock_threshold, location,
    created_at, updated_at
)
VALUES
    (1, 'Paracetamol', 'Dolo 650', 'Tablet', '650 mg', 'Paracetamol', 'Pain and fever relief tablet', 'Fever', true,
     'DL650A1', CURRENT_DATE - INTERVAL '11 months', CURRENT_DATE + INTERVAL '8 months', 180,
     1.80, 2.50, 1, 50, 20, 'A1-R1', NOW() - INTERVAL '20 days', NOW() - INTERVAL '1 days'),

    (2, 'Cetirizine', 'Cetzine', 'Tablet', '10 mg', 'Cetirizine Hydrochloride', 'Antihistamine for allergies', 'Allergy', true,
     'CTZ10B2', CURRENT_DATE - INTERVAL '7 months', CURRENT_DATE + INTERVAL '11 months', 120,
     1.20, 2.00, 2, 40, 15, 'A1-R2', NOW() - INTERVAL '19 days', NOW() - INTERVAL '1 days'),

    (3, 'Azithromycin', 'Azee 500', 'Tablet', '500 mg', 'Azithromycin', 'Antibiotic course tablet', 'Infection', false,
     'AZ500C3', CURRENT_DATE - INTERVAL '6 months', CURRENT_DATE + INTERVAL '5 months', 75,
     9.50, 14.00, 1, 30, 10, 'B2-R1', NOW() - INTERVAL '18 days', NOW() - INTERVAL '1 days'),

    (4, 'Pantoprazole', 'Pantocid 40', 'Tablet', '40 mg', 'Pantoprazole', 'Acidity and reflux medicine', 'Acidity', false,
     'PT40D4', CURRENT_DATE - INTERVAL '8 months', CURRENT_DATE + INTERVAL '10 months', 95,
     4.00, 6.50, 2, 35, 12, 'B2-R2', NOW() - INTERVAL '17 days', NOW() - INTERVAL '1 days'),

    (5, 'Amoxicillin + Clavulanic Acid', 'Augmentin 625', 'Tablet', '625 mg', 'Amoxicillin + Clavulanate', 'Broad-spectrum antibiotic', 'Infection', false,
     'AG625E5', CURRENT_DATE - INTERVAL '9 months', CURRENT_DATE + INTERVAL '4 months', 45,
     16.00, 24.00, 1, 25, 8, 'C1-R1', NOW() - INTERVAL '16 days', NOW() - INTERVAL '1 days')
ON CONFLICT (medicine_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- PURCHASES + PURCHASE ITEMS
-- -----------------------------------------------------------------------------
INSERT INTO purchases (purchase_id, supplier_id, pharmacist_id, total_amount, status, created_at)
VALUES
    (1, 1, 1, 2350.00, 'Completed', NOW() - INTERVAL '15 days'),
    (2, 2, 2, 1725.00, 'Completed', NOW() - INTERVAL '9 days')
ON CONFLICT (purchase_id) DO NOTHING;

INSERT INTO purchase_items (purchase_item_id, purchase_id, medicine_id, batch_no, expiry_date, quantity, unit_cost)
VALUES
    (1, 1, 1, 'DL650A1', CURRENT_DATE + INTERVAL '8 months', 200, 1.80),
    (2, 1, 3, 'AZ500C3', CURRENT_DATE + INTERVAL '5 months', 80, 9.50),
    (3, 1, 5, 'AG625E5', CURRENT_DATE + INTERVAL '4 months', 50, 16.00),
    (4, 2, 2, 'CTZ10B2', CURRENT_DATE + INTERVAL '11 months', 150, 1.20),
    (5, 2, 4, 'PT40D4', CURRENT_DATE + INTERVAL '10 months', 100, 4.00)
ON CONFLICT (purchase_item_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- SALES + SALE ITEMS
-- -----------------------------------------------------------------------------
INSERT INTO sales (
    sale_id, invoice_no, pharmacist_id, customer_id, total_amount, discount, tax,
    payment_method, loyalty_points_earned, loyalty_points_used, created_at
)
VALUES
    (1, 'INV-2026-0001', 2, 1, 165.00, 5.00, 8.00, 'UPI', 10, 0, NOW() - INTERVAL '7 days'),
    (2, 'INV-2026-0002', 3, 2, 242.00, 0.00, 12.00, 'Card', 14, 20, NOW() - INTERVAL '4 days'),
    (3, 'INV-2026-0003', 2, 4, 84.00, 0.00, 4.00, 'Cash', 4, 0, NOW() - INTERVAL '1 days')
ON CONFLICT (sale_id) DO NOTHING;

INSERT INTO sale_items (sale_item_id, sale_id, medicine_id, quantity, unit_price)
VALUES
    (1, 1, 1, 20, 2.50),
    (2, 1, 2, 15, 2.00),
    (3, 1, 4, 10, 6.50),

    (4, 2, 3, 8, 14.00),
    (5, 2, 5, 5, 24.00),
    (6, 2, 1, 8, 2.50),

    (7, 3, 2, 12, 2.00),
    (8, 3, 4, 8, 6.50)
ON CONFLICT (sale_item_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- NOTIFICATIONS
-- -----------------------------------------------------------------------------
INSERT INTO notifications (
    notification_id, message, type, link, is_read, created_at, status, related_id, pharmacist_id
)
VALUES
    (1, 'New staff account approved: Ananya Rao', 'info', '/admin/approvals', true, NOW() - INTERVAL '3 days', 'Read', 3, 1),
    (2, 'Low stock warning: Augmentin 625 below reorder level', 'warning', '/medicines', false, NOW() - INTERVAL '1 days', 'Unread', 5, 1),
    (3, 'Daily sales summary is ready for review', 'info', '/admin/analytics', false, NOW() - INTERVAL '12 hours', 'Unread', 2, 1)
ON CONFLICT (notification_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- CHATBOT SESSIONS + LOGS
-- -----------------------------------------------------------------------------
INSERT INTO bot_sessions (session_id, user_identifier, context_data, message_count, started_at, last_active)
VALUES
    (1, 'admin@pharmatrust.local', '{"role":"Admin","last_intent":"CHECK_STOCK"}'::jsonb, 3, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 hours'),
    (2, 'teja@pharmatrust.local', '{"role":"Staff","last_intent":"TOP_SELLING"}'::jsonb, 2, NOW() - INTERVAL '1 days', NOW() - INTERVAL '3 hours')
ON CONFLICT (user_identifier) DO NOTHING;

INSERT INTO bot_logs (
    log_id, session_id, user_identifier, user_message, bot_response,
    detected_intent, confidence_score, execution_time_ms, metadata, created_at
)
VALUES
    (1, 1, 'admin@pharmatrust.local', 'show me low stock medicines', 'I found 1 medicine below threshold: Augmentin 625.',
     'LOW_STOCK', 0.93, 121, '{"matches":1}'::jsonb, NOW() - INTERVAL '2 days'),

    (2, 1, 'admin@pharmatrust.local', 'check stock of dolo 650', 'Dolo 650 currently has 180 units in stock.',
     'CHECK_STOCK', 0.97, 98, '{"medicine_id":1}'::jsonb, NOW() - INTERVAL '1 days'),

    (3, 2, 'teja@pharmatrust.local', 'top selling products this week', 'Top sellers are Dolo 650, Azee 500, and Cetzine.',
     'TOP_SELLING', 0.89, 147, '{"window_days":7}'::jsonb, NOW() - INTERVAL '5 hours')
ON CONFLICT (log_id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Keep serial sequences aligned after explicit IDs.
-- -----------------------------------------------------------------------------
SELECT setval(pg_get_serial_sequence('pharmacists', 'pharmacist_id'), COALESCE(MAX(pharmacist_id), 1), true) FROM pharmacists;
SELECT setval(pg_get_serial_sequence('customers', 'customer_id'), COALESCE(MAX(customer_id), 1), true) FROM customers;
SELECT setval(pg_get_serial_sequence('suppliers', 'supplier_id'), COALESCE(MAX(supplier_id), 1), true) FROM suppliers;
SELECT setval(pg_get_serial_sequence('medicines', 'medicine_id'), COALESCE(MAX(medicine_id), 1), true) FROM medicines;
SELECT setval(pg_get_serial_sequence('sales', 'sale_id'), COALESCE(MAX(sale_id), 1), true) FROM sales;
SELECT setval(pg_get_serial_sequence('purchases', 'purchase_id'), COALESCE(MAX(purchase_id), 1), true) FROM purchases;
SELECT setval(pg_get_serial_sequence('sale_items', 'sale_item_id'), COALESCE(MAX(sale_item_id), 1), true) FROM sale_items;
SELECT setval(pg_get_serial_sequence('purchase_items', 'purchase_item_id'), COALESCE(MAX(purchase_item_id), 1), true) FROM purchase_items;
SELECT setval(pg_get_serial_sequence('notifications', 'notification_id'), COALESCE(MAX(notification_id), 1), true) FROM notifications;
SELECT setval(pg_get_serial_sequence('bot_sessions', 'session_id'), COALESCE(MAX(session_id), 1), true) FROM bot_sessions;
SELECT setval(pg_get_serial_sequence('bot_logs', 'log_id'), COALESCE(MAX(log_id), 1), true) FROM bot_logs;

COMMIT;
