import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import cloud_db_utils as db

st.title("Cloud DB Utilities Test")

# Test SQL connection
try:
    conn = st.connection("supabase_sql", type="sql")
    st.success("✅ SQL Connection initialized")
    
    # Display PostgreSQL version
    with st.expander("Database Version"):
        try:
            df = conn.query("SELECT version();")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error querying version: {str(e)}")
    
    # Test stores retrieval
    if st.button("Test Get All Stores"):
        with st.spinner("Fetching stores..."):
            stores_df = db.get_all_stores()
            if not stores_df.empty:
                st.success(f"✅ Found {len(stores_df)} stores!")
                st.dataframe(stores_df)
            else:
                st.warning("No stores found or error occurred.")
    
    # Test store by ID retrieval
    with st.expander("Get Store by ID"):
        store_id = st.text_input("Enter Store ID", "4VZSM7038BKQ1")
        if st.button("Fetch Store"):
            store = db.get_store_by_id(store_id)
            if store:
                st.success(f"✅ Found store: {store.get('name', 'Unknown')}")
                st.json(store)
            else:
                st.warning(f"Store with ID {store_id} not found.")
    
    # Test orders retrieval
    with st.expander("Get Orders by Date Range"):
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        store_filter = st.checkbox("Filter by Store")
        filter_id = None
        if store_filter:
            filter_id = st.text_input("Store ID", "4VZSM7038BKQ1")
        
        if st.button("Fetch Orders"):
            with st.spinner("Fetching orders..."):
                orders_df = db.get_orders_by_date_range(start_date, end_date, filter_id if store_filter else None)
                if not orders_df.empty:
                    st.success(f"✅ Found {len(orders_df)} orders!")
                    st.dataframe(orders_df)
                else:
                    st.warning("No orders found for the selected date range.")
    
    # Test expenses
    with st.expander("Expenses"):
        exp_tab1, exp_tab2 = st.tabs(["View Expenses", "Add Expense"])
        
        with exp_tab1:
            exp_store_id = st.text_input("Store ID for Expenses", "4VZSM7038BKQ1")
            if st.button("Get Expenses"):
                expenses_df = db.get_store_expenses(exp_store_id)
                if not expenses_df.empty:
                    st.success(f"✅ Found {len(expenses_df)} expenses!")
                    st.dataframe(expenses_df)
                else:
                    st.info("No expenses found for this store.")
        
        with exp_tab2:
            add_store_id = st.text_input("Store ID", "4VZSM7038BKQ1", key="add_exp_store")
            add_date = st.date_input("Expense Date", datetime.now())
            add_amount = st.number_input("Amount", min_value=0.01, value=100.00, step=10.0)
            add_category = st.selectbox("Category", ["Rent", "Utilities", "Supplies", "Payroll", "Other"])
            add_description = st.text_area("Description", "Test expense")
            
            if st.button("Add Expense"):
                if db.add_expense(add_store_id, add_date, add_amount, add_category, add_description):
                    st.success("✅ Expense added successfully!")
                else:
                    st.error("Failed to add expense.")
    
    # Test sync log
    with st.expander("Sync Log"):
        if st.button("Get Last Sync Time"):
            last_sync = db.get_last_sync_time()
            if last_sync:
                st.success(f"✅ Last sync: {last_sync}")
            else:
                st.info("No sync log found.")
        
        if st.button("Add Sync Log Entry"):
            if db.update_sync_log():
                st.success("✅ Sync log updated!")
            else:
                st.error("Failed to update sync log.")
    
    # Test raw query
    with st.expander("Raw SQL Query"):
        query = st.text_area("SQL Query", "SELECT COUNT(*) as order_count FROM order_items;")
        if st.button("Execute Query"):
            try:
                result = db.execute_raw_query(query)
                st.success("Query executed successfully!")
                st.dataframe(result)
            except Exception as e:
                st.error(f"Query error: {str(e)}")

except Exception as e:
    st.error(f"❌ Connection failed: {str(e)}")
    st.info("""
    Make sure your secrets.toml file contains the proper connection configuration:
    
    [connections.supabase_sql]
    type = "postgresql"
    url = "your_postgresql_connection_string"
    """) 