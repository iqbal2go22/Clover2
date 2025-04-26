import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

st.title("🔧 Supabase Database Setup (REST API)")
st.write("This script will set up all necessary tables in your Supabase database using REST API.")

# Get connection details from admin secrets (service_role)
project_url = st.secrets.connections.supabase_admin.get("project_url")
api_key = st.secrets.connections.supabase_admin.get("api_key")

# Display masked connection info
st.write(f"Project URL: {project_url}")
masked_key = api_key[:10] + "..." + api_key[-5:] if len(api_key) > 15 else api_key
st.write(f"API Key: {masked_key}")
st.info("Using admin key (service_role) for database setup")

# Set up headers for Supabase REST API
headers = {
    "apikey": api_key,
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Test connection function
def test_connection():
    try:
        response = requests.get(
            f"{project_url}/rest/v1/",
            headers=headers,
            timeout=10
        )
        st.write(f"Response status: {response.status_code}")
        st.write(f"Response: {response.text[:100]}")
        return response.status_code in (200, 201, 204)
    except Exception as e:
        st.error(f"Connection test failed: {str(e)}")
        return False

# First, test connection
st.subheader("Testing Admin Connection")
if test_connection():
    st.success("✅ Admin connection successful")
else:
    st.error("❌ Admin connection failed")
    st.stop()

# Direct SQL execution with Supabase's pg_dump endpoint
st.subheader("Create Database Structure")

if st.button("Create Tables Using SQL API", type="primary"):
    # SQL statements to create all tables
    create_tables_sql = """
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
    """
    
    # Try using Supabase's PostgreSQL REST API
    st.write("Attempting to create tables using SQL API...")
    
    # Show SQL for reference
    with st.expander("SQL to execute"):
        st.code(create_tables_sql, language="sql")
    
    # Split SQL into individual statements to execute one by one
    sql_statements = [stmt.strip() for stmt in create_tables_sql.split(';') if stmt.strip()]
    
    success_count = 0
    for i, sql in enumerate(sql_statements):
        try:
            # Use REST pgSQL endpoint for direct SQL execution
            response = requests.post(
                f"{project_url}/rest/v1/pg_dump",
                headers=headers,
                json={"query": sql},
                timeout=15
            )
            
            if response.status_code in (200, 201, 204):
                st.success(f"✅ SQL statement {i+1} executed successfully")
                success_count += 1
            else:
                st.error(f"❌ Failed to execute SQL statement {i+1}: {response.status_code} - {response.text}")
                
                # Try alternative endpoint
                st.write("Trying alternative endpoint...")
                alt_response = requests.post(
                    f"{project_url}/rest/v1/sql",
                    headers=headers,
                    json={"query": sql},
                    timeout=15
                )
                
                if alt_response.status_code in (200, 201, 204):
                    st.success(f"✅ SQL statement {i+1} executed successfully with alternative endpoint")
                    success_count += 1
                else:
                    st.error(f"❌ Failed with alternative endpoint: {alt_response.status_code} - {alt_response.text}")
        except Exception as e:
            st.error(f"❌ Error executing SQL statement {i+1}: {str(e)}")
    
    if success_count == len(sql_statements):
        st.success(f"✅ All {len(sql_statements)} SQL statements executed successfully!")
    else:
        st.warning(f"⚠️ {success_count} of {len(sql_statements)} SQL statements executed successfully.")
        
        # Show instructions for manual creation
        st.error("SQL API not working. Please create tables manually in Supabase SQL editor.")
        st.info("Copy the SQL above and run it in the Supabase SQL Editor.")
        
        link = f"{project_url.replace('.co', '.co/project/sql')}"
        st.markdown(f"[Open Supabase SQL Editor]({link})")

# Add store data
st.subheader("Insert Real Store Data")
if st.button("Insert Store Data"):
    # Insert store data using REST API
    stores_data = [
        {
            "name": "Laurel",
            "merchant_id": "4VZSM7038BKQ1",
            "access_token": "b9f678d7-9b27-e971-d9e4-feab8b227c96"
        },
        {
            "name": "Algiers",
            "merchant_id": "K25SHP45Z91H1",
            "access_token": "fb51be17-f0c4-c58c-0e08-44bcd4bbc5ab"
        },
        {
            "name": "Hattiesburg",
            "merchant_id": "J3N08YKN8TSD1",
            "access_token": "5608c683-801e-d4cf-092d-abfc907eafcc"
        }
    ]
    
    # Try to insert each store
    success_count = 0
    for store in stores_data:
        try:
            response = requests.post(
                f"{project_url}/rest/v1/stores",
                headers=headers,
                json=store,
                timeout=10
            )
            
            if response.status_code in (200, 201, 204, 409):  # 409 is conflict (already exists)
                success_count += 1
                st.success(f"✅ Store {store['name']} added or already exists")
            else:
                st.error(f"❌ Failed to add store {store['name']}: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"❌ Error adding store {store['name']}: {str(e)}")
    
    if success_count == len(stores_data):
        st.success(f"✅ All {len(stores_data)} stores added successfully!")

# Add initial sync log entry
st.subheader("Create Sync Log Entry")
if st.button("Create Sync Log Entry"):
    try:
        sync_time = datetime.now().isoformat()
        response = requests.post(
            f"{project_url}/rest/v1/sync_log",
            headers=headers,
            json={"sync_time": sync_time, "status": "initial_setup"},
            timeout=10
        )
        
        if response.status_code in (200, 201, 204):
            result = response.json()
            st.success("✅ Sync log entry created")
            st.json(result)
        else:
            st.error(f"❌ Failed to create sync log entry: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"❌ Error creating sync log entry: {str(e)}")

# Check table status
st.subheader("Check Tables")
if st.button("List Tables"):
    tables = ["stores", "payments", "order_items", "expenses", "sync_log"]
    
    st.write("Checking tables:")
    for table in tables:
        try:
            response = requests.get(
                f"{project_url}/rest/v1/{table}?limit=1",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                st.success(f"✅ Table '{table}' exists")
                
                # Count rows
                count_response = requests.get(
                    f"{project_url}/rest/v1/{table}?select=count",
                    headers={**headers, "Prefer": "count=exact"},
                    timeout=5
                )
                
                if "content-range" in count_response.headers:
                    count = count_response.headers["content-range"].split("/")[1]
                    st.write(f"   - Row count: {count}")
                else:
                    st.write(f"   - Unable to get exact count")
                    
                # Show sample data if available
                if response.text and response.text != "[]":
                    sample = response.json()
                    st.write(f"   - Sample data:")
                    st.json(sample)
            else:
                st.error(f"❌ Table '{table}' doesn't exist: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Error checking table '{table}': {str(e)}")

# Show Manual Creation Instructions
st.subheader("Manual Database Setup")
with st.expander("Create Tables Manually"):
    st.write("If automatic table creation doesn't work, you can create tables manually in the Supabase SQL Editor.")
    
    st.code("""
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
    """, language="sql")
    
    # Link to Supabase SQL Editor
    sql_editor_url = f"{project_url.replace('.co', '.co/project/sql')}"
    st.markdown(f"[Open Supabase SQL Editor]({sql_editor_url})")

# Final instructions
st.markdown("---")
st.info("""
### Next Steps
After tables are created, you can:
1. Run the migration script to transfer data from SQLite
2. Use the `cloud_db_utils.py` module with Supabase REST API connection
3. Deploy to Streamlit Cloud
""")

# Show project URL for easy reference
st.markdown(f"Supabase Project: [Open Dashboard]({project_url})") 