import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="Supabase Table Creation", layout="wide")
st.title("🛠️ Supabase Table Setup")
st.write("This utility creates necessary tables in your Supabase database")

def get_supabase_client():
    """Get Supabase connection details from secrets"""
    try:
        # Get connection details from secrets
        if hasattr(st, 'secrets') and 'connections' in st.secrets and 'supabase' in st.secrets.connections:
            project_url = st.secrets.connections.supabase.get("project_url")
            api_key = st.secrets.connections.supabase.key if hasattr(st.secrets.connections.supabase, 'key') else st.secrets.connections.supabase.get("api_key")
            service_key = None
            
            # Try to get service role key from admin connection or service_role_key field
            if hasattr(st, 'secrets') and 'connections' in st.secrets and 'supabase_admin' in st.secrets.connections:
                service_key = st.secrets.connections.supabase_admin.get("api_key")
            elif hasattr(st.secrets.connections.supabase, 'service_role_key'):
                service_key = st.secrets.connections.supabase.service_role_key
                
            st.write("✅ Using connections.supabase format")
        else:
            # Fallback to older format
            project_url = st.secrets.supabase.url if hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase') and hasattr(st.secrets.supabase, 'url') else None
            api_key = st.secrets.supabase.api_key if hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase') and hasattr(st.secrets.supabase, 'api_key') else None
            service_key = st.secrets.supabase.service_role_key if hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase') and hasattr(st.secrets.supabase, 'service_role_key') else None
            
            # Check for key instead of api_key
            if not api_key and hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase') and hasattr(st.secrets.supabase, 'key'):
                api_key = st.secrets.supabase.key
                
            # Check for service_key
            if not service_key and hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase') and hasattr(st.secrets.supabase, 'service_key'):
                service_key = st.secrets.supabase.service_key
                
            st.write("✅ Using direct supabase format")
        
        if not project_url or not api_key:
            st.error("Supabase connection details not found in Streamlit secrets")
            st.write("Please configure your Supabase secrets with at least:")
            st.code("""
[connections.supabase]
project_url = "https://your-project-id.supabase.co"
api_key = "your_anon_key"
service_role_key = "your_service_role_key"  # Needed for table creation
            """)
            return None
        
        if not service_key:
            st.warning("No service role key found. Table creation may fail without admin privileges.")
            headers = {
                "apikey": api_key,
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        else:
            headers = {
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
        
        client = {
            "project_url": project_url,
            "headers": headers
        }
        
        # Test connection
        test_url = f"{project_url}/rest/v1/stores?limit=1"
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        st.success(f"✅ Supabase connection successful!")
        return client
        
    except Exception as e:
        st.error(f"❌ Supabase connection failed: {str(e)}")
        return None

def execute_sql(client, sql_query):
    """Execute an SQL query via the Supabase RESTful API"""
    try:
        # We need to use the rpc endpoint for SQL execution
        url = f"{client['project_url']}/rest/v1/rpc/execute_sql"
        
        # Payload
        payload = {
            "query": sql_query
        }
        
        response = requests.post(url, headers=client["headers"], json=payload)
        
        # Check if the function is not found
        if response.status_code == 404:
            st.error("The 'execute_sql' function does not exist in Supabase.")
            st.write("You might need to create this function using SQL Editor first:")
            st.code("""
CREATE OR REPLACE FUNCTION execute_sql(query text)
RETURNS VOID AS $$
BEGIN
  EXECUTE query;
END;
$$ LANGUAGE plpgsql;
            """)
            return False
        
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error executing SQL: {str(e)}")
        return False

def create_tables(client):
    """Create all necessary tables if they don't exist"""
    
    # Create stores table
    stores_table = """
    CREATE TABLE IF NOT EXISTS stores (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        merchant_id TEXT UNIQUE NOT NULL,
        api_key TEXT,
        access_token TEXT,
        last_sync_date TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Create payments table
    payments_table = """
    CREATE TABLE IF NOT EXISTS payments (
        id TEXT PRIMARY KEY,
        merchant_id TEXT NOT NULL,
        order_id TEXT,
        amount INTEGER NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Create order_items table
    order_items_table = """
    CREATE TABLE IF NOT EXISTS order_items (
        id TEXT PRIMARY KEY,
        merchant_id TEXT NOT NULL,
        order_id TEXT NOT NULL,
        name TEXT,
        price NUMERIC(10,2),
        quantity INTEGER DEFAULT 1,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Create expenses table
    expenses_table = """
    CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        store_id TEXT NOT NULL,
        date DATE NOT NULL,
        amount NUMERIC(10,2) NOT NULL,
        category TEXT,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # Create sync_log table
    sync_log_table = """
    CREATE TABLE IF NOT EXISTS sync_log (
        id SERIAL PRIMARY KEY,
        sync_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        status TEXT,
        details TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    tables = {
        "stores": stores_table,
        "payments": payments_table,
        "order_items": order_items_table,
        "expenses": expenses_table,
        "sync_log": sync_log_table
    }
    
    results = {}
    
    # Try to create tables
    for table_name, sql in tables.items():
        st.write(f"Creating table: {table_name}")
        success = execute_sql(client, sql)
        results[table_name] = success
        if success:
            st.success(f"✅ Table '{table_name}' created or already exists")
        else:
            st.error(f"❌ Failed to create table '{table_name}'")
            
            # Try using REST API to check if table exists
            try:
                check_url = f"{client['project_url']}/rest/v1/{table_name}?limit=1"
                response = requests.get(check_url, headers=client["headers"])
                if response.status_code == 200:
                    st.warning(f"Table '{table_name}' might already exist (REST API check passed)")
                    results[table_name] = True
                else:
                    st.error(f"REST API check also failed: {response.status_code}")
            except Exception as e:
                st.error(f"REST API check error: {str(e)}")
    
    # Check overall result
    if all(results.values()):
        st.success("🎉 All tables created successfully!")
        return True
    else:
        st.warning("⚠️ Some tables could not be created using SQL. Trying with REST API...")
        return False

# Main execution
supabase_client = get_supabase_client()

if not supabase_client:
    st.stop()

if st.button("Create Tables"):
    with st.spinner("Creating tables..."):
        success = create_tables(supabase_client)
        
        if success:
            st.success("✅ Database setup complete! Your app should now work properly.")
        else:
            st.error("❌ Could not create all tables. Please check your Supabase account permissions.")
            st.write("You may need to create tables manually using the Supabase UI or SQL Editor.") 