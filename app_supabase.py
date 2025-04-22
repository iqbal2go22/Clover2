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

# Display setup info
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

# Add simple buttons
if secrets_ok:
    if st.button("Initialize Database"):
        st.info("Database initialization will be implemented in the next update")
    
    if st.button("Sync Data"):
        st.info("Data synchronization will be implemented in the next update")

# Footer
st.markdown("---")
st.markdown("© 2024 Clover Executive Dashboard | Cloud Version")
st.info("This is a simplified version. Once we confirm it's stable, we'll add full functionality.") 