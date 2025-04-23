import streamlit as st
import json
import requests
import pandas as pd

st.title("Supabase Connection Test (Simple Version)")

# This version avoids using the supabase-py library which has compatibility issues
# Instead, it uses direct REST API calls which are more reliable

# Get credentials from secrets
if hasattr(st, 'secrets') and 'supabase' in st.secrets:
    project_url = st.secrets.supabase.get("project_url", "https://yegrbbtxlsfbrlyavmbg.supabase.co")
    api_key = st.secrets.supabase.get("api_key", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ3JiYnR4bHNmYnJseWF2bWJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTQ2OTA4NTcsImV4cCI6MjAxMDI2Njg1N30.CQRKj-CzkPWtdWgIOuRKUeXVfZUK5j77l_3X9M5-V2Y")
else:
    # Default values for testing
    project_url = "https://yegrbbtxlsfbrlyavmbg.supabase.co"
    api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ3JiYnR4bHNmYnJseWF2bWJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTQ2OTA4NTcsImV4cCI6MjAxMDI2Njg1N30.CQRKj-CzkPWtdWgIOuRKUeXVfZUK5j77l_3X9M5-V2Y"

# Display configuration
st.write(f"Project URL: {project_url}")
masked_key = api_key[:10] + "..." + api_key[-5:] if len(api_key) > 15 else api_key
st.write(f"API Key: {masked_key}")

# Test connection button
if st.button("Test Connection", type="primary"):
    st.write("Testing connection to Supabase...")
    
    try:
        # Set up headers for Supabase REST API
        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Test connection with a simple health check
        response = requests.get(
            f"{project_url}/rest/v1/",
            headers=headers,
            timeout=10
        )
        
        if response.status_code in (200, 201, 204):
            st.success("✅ Successfully connected to Supabase REST API!")
            
            # Try to get tables list
            try:
                # List all tables by querying pg_tables
                rpc_url = f"{project_url}/rest/v1/rpc/get_all_tables"
                payload = {}
                
                response = requests.post(
                    rpc_url,
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code in (200, 201):
                    tables = response.json()
                    if isinstance(tables, list) and len(tables) > 0:
                        st.success(f"✅ Found {len(tables)} tables in the database!")
                        st.write("Tables found:")
                        for table in tables:
                            st.write(f"- {table}")
                    else:
                        st.info("No tables found or insufficient permissions.")
                else:
                    st.warning(f"Could not list tables. Status: {response.status_code}")
                    st.write("This is normal if using anon key with limited permissions.")
            except Exception as e:
                st.warning(f"Could not list tables: {str(e)}")
                st.write("This is normal if using the anon key with limited permissions.")
            
            # Attempt to check if specific tables exist
            for table_name in ["stores", "payments", "order_items"]:
                try:
                    check_url = f"{project_url}/rest/v1/{table_name}?limit=1"
                    response = requests.get(
                        check_url,
                        headers=headers,
                        timeout=5
                    )
                    if response.status_code == 200:
                        st.success(f"✅ Table '{table_name}' exists!")
                    else:
                        st.warning(f"Table '{table_name}' not found or no access. Status: {response.status_code}")
                except Exception as e:
                    st.error(f"Error checking table '{table_name}': {str(e)}")
        else:
            st.error(f"❌ Failed to connect to Supabase. Status code: {response.status_code}")
            st.write(f"Response: {response.text}")
            
    except Exception as e:
        st.error(f"❌ Connection test failed: {str(e)}")

# Initialize Database button
if st.button("Initialize Database", type="primary"):
    st.write("Initializing database tables...")
    
    tables_created = []
    errors = []
    
    # Set up headers for Supabase REST API
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Call custom RPC function to create tables
    # Note: This requires setting up RPC functions in your Supabase project
    try:
        rpc_url = f"{project_url}/rest/v1/rpc/initialize_tables"
        payload = {}
        
        response = requests.post(
            rpc_url,
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code in (200, 201, 204):
            st.success("✅ Tables initialized successfully!")
            result = response.json()
            st.write(f"Result: {result}")
        else:
            st.error(f"❌ Failed to initialize tables. Status code: {response.status_code}")
            st.write(f"Response: {response.text}")
            st.info("Note: You may need to set up an RPC function named 'initialize_tables' in your Supabase project.")
    except Exception as e:
        st.error(f"❌ Error initializing tables: {str(e)}")
        
# Display help info
st.markdown("---")
st.markdown("""
### Using Direct REST API Calls
This app uses direct REST API calls to Supabase instead of the Python client.
This approach is more reliable and avoids compatibility issues with the Supabase library.

### Current Configuration
Make sure your secrets.toml file contains:
""")

st.code("""
[supabase]
project_url = "https://yegrbbtxlsfbrlyavmbg.supabase.co"
api_key = "your-anon-key"
""", language="toml")

st.markdown("""
### Setting up Database Tables
For this to work fully, you may need to create an RPC function in your Supabase project.
""")

st.markdown("© 2024 Clover Executive Dashboard | Cloud Version") 