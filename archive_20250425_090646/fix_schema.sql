-- DROP EXISTING TABLES
DROP TABLE IF EXISTS stores;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS expenses;
DROP TABLE IF EXISTS sync_log;

-- Now recreate tables with EXACT SQLite schema

-- Create stores table
CREATE TABLE stores (
    id SERIAL PRIMARY KEY,
    merchant_id TEXT UNIQUE,
    name TEXT,
    access_token TEXT,
    last_sync_date TEXT
);

-- Create payments table
CREATE TABLE payments (
    payment_id TEXT PRIMARY KEY,
    store_id INTEGER,
    amount REAL,
    created_time TEXT,
    employee_id TEXT,
    order_id TEXT,
    device_id TEXT,
    tender_type TEXT,
    card_type TEXT,
    last_4 TEXT,
    sync_date TEXT
);

-- Create order_items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id TEXT,
    item_id TEXT,
    store_id INTEGER,
    name TEXT,
    price REAL,
    quantity INTEGER,
    created_time TEXT,
    employee_id TEXT,
    is_refunded TEXT,
    discount_amount REAL,
    sync_date TEXT,
    UNIQUE(order_id, item_id)
);

-- Create expenses table
CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    store_id INTEGER,
    amount REAL,
    category TEXT,
    description TEXT,
    date TEXT,
    created_at TEXT
);

-- Create sync_log table
CREATE TABLE sync_log (
    id SERIAL PRIMARY KEY,
    store_id INTEGER,
    sync_date TEXT,
    payments_count INTEGER,
    orders_count INTEGER,
    UNIQUE(store_id, sync_date)
); 