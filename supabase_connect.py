import streamlit as st
from supabase import create_client, Client
import pandas as pd

st.title("Supabase Connection Test (Official Client)")

# Initialize connection with Supabase
if 'supabase_client' not in st.session_state:
    try:
        if hasattr(st, 'secrets') and 'supabase' in st.secrets:
            # Use the URL from the secrets if available
            supabase_url = st.secrets.supabase.get("project_url", "https://yegrbbtxlsfbrlyavmbg.supabase.co")
            supabase_key = st.secrets.supabase.get("api_key", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ3JiYnR4bHNmYnJseWF2bWJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTQ2OTA4NTcsImV4cCI6MjAxMDI2Njg1N30.CQRKj-CzkPWtdWgIOuRKUeXVfZUK5j77l_3X9M5-V2Y")
        else:
            # Default values for testing
            supabase_url = "https://yegrbbtxlsfbrlyavmbg.supabase.co"
            supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ3JiYnR4bHNmYnJseWF2bWJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTQ2OTA4NTcsImV4cCI6MjAxMDI2Njg1N30.CQRKj-CzkPWtdWgIOuRKUeXVfZUK5j77l_3X9M5-V2Y"
        
        st.session_state.supabase_client = create_client(supabase_url, supabase_key)
        st.success("✅ Supabase client initialized successfully!")
        st.write(f"Connected to project URL: {supabase_url}")
    except Exception as e:
        st.error(f"❌ Failed to initialize Supabase client: {str(e)}")

# Connection check button
if st.button("Test Database Connection", type="primary"):
    if 'supabase_client' in st.session_state:
        try:
            client: Client = st.session_state.supabase_client
            
            # Simple query to check connection
            # First, check if table exists, if not create it
            st.write("Checking if test table exists...")
            try:
                # Test query on existing tables
                response = client.table('stores').select("*").limit(5).execute()
                data = response.data
                
                if data:
                    st.success(f"✅ Successfully queried existing table 'stores'")
                    st.write(f"Found {len(data)} records in 'stores' table")
                    
                    # Display the data
                    df = pd.DataFrame(data)
                    st.dataframe(df)
                else:
                    st.warning("Table 'stores' exists but is empty")
            except Exception as e:
                if "relation" in str(e) and "does not exist" in str(e):
                    st.warning("Table 'stores' doesn't exist yet. Let's create a test table.")
                    
                    # Create a test table
                    try:
                        st.write("Creating a test table 'test_connection'...")
                        # Use SQL through the rpc method to create a table
                        client.rpc(
                            'create_test_table',
                            {'table_name': 'test_connection'}
                        ).execute()
                        st.success("✅ Test table created successfully!")
                    except Exception as table_e:
                        st.error(f"❌ Error creating test table: {str(table_e)}")
                else:
                    st.error(f"❌ Error querying table: {str(e)}")
        except Exception as e:
            st.error(f"❌ Connection test failed: {str(e)}")
    else:
        st.error("❌ Supabase client not initialized. Please check the error above.")

# Helper info
st.markdown("---")
st.markdown("""
### Important Notes:
1. Make sure your Supabase project URL and API key are correct
2. The API key should be the public anon key for basic operations
3. For database operations that require more permissions, use the service_role key
""")

# Update secrets info
st.markdown("### Secrets Configuration Guide")
st.code("""
# Add this to your .streamlit/secrets.toml file:
[supabase]
project_url = "https://your-project-id.supabase.co"
api_key = "your-anon-key"
""", language="toml") 