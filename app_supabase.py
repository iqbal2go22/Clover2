import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

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

# Create tabs
setup_tab, dashboard_tab = st.tabs(["Setup & Configuration", "Dashboard"])

with setup_tab:
    st.header("Database Setup")
    
    # Check if secrets are configured
    secrets_status = []
    
    if hasattr(st, 'secrets'):
        # Check for Supabase
        if 'supabase' in st.secrets and 'url' in st.secrets.supabase:
            secrets_status.append(("✅ Supabase configuration", True))
        else:
            secrets_status.append(("❌ Supabase configuration missing", False))
        
        # Check for Stores
        store_count = 0
        for key in st.secrets:
            if key.startswith('store_') and 'name' in st.secrets[key]:
                store_count += 1
        
        if store_count > 0:
            secrets_status.append((f"✅ Found {store_count} stores in configuration", True))
        else:
            secrets_status.append(("❌ No store configurations found", False))
    else:
        secrets_status.append(("❌ No secrets configured", False))
    
    # Display secrets status
    for message, status in secrets_status:
        if status:
            st.success(message)
        else:
            st.error(message)
    
    # Import cloud_db_utils
    try:
        import cloud_db_utils as db_utils
        st.success("✅ Successfully imported cloud_db_utils module")
        
        # Test database connection
        try:
            conn = db_utils.get_db_connection()
            st.success("✅ Successfully connected to Supabase database")
            conn.close()
            
            # Add button to initialize database
            if st.button("Initialize Database Tables"):
                try:
                    db_utils.create_database()
                    st.success("✅ Database tables created successfully")
                except Exception as e:
                    st.error(f"❌ Error creating database tables: {str(e)}")
            
            # Add button to sync data
            if store_count > 0:
                if st.button("Sync Recent Data (Last 7 Days)"):
                    try:
                        import incremental_sync
                        today = datetime.now().date()
                        start_date = today - timedelta(days=7)
                        
                        # Get stores from the database
                        try:
                            stores = db_utils.get_all_stores()
                            if not stores.empty:
                                progress_bar = st.progress(0)
                                for i, (_, store) in enumerate(stores.iterrows()):
                                    st.write(f"Syncing {store['name']}...")
                                    incremental_sync.sync_store_data(
                                        store['id'], 
                                        store['merchant_id'], 
                                        store['access_token'], 
                                        start_date
                                    )
                                    progress_bar.progress((i + 1) / len(stores))
                                st.success("✅ Data sync completed!")
                            else:
                                st.warning("No stores found in database. Please run 'Initialize Database' first.")
                        except Exception as e:
                            st.error(f"❌ Error getting stores: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Error syncing data: {str(e)}")
        except Exception as e:
            st.error(f"❌ Error connecting to database: {str(e)}")
            st.write("Please check your database credentials in the secrets configuration.")
    except Exception as e:
        st.error(f"❌ Error importing cloud_db_utils: {str(e)}")

with dashboard_tab:
    st.header("Dashboard")
    st.write("Switch to this tab after completing setup to view your dashboard.")
    
    # Check if we have database access before trying to load dashboard
    try:
        import cloud_db_utils as db_utils
        
        # Try to get stores to see if database is set up
        try:
            stores = db_utils.get_all_stores()
            if not stores.empty:
                # Date range selection
                col1, col2 = st.columns(2)
                with col1:
                    view = st.radio("Date Range", ["Today", "Last 7 Days", "This Month", "Custom"])
                
                with col2:
                    today = datetime.now().date()
                    if view == "Today":
                        start_date = today
                        end_date = today
                    elif view == "Last 7 Days":
                        start_date = today - timedelta(days=7)
                        end_date = today
                    elif view == "This Month":
                        start_date = datetime(today.year, today.month, 1).date()
                        end_date = today
                    elif view == "Custom":
                        col1, col2 = st.columns(2)
                        with col1:
                            start_date = st.date_input("Start Date", today - timedelta(days=7))
                        with col2:
                            end_date = st.date_input("End Date", today)
                
                st.write(f"Showing data from {start_date} to {end_date}")
                
                # Display a loading message
                with st.spinner("Loading dashboard data..."):
                    st.write("Dashboard will appear here once data is loaded.")
                    
                    # In a real implementation, you would call functions to:
                    # 1. Query the database for metrics within the date range
                    # 2. Create visualizations of the data
                    # 3. Display the results in the dashboard
                    
                    # For demonstration purposes, we'll just create placeholders
                    st.subheader("Summary Metrics")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Sales", "$0.00")
                    with col2:
                        st.metric("Total Orders", "0")
                    with col3:
                        st.metric("Average Order", "$0.00")
                    
                    # Store comparison placeholder
                    st.subheader("Store Comparison")
                    st.info("Once your data is synced, store comparison charts will appear here.")
            else:
                st.warning("No stores found in database. Please go to the Setup tab and initialize the database first.")
        except Exception as e:
            st.error(f"Error getting stores: {str(e)}")
            st.info("Please go to the Setup tab and initialize the database first.")
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

# Footer
st.markdown("---")
st.markdown("© 2024 Clover Executive Dashboard | Cloud Version")
st.info("This is the initial version of the cloud dashboard. For full functionality, please complete the setup process.") 