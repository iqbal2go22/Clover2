import streamlit as st
import pandas as pd
from supabase_connect import SupabaseConnection

st.title("Testing Supabase Connection")

# Initialize the connection
try:
    conn = st.connection("supabase", type=SupabaseConnection)
    
    # Display basic connection info
    st.write(f"Connected to: {conn.project_url}")
    masked_key = conn.api_key[:10] + "..." + conn.api_key[-5:] if len(conn.api_key) > 15 else conn.api_key
    st.write(f"API Key: {masked_key}")
    
    # Test connection
    if st.button("Test Connection"):
        if conn.test_connection():
            st.success("✅ Successfully connected to Supabase!")
            
            # Try to get tables
            try:
                tables = conn.get_all_tables()
                if tables:
                    st.success(f"Found {len(tables)} tables!")
                    st.write("Tables:")
                    st.json(tables)
                else:
                    st.info("No tables found or insufficient permissions.")
            except Exception as e:
                st.warning(f"Couldn't list tables: {str(e)}")
                
            # Try to query stores
            try:
                stores = conn.query("stores", limit=10)
                if not stores.empty:
                    st.success(f"Found {len(stores)} stores!")
                    st.dataframe(stores)
                else:
                    st.info("No stores found.")
            except Exception as e:
                st.error(f"Error fetching stores: {str(e)}")
        else:
            st.error("Failed to connect to Supabase")
            
except Exception as e:
    st.error(f"Error initializing connection: {str(e)}")
    st.write("Make sure your secrets.toml file is correctly set up with [connections.supabase] section.") 