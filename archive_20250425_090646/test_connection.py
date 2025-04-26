import streamlit as st
import pandas as pd
from datetime import datetime

st.title("Supabase Connection Test")
st.write("This tool tests the direct SQL connection to Supabase.")

conn = st.connection("supabase_sql", type="sql")

# Test basic connection
try:
    with st.spinner("Testing basic connection..."):
        df = conn.query("SELECT 1 as connection_test")
    
    if not df.empty and df.iloc[0][0] == 1:
        st.success("✅ Basic connection succeeded!")
    else:
        st.error("❌ Basic connection test failed!")
except Exception as e:
    st.error(f"❌ Connection error: {str(e)}")
    st.info("""
    Troubleshooting tips:
    - Make sure your Supabase project is active (not paused)
    - Check that your database password is correct
    - Verify that your IP is not blocked by Supabase
    - Try using port 5432 instead of 6543 for direct connection
    """)

# Display connection details
st.subheader("Connection Details")
with st.expander("Show details"):
    try:
        # Mask sensitive information
        if hasattr(st, 'secrets') and 'connections' in st.secrets and 'supabase_sql' in st.secrets.connections:
            url = st.secrets.connections.supabase_sql.get("url", "")
            masked_url = url.split("@")[1] if "@" in url else ""
            st.write(f"Connection URL: ...@{masked_url}")
    except:
        st.write("Could not display connection details.")

# Test listing tables
st.subheader("Database Tables")
try:
    tables_df = conn.query("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    if not tables_df.empty:
        st.success(f"Found {len(tables_df)} tables")
        st.dataframe(tables_df)
        
        # Get row counts
        counts = []
        for table in tables_df['table_name']:
            try:
                count_df = conn.query(f"SELECT COUNT(*) as count FROM {table}")
                count = count_df.iloc[0]['count'] if not count_df.empty else 0
                counts.append({"table": table, "row_count": count})
            except:
                counts.append({"table": table, "row_count": "Error"})
        
        st.write("Row counts:")
        st.dataframe(pd.DataFrame(counts))
    else:
        st.warning("No tables found. You may need to run setup_supabase_db.py first.")
except Exception as e:
    st.error(f"Error listing tables: {str(e)}")

# Run a simple query if stores table exists
st.subheader("Sample Query")
if 'tables_df' in locals() and not tables_df.empty and 'stores' in tables_df['table_name'].values:
    try:
        stores_df = conn.query("SELECT * FROM stores LIMIT 10")
        if not stores_df.empty:
            st.success(f"Found {len(stores_df)} stores")
            st.dataframe(stores_df)
        else:
            st.info("Stores table exists but has no data")
    except Exception as e:
        st.error(f"Error querying stores: {str(e)}")
else:
    st.info("Stores table not found")

# Test inserting and querying data
st.subheader("Test Data Operations")
with st.expander("Test write operations"):
    st.write("This will test inserting a test expense and then reading it back")
    
    if st.button("Run Test", key="test_write"):
        try:
            # Insert a test expense
            test_desc = f"Test expense {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            test_date = datetime.now().isoformat()
            
            insert_query = f"""
            INSERT INTO expenses (store_id, date, amount, category, description, created_at)
            VALUES ('TEST', '{test_date}'::date, 0.01, 'Test', '{test_desc}', '{test_date}')
            RETURNING id
            """
            
            with st.spinner("Inserting test data..."):
                result = conn.query(insert_query)
            
            if not result.empty:
                expense_id = result.iloc[0][0]
                st.success(f"✅ Test data inserted successfully with ID: {expense_id}")
                
                # Query it back
                read_query = f"SELECT * FROM expenses WHERE id = {expense_id}"
                read_result = conn.query(read_query)
                
                if not read_result.empty:
                    st.success("✅ Successfully read back test data")
                    st.dataframe(read_result)
                    
                    # Clean up test data
                    delete_query = f"DELETE FROM expenses WHERE id = {expense_id}"
                    conn.query(delete_query)
                    st.success("✅ Test data cleaned up")
                else:
                    st.error("❌ Could not read back the test data")
            else:
                st.error("❌ Failed to insert test data")
        except Exception as e:
            st.error(f"❌ Test failed: {str(e)}")

# Display help info
st.markdown("---")
st.markdown("""
### Troubleshooting Connection Issues

If you're having connection problems:

1. **Check Supabase Status**: Make sure your project is active
2. **Verify Credentials**: Check that your connection URL is correct
3. **Try Direct Connection**: Use port 5432 instead of 6543
4. **Check Network**: Make sure your network allows outbound connections to Supabase

If you still have issues, you can try running:
```python
streamlit run setup_supabase_db.py
```
to set up your database tables.
""") 