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

# If we couldn't import the module, show a clear error
if not db_utils:
    st.warning("The app cannot continue without required modules.")
    st.info("Please check that all required Python modules are installed.")
    st.stop()  # Stop execution to prevent further errors

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

# Only attempt to use database if secrets are configured
if secrets_ok:
    # Safely try to connect to the database
    try:
        conn = db_utils.get_db_connection()
        st.success("✅ Successfully connected to Supabase database")
        
        # Add button to initialize database
        if st.button("Initialize Database"):
            try:
                db_utils.create_database()
                st.success("✅ Database tables created successfully")
            except Exception as e:
                st.error(f"❌ Error creating database tables: {str(e)}")
        
        # Get stores from database to see if we have any
        try:
            stores = db_utils.get_all_stores()
            if not stores.empty:
                st.success(f"✅ Found {len(stores)} stores in database")
                
                # Add button to sync data
                if st.button("Sync Data"):
                    st.info("Data synchronization will be implemented soon")
            else:
                st.warning("No stores found in database. Try initializing the database first.")
        except Exception as e:
            st.error(f"❌ Error getting stores: {str(e)}")
        
        conn.close()
    except Exception as e:
        st.error(f"❌ Error connecting to database: {str(e)}")
        st.info("Please check your database credentials in the secrets configuration.")

# Footer
st.markdown("---")
st.markdown("© 2024 Clover Executive Dashboard | Cloud Version")
st.info("This is a simplified version. Once we confirm it's stable, we'll add full functionality.") 