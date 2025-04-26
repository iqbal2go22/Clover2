# Setting Up Supabase Database Using SQL Editor

Based on the error messages, it seems direct PostgreSQL connections may be blocked by firewall or network settings. Let's use the Supabase SQL Editor instead.

## Step 1: Access the SQL Editor

1. Go to your Supabase Dashboard
2. Click on the "SQL Editor" tab in the left sidebar
3. Create a new SQL query or use an existing one

## Step 2: Create Tables

Copy and paste the following SQL into the query editor:

```sql
-- Create stores table
CREATE TABLE IF NOT EXISTS stores (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    merchant_id TEXT NOT NULL UNIQUE,
    api_key TEXT,
    access_token TEXT,
    last_sync_date TIMESTAMP
);

-- Create payments table
CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    merchant_id TEXT,
    order_id TEXT,
    amount INTEGER,
    created_at TIMESTAMP
);

-- Create order_items table
CREATE TABLE IF NOT EXISTS order_items (
    id TEXT PRIMARY KEY,
    merchant_id TEXT, 
    order_id TEXT,
    name TEXT,
    price REAL,
    quantity INTEGER,
    created_at TIMESTAMP
);

-- Create expenses table
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    store_id TEXT,
    date DATE,
    amount REAL,
    category TEXT,
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create sync_log table
CREATE TABLE IF NOT EXISTS sync_log (
    id SERIAL PRIMARY KEY,
    sync_time TIMESTAMP,
    status TEXT
);

-- Insert store data
INSERT INTO stores (name, merchant_id, access_token) VALUES
('Laurel', '4VZSM7038BKQ1', 'b9f678d7-9b27-e971-d9e4-feab8b227c96'),
('Algiers', 'K25SHP45Z91H1', 'fb51be17-f0c4-c58c-0e08-44bcd4bbc5ab'),
('Hattiesburg', 'J3N08YKN8TSD1', '5608c683-801e-d4cf-092d-abfc907eafcc')
ON CONFLICT (merchant_id) DO NOTHING;

-- Add initial sync log entry
INSERT INTO sync_log (sync_time, status) VALUES (NOW(), 'initial_setup');
```

## Step 3: Run the SQL

1. Click the "Run" button to execute the SQL statements
2. Verify that all tables were created successfully
3. Check that the store data and sync log entry were inserted

## Step 4: Verify Tables

Run these queries to check that your tables exist and contain data:

```sql
-- List all tables
SELECT * FROM pg_catalog.pg_tables 
WHERE schemaname = 'public';

-- Check stores table
SELECT * FROM stores;

-- Check sync_log table
SELECT * FROM sync_log;
```

## Step 5: Update Your App

Once the tables are created, you can run your application with the Streamlit Cloud connection. Your app should now be able to connect using the REST API, even if direct PostgreSQL connections are blocked.

## Troubleshooting

If you encounter errors in the SQL editor:
- Make sure you're logged in with an account that has sufficient permissions
- Try executing one statement at a time if the batch execution fails
- Check for syntax errors in the SQL statements 