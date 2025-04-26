import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.title("Supabase SQL Connection Test")

# Initialize the SQL connection to Supabase
try:
    # This uses the built-in SQLConnection functionality
    conn = st.connection("supabase_sql", type="sql")
    
    st.success("✅ SQL Connection initialized")
    
    # Test the connection with a simple query
    if st.button("Test SQL Connection"):
        with st.spinner("Running query..."):
            # Try to query the PostgreSQL version
            df = conn.query("SELECT version();")
            if not df.empty:
                st.success("Connection successful!")
                st.dataframe(df)
                
                # List all tables in the public schema
                tables_df = conn.query("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                
                if not tables_df.empty:
                    st.success(f"Found {len(tables_df)} tables in the public schema!")
                    st.dataframe(tables_df)
                    
                    # If we found tables, try to get a sample from the stores table
                    if 'stores' in tables_df['table_name'].values:
                        stores_df = conn.query("SELECT * FROM stores LIMIT 5;")
                        st.subheader("Sample stores data:")
                        st.dataframe(stores_df)
                else:
                    st.info("No tables found in the public schema.")
            else:
                st.error("Query returned no results.")
                
except Exception as e:
    st.error(f"❌ Connection failed: {str(e)}")
    st.info("""
    Make sure your secrets.toml file contains:
    
    ```
    [connections.supabase_sql]
    type = "postgresql"
    url = "${database_url}"
    ```
    
    Where `${database_url}` is your Supabase PostgreSQL connection string.
    """)

# Add a section showing required secrets.toml format
st.markdown("---")
st.markdown("""
### Required Configuration
To use this SQL connection, add the following to your `.streamlit/secrets.toml` file:
""")

st.code("""
[connections.supabase_sql]
type = "postgresql"
url = "postgresql://postgres.yegrbbtxlsfbrlyavmbg:password@yegrbbtxlsfbrlyavmbg.supabase.co:6543/postgres"

# Replace with your actual connection string from Supabase
# For direct connection use port 5432
# For connection pooling use port 6543
""", language="toml") 