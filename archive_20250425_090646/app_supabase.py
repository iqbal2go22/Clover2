import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Clover Executive Dashboard",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# App title and description
st.title("📊 Clover Executive Dashboard")
st.write("Cloud version with Supabase database")

# IMPORTANT: Defer all module imports to functions that are called after user interaction
# This prevents initialization issues that can cause the app to hang

# DATABASE MANAGEMENT SECTION
st.markdown("---")
st.header("Database Setup")

# Check if secrets are configured
secrets_ok = False
if hasattr(st, 'secrets'):
    # Check for Supabase
    if 'supabase' in st.secrets and 'url' in st.secrets.supabase:
        st.success("✅ Supabase configuration found")
        secrets_ok = True
    else:
        st.error("❌ Supabase configuration missing")
    
    # Check for Stores
    store_count = 0
    for key in st.secrets:
        if key.startswith('store_'):
            store_count += 1
    
    if store_count > 0:
        st.success(f"✅ Found {store_count} store configurations")
    else:
        st.warning("⚠️ No store configurations found")
else:
    st.error("❌ No secrets configured")

# Always show the database initialization button
if st.button("Initialize Database Tables", key="init_db", type="primary"):
    try:
        # Import modules only when button is clicked
        import cloud_db_utils as db_utils
        st.success("✅ Successfully imported cloud_db_utils module")
        
        # Create database tables
        db_utils.create_database()
        st.success("✅ Database tables created successfully")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Always show the sync data button
if st.button("Sync Recent Data (Last 7 Days)", key="sync_data", type="primary"):
    try:
        # Import modules only when button is clicked
        import cloud_db_utils as db_utils
        import incremental_sync
        
        st.success("✅ Successfully imported required modules")
        st.info("Starting data synchronization...")
        
        # Get stores
        stores = db_utils.get_all_stores()
        if not stores.empty:
            st.write(f"Found {len(stores)} stores in database")
            st.success("Data sync will be implemented in the next update")
        else:
            st.warning("No stores found in database. Initialize database first.")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Add a button to check database connection without taking action
if st.button("Check Database Connection", key="check_connection"):
    try:
        import cloud_db_utils as db_utils
        st.success("✅ Successfully imported cloud_db_utils module")
        
        # Attempt to connect
        conn = db_utils.get_db_connection()
        st.success("✅ Successfully connected to database")
        conn.close()
    except Exception as e:
        st.error(f"❌ Connection error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("© 2024 Clover Executive Dashboard | Cloud Version")
st.info("This simplified version defers database operations until needed to prevent initialization issues.") 