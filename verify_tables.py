import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Supabase Table Verification", layout="wide")
st.title("🔍 Supabase Table Verification")
st.write("This tool verifies that all necessary tables exist in your Supabase database")

def get_supabase_client():
    """Get Supabase connection details from secrets"""
    try:
        # Get connection details from secrets
        if hasattr(st, 'secrets') and 'connections' in st.secrets and 'supabase' in st.secrets.connections:
            project_url = st.secrets.connections.supabase.get("project_url")
            api_key = st.secrets.connections.supabase.get("api_key")
            st.write("✅ Using connections.supabase format")
        else:
            # Fallback to older format
            project_url = st.secrets.supabase.url if hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase') and hasattr(st.secrets.supabase, 'url') else None
            api_key = st.secrets.supabase.api_key if hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase') and hasattr(st.secrets.supabase, 'api_key') else None
            
            # Second fallback for key names
            if not api_key and hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase') and hasattr(st.secrets.supabase, 'key'):
                api_key = st.secrets.supabase.key
                
            st.write("✅ Using direct supabase format")
        
        if not project_url or not api_key:
            st.error("Supabase connection details not found in Streamlit secrets")
            return None
        
        # Set up headers for Supabase REST API
        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        client = {
            "project_url": project_url,
            "headers": headers
        }
        
        # Test connection with a simple request
        test_url = f"{project_url}/rest/v1/?apikey={api_key}"
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        st.success(f"✅ Supabase connection successful!")
        return client
        
    except Exception as e:
        st.error(f"❌ Supabase connection failed: {str(e)}")
        return None

def verify_table(client, table_name):
    """Verify that a table exists by querying it"""
    try:
        url = f"{client['project_url']}/rest/v1/{table_name}?limit=1"
        response = requests.get(url, headers=client["headers"], timeout=10)
        
        if response.status_code == 200:
            st.success(f"✅ Table '{table_name}' exists")
            
            # Check if we can get column information
            try:
                # If response is an array, it might have data
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    columns = list(data[0].keys())
                    st.write(f"Columns: {', '.join(columns)}")
                    # Show sample data if available
                    st.write("Sample data:")
                    st.dataframe(pd.DataFrame(data))
                else:
                    st.info("Table exists but is empty")
            except:
                st.info("Table exists but couldn't parse structure")
            
            return True
        else:
            st.error(f"❌ Table '{table_name}' does not exist (Status code: {response.status_code})")
            response_text = response.text if hasattr(response, 'text') else "No response text"
            st.write(f"Response: {response_text}")
            return False
    except Exception as e:
        st.error(f"❌ Error verifying table '{table_name}': {str(e)}")
        return False

# The main tables to check
required_tables = [
    "stores", 
    "payments", 
    "order_items", 
    "expenses", 
    "sync_log"
]

# Main execution
supabase_client = get_supabase_client()

if not supabase_client:
    st.stop()

# Add option to check specific table
selected_table = st.selectbox(
    "Select a table to check",
    ["All Tables"] + required_tables
)

if st.button("Verify Tables"):
    with st.spinner("Checking tables..."):
        results = {}
        
        if selected_table == "All Tables":
            # Check all required tables
            for table in required_tables:
                st.subheader(f"Checking table: {table}")
                results[table] = verify_table(supabase_client, table)
                st.divider()
            
            # Final summary
            success_count = sum(1 for result in results.values() if result)
            if success_count == len(required_tables):
                st.success(f"✅ All {len(required_tables)} tables exist!")
            else:
                st.warning(f"⚠️ Only {success_count} out of {len(required_tables)} tables were found.")
        else:
            # Check just the selected table
            st.subheader(f"Checking table: {selected_table}")
            verify_table(supabase_client, selected_table) 