import streamlit as st
import pandas as pd

st.title("Supabase Connection Test (Official Client)")

# Initialize connection with Supabase
def init_supabase():
    try:
        from supabase import create_client
        
        if hasattr(st, 'secrets') and 'supabase' in st.secrets:
            # Use the URL from the secrets if available
            supabase_url = st.secrets.supabase.get("project_url", "https://yegrbbtxlsfbrlyavmbg.supabase.co")
            supabase_key = st.secrets.supabase.get("api_key", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ3JiYnR4bHNmYnJseWF2bWJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTQ2OTA4NTcsImV4cCI6MjAxMDI2Njg1N30.CQRKj-CzkPWtdWgIOuRKUeXVfZUK5j77l_3X9M5-V2Y")
        else:
            # Default values for testing
            supabase_url = "https://yegrbbtxlsfbrlyavmbg.supabase.co"
            supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ3JiYnR4bHNmYnJseWF2bWJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTQ2OTA4NTcsImV4cCI6MjAxMDI2Njg1N30.CQRKj-CzkPWtdWgIOuRKUeXVfZUK5j77l_3X9M5-V2Y"
        
        # Simple create client with minimal parameters
        client = create_client(supabase_url, supabase_key)
        st.success("✅ Supabase client initialized successfully!")
        st.write(f"Connected to project URL: {supabase_url}")
        return client
    except Exception as e:
        st.error(f"❌ Failed to initialize Supabase client: {str(e)}")
        st.write("Supabase client version may be incompatible. Try using version 1.0.3.")
        return None

# Test Connection button
if st.button("Test Connection", type="primary"):
    client = init_supabase()
    if client:
        try:
            # Simple query to test connection
            st.write("Testing basic connection...")
            
            try:
                # Try a simple query
                response = client.from_('stores').select('*').limit(5).execute()
                data = response.get('data', [])
                
                if data:
                    st.success(f"✅ Successfully queried data from 'stores' table")
                    st.write(f"Found {len(data)} records")
                    
                    # Display the data
                    df = pd.DataFrame(data)
                    st.dataframe(df)
                else:
                    st.warning("Table 'stores' exists but is empty or no access")
            except Exception as e:
                st.error(f"❌ Error querying data: {str(e)}")
                st.info("This is normal if the table doesn't exist or you don't have access.")
        except Exception as e:
            st.error(f"❌ Connection test failed: {str(e)}")

# Check Secrets button
if st.button("Check Secrets Configuration", type="primary"):
    if hasattr(st, 'secrets'):
        st.write("Secrets found in Streamlit configuration:")
        
        if 'supabase' in st.secrets:
            st.success("✅ Supabase section found in secrets")
            
            if 'project_url' in st.secrets.supabase:
                masked_url = st.secrets.supabase.project_url[:20] + "..." + st.secrets.supabase.project_url[-10:]
                st.write(f"Project URL: {masked_url}")
            else:
                st.error("❌ No project_url in supabase secrets")
                
            if 'api_key' in st.secrets.supabase:
                st.write("API key: ✓ Present (hidden for security)")
            else:
                st.error("❌ No api_key in supabase secrets")
        else:
            st.error("❌ No supabase section in secrets")
            
        # Check for store configurations
        store_sections = [s for s in st.secrets.keys() if s.startswith('store_')]
        if store_sections:
            st.success(f"✅ Found {len(store_sections)} store configurations")
            for store in store_sections:
                if 'name' in st.secrets[store]:
                    st.write(f"- {st.secrets[store].name}")
                else:
                    st.write(f"- {store} (no name specified)")
        else:
            st.warning("⚠️ No store configurations found")
    else:
        st.error("❌ No secrets configured")

# Helper info
st.markdown("---")
st.markdown("""
### Required Secrets Configuration:

The app needs these secrets to be configured in the Streamlit Cloud dashboard:

```toml
[supabase]
project_url = "https://yegrbbtxlsfbrlyavmbg.supabase.co"
api_key = "your-anon-key"

# Store configurations
[store_1]
name = "Store Name"
merchant_id = "MERCHANT_ID"
access_token = "ACCESS_TOKEN"
```
""")

st.info("This test app is using Supabase version 1.0.3 for compatibility with Streamlit Cloud.") 