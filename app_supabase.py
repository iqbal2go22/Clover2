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

# Simple error handler for imports
def safe_import(module_name):
    try:
        module = __import__(module_name)
        st.success(f"✅ Successfully imported {module_name}")
        return module
    except Exception as e:
        st.error(f"❌ Error importing {module_name}: {str(e)}")
        return None

# Check if we can import needed modules
db_utils = safe_import("cloud_db_utils")

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

# DATABASE MANAGEMENT SECTION
st.markdown("---")
st.header("Database Management")
st.markdown("Use these controls to set up and manage your database:")

# Always show the database initialization button
initialize_button = st.button("Initialize Database Tables", key="init_db", type="primary")
if initialize_button:
    if db_utils:
        try:
            db_utils.create_database()
            st.success("✅ Database tables created successfully")
        except Exception as e:
            st.error(f"❌ Error creating database tables: {str(e)}")
    else:
        st.error("❌ Cannot initialize database - module not loaded")

# Always show the sync data button
sync_button = st.button("Sync Recent Data (Last 7 Days)", key="sync_data", type="primary")
if sync_button:
    if db_utils:
        try:
            import incremental_sync
            st.success("✅ Successfully imported incremental_sync module")
            st.info("Starting data synchronization...")
            
            # Getting stores
            stores = db_utils.get_all_stores()
            if not stores.empty:
                st.write(f"Found {len(stores)} stores in database")
                # You would normally sync data here
                st.success("Data sync would happen here!")
            else:
                st.warning("No stores found in database. Initialize database first.")
                
        except Exception as e:
            st.error(f"❌ Error during sync: {str(e)}")
    else:
        st.error("❌ Cannot sync data - module not loaded")

# DIAGNOSTICS SECTION
st.markdown("---")
st.header("Connection Diagnostics")

# Try to connect to the database and show status
if db_utils:
    try:
        st.write("Attempting to connect to database...")
        conn = db_utils.get_db_connection()
        st.success("✅ Successfully connected to Supabase database")
        
        # Get stores from database
        try:
            stores = db_utils.get_all_stores()
            if not stores.empty:
                st.success(f"✅ Found {len(stores)} stores in database")
                
                # Show store details
                st.write("Store details:")
                for _, store in stores.iterrows():
                    st.write(f"- {store['name']} (ID: {store['id']})")
            else:
                st.warning("No stores found in database. Try initializing the database first.")
        except Exception as e:
            st.error(f"❌ Error getting stores: {str(e)}")
        
        conn.close()
    except Exception as e:
        st.error(f"❌ Error connecting to database: {str(e)}")
        st.info("Please check your database credentials in the secrets configuration.")
else:
    st.error("❌ Cannot connect to database - module not loaded")

# Footer
st.markdown("---")
st.markdown("© 2024 Clover Executive Dashboard | Cloud Version")
st.info("This is a simplified version. Once we confirm it's stable, we'll add full functionality.") 