import streamlit as st
import pandas as pd
from datetime import datetime

st.title("🔧 Supabase Database Setup")
st.write("This script will set up all necessary tables in your Supabase database.")

# Get the SQL connection
conn = st.connection("supabase_sql", type="sql")

# Define the SQL scripts for creating tables
create_stores_table = """
CREATE TABLE IF NOT EXISTS stores (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    merchant_id TEXT NOT NULL UNIQUE,
    api_key TEXT,
    access_token TEXT,
    last_sync_date TIMESTAMP
);
"""

create_payments_table = """
CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    merchant_id TEXT,
    order_id TEXT,
    amount INTEGER,
    created_at TIMESTAMP
);
"""

create_order_items_table = """
CREATE TABLE IF NOT EXISTS order_items (
    id TEXT PRIMARY KEY,
    merchant_id TEXT, 
    order_id TEXT,
    name TEXT,
    price REAL,
    quantity INTEGER,
    created_at TIMESTAMP
);
"""

create_expenses_table = """
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
"""

create_sync_log_table = """
CREATE TABLE IF NOT EXISTS sync_log (
    id SERIAL PRIMARY KEY,
    sync_time TIMESTAMP,
    status TEXT
);
"""

insert_stores_data = """
INSERT INTO stores (name, merchant_id, access_token)
VALUES 
('Laurel', '4VZSM7038BKQ1', 'b9f678d7-9b27-e971-d9e4-feab8b227c96'),
('Algiers', 'K25SHP45Z91H1', 'fb51be17-f0c4-c58c-0e08-44bcd4bbc5ab'),
('Hattiesburg', 'J3N08YKN8TSD1', '5608c683-801e-d4cf-092d-abfc907eafcc')
ON CONFLICT (merchant_id) DO NOTHING;
"""

# Create an RPC function for executing arbitrary queries
create_execute_query_function = """
CREATE OR REPLACE FUNCTION execute_query(query_text TEXT, params JSONB DEFAULT '[]')
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    EXECUTE query_text INTO result;
    RETURN result;
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object('error', SQLERRM);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
"""

# Function to run a query and handle errors
def run_query(query, description):
    try:
        with st.spinner(f"Creating {description}..."):
            conn.query(query)
        st.success(f"✅ {description} created successfully")
        return True
    except Exception as e:
        st.error(f"❌ Error creating {description}: {str(e)}")
        return False

# UI to run setup
if st.button("Run Database Setup", type="primary"):
    setup_success = True
    
    # Create tables
    tables = [
        (create_stores_table, "stores table"),
        (create_payments_table, "payments table"),
        (create_order_items_table, "order_items table"),
        (create_expenses_table, "expenses table"),
        (create_sync_log_table, "sync_log table"),
    ]
    
    for query, description in tables:
        success = run_query(query, description)
        setup_success = setup_success and success
    
    # Insert initial data
    if setup_success:
        if run_query(insert_stores_data, "store data"):
            st.success("✅ Initial store data inserted")
        else:
            st.warning("⚠️ Could not insert store data")
    
    # Create RPC function
    if setup_success:
        if run_query(create_execute_query_function, "execute_query RPC function"):
            st.success("✅ RPC function created")
        else:
            st.warning("⚠️ Could not create RPC function")
    
    # Add a sync log entry to record setup
    if setup_success:
        try:
            sync_time = datetime.now().isoformat()
            conn.query(f"INSERT INTO sync_log (sync_time, status) VALUES ('{sync_time}', 'initial_setup')")
            st.success("✅ Initial sync log entry created")
        except Exception as e:
            st.warning(f"⚠️ Could not create sync log entry: {str(e)}")
    
    # Final message
    if setup_success:
        st.success("🎉 Database setup complete! Your Supabase database is ready to use.")
    else:
        st.error("⚠️ Database setup encountered some errors. Please check the messages above.")

# Display current database status
st.subheader("Current Database Status")
with st.expander("Check Tables"):
    try:
        tables_df = conn.query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        if not tables_df.empty:
            st.success(f"Found {len(tables_df)} tables in the database")
            st.dataframe(tables_df)
            
            # For each table, show row count
            st.subheader("Table Row Counts")
            for table in tables_df['table_name']:
                try:
                    count_df = conn.query(f"SELECT COUNT(*) as count FROM {table}")
                    st.write(f"{table}: {count_df.iloc[0]['count']} rows")
                except:
                    st.write(f"{table}: Error counting rows")
        else:
            st.info("No tables found in the database")
    except Exception as e:
        st.error(f"Error checking database status: {str(e)}") 