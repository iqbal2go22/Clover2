import streamlit as st
import pandas as pd
import sqlite3
import requests
import json
from datetime import datetime
import os
import time

st.title("SQLite to Supabase Migration (REST API)")
st.write("This tool will migrate your data from SQLite to Supabase using the REST API.")

# Define the SQLite database path
sqlite_db_path = "clover_dashboard.db"

# Check if SQLite database exists
if not os.path.exists(sqlite_db_path):
    st.error(f"❌ SQLite database not found at: {sqlite_db_path}")
    st.stop()

# Get Supabase connection details from secrets
try:
    project_url = st.secrets.connections.supabase_admin.get("project_url")
    api_key = st.secrets.connections.supabase_admin.get("api_key")
    
    # Set up headers for Supabase REST API
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    st.success("✅ Loaded Supabase connection details")
except Exception as e:
    st.error(f"❌ Error loading Supabase secrets: {str(e)}")
    st.stop()

# Function to get data from SQLite
def get_sqlite_data(table_name):
    try:
        conn = sqlite3.connect(sqlite_db_path)
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error reading from SQLite table {table_name}: {str(e)}")
        return pd.DataFrame()

# Helper function to convert datetime to ISO format string
def prepare_data_for_json(df):
    df_copy = df.copy()
    
    for col in df_copy.columns:
        # Convert datetime columns to ISO format strings
        if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Handle NaN and None values
        df_copy[col] = df_copy[col].apply(lambda x: None if pd.isna(x) else x)
    
    return df_copy

# Function to insert data into Supabase using REST API
def insert_into_supabase(table_name, df, batch_size=25):
    if df.empty:
        return 0
    
    # Prepare data for JSON serialization
    df_prepared = prepare_data_for_json(df)
    records = df_prepared.to_dict('records')
    
    # Insert in batches
    rows_inserted = 0
    batches = [records[i:i+batch_size] for i in range(0, len(records), batch_size)]
    
    # Create progress bar OUTSIDE the loop - FIX for the None error
    progress_bar = st.progress(0.0)
    st.write(f"Migrating {len(records)} records in {len(batches)} batches")
    
    for batch_idx, batch in enumerate(batches):
        try:
            # Update progress display - now we're sure progress_bar exists
            progress_bar.progress((batch_idx + 1) / len(batches), 
                                 text=f"Processing batch {batch_idx+1}/{len(batches)}")
            
            response = requests.post(
                f"{project_url}/rest/v1/{table_name}",
                headers=headers,
                json=batch,
                timeout=30
            )
            
            if response.status_code in (200, 201, 202, 204):
                rows_inserted += len(batch)
                st.write(f"✅ Batch {batch_idx+1}/{len(batches)}: Inserted {len(batch)} rows successfully")
            else:
                st.error(f"❌ Batch {batch_idx+1}/{len(batches)}: Failed to insert {len(batch)} rows")
                st.write(f"Status code: {response.status_code}")
                st.write(f"Response: {response.text[:500]}")
                
                # Try one by one as fallback
                st.write("Trying one-by-one insertion as fallback...")
                for record in batch:
                    try:
                        single_response = requests.post(
                            f"{project_url}/rest/v1/{table_name}",
                            headers=headers,
                            json=record,
                            timeout=10
                        )
                        
                        if single_response.status_code in (200, 201, 202, 204):
                            rows_inserted += 1
                        else:
                            st.write(f"❌ Failed to insert record: {single_response.status_code}")
                    except Exception as e:
                        st.write(f"❌ Error inserting single record: {str(e)}")
                    
                    # Add a small delay to avoid overwhelming the API
                    time.sleep(0.1)
        
        except Exception as e:
            st.error(f"❌ Error processing batch {batch_idx+1}: {str(e)}")
    
    # Set progress to complete
    progress_bar.progress(1.0, text="Complete")
    
    return rows_inserted

# Function to count records in Supabase table using REST API
def count_supabase_records(table_name):
    try:
        response = requests.get(
            f"{project_url}/rest/v1/{table_name}?select=count",
            headers={**headers, "Prefer": "count=exact"},
            timeout=10
        )
        
        if "content-range" in response.headers:
            count = response.headers["content-range"].split("/")[1]
            return int(count)
        return 0
    except Exception as e:
        st.error(f"Error counting records in {table_name}: {str(e)}")
        return 0

# Function to check if a table exists in Supabase
def check_table_exists(table_name):
    try:
        response = requests.get(
            f"{project_url}/rest/v1/{table_name}?limit=1",
            headers=headers,
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error checking if table {table_name} exists: {str(e)}")
        return False

# Function to add entry to sync_log
def add_sync_log_entry(status):
    try:
        sync_time = datetime.now().isoformat()
        response = requests.post(
            f"{project_url}/rest/v1/sync_log",
            headers=headers,
            json={"sync_time": sync_time, "status": status},
            timeout=10
        )
        return response.status_code in (200, 201, 202, 204)
    except Exception as e:
        st.error(f"Error adding sync log entry: {str(e)}")
        return False

# Main migration function
def migrate_data():
    # Tables to migrate
    tables = ['stores', 'payments', 'order_items', 'expenses', 'sync_log']
    
    total_rows_migrated = 0
    migration_results = []
    
    for table in tables:
        with st.status(f"Migrating {table}...") as status:
            # First check if table exists
            status.update(label=f"Checking if table {table} exists in Supabase...")
            if not check_table_exists(table):
                st.error(f"❌ Table {table} does not exist in Supabase")
                migration_results.append({"table": table, "rows": 0, "status": "Table not found"})
                continue
                
            # Get data from SQLite
            status.update(label=f"Reading data from SQLite table: {table}")
            df = get_sqlite_data(table)
            
            if df.empty:
                st.warning(f"⚠️ No data found in SQLite table: {table}")
                migration_results.append({"table": table, "rows": 0, "status": "No data"})
                continue
                
            st.write(f"Found {len(df)} rows in SQLite table: {table}")
            
            # Check current count in Supabase
            status.update(label=f"Checking current data in Supabase table: {table}")
            current_count = count_supabase_records(table)
            st.write(f"Current row count in Supabase table {table}: {current_count}")
            
            # Insert data into Supabase
            status.update(label=f"Inserting data into Supabase table: {table}")
            rows_inserted = insert_into_supabase(table, df)
            
            # Verify final count
            status.update(label=f"Verifying migration for table: {table}")
            final_count = count_supabase_records(table)
            st.write(f"Final row count in Supabase table {table}: {final_count}")
            
            status.update(label=f"Migrated {rows_inserted} rows into {table}", state="complete")
            
            total_rows_migrated += rows_inserted
            migration_results.append({
                "table": table,
                "sqlite_rows": len(df),
                "inserted": rows_inserted,
                "final_count": final_count,
                "status": "Success" if rows_inserted > 0 else "Error"
            })
    
    # Record migration in sync_log
    add_sync_log_entry("data_migration_rest_api")
    
    return total_rows_migrated, migration_results

# UI
st.subheader("Migration Process")
st.info("""
This will copy all your data from the local SQLite database to Supabase using the REST API.
Existing data in Supabase won't be affected (no duplicates will be created).
""")

# IMPORTANT: Only run migrate_data when button is clicked
if st.button("Start Migration", type="primary"):
    with st.spinner("Migrating data..."):
        total_migrated, results = migrate_data()
    
        if total_migrated > 0:
            st.success(f"🎉 Migration complete! {total_migrated} rows migrated.")
        else:
            st.warning("⚠️ Migration completed, but no rows were migrated.")
    
        st.subheader("Migration Results")
        st.dataframe(pd.DataFrame(results))

# Database status
st.subheader("Database Status")
col1, col2 = st.columns(2)

with col1:
    st.write("SQLite Database")
    if os.path.exists(sqlite_db_path):
        try:
            conn = sqlite3.connect(sqlite_db_path)
            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
            conn.close()
            
            st.success(f"Found {len(tables)} tables")
            for table in tables['name']:
                df = get_sqlite_data(table)
                st.write(f"{table}: {len(df)} rows")
        except Exception as e:
            st.error(f"Error reading SQLite database: {str(e)}")
    else:
        st.error("SQLite database not found")

with col2:
    st.write("Supabase Database")
    tables = ['stores', 'payments', 'order_items', 'expenses', 'sync_log']
    tables_checked = 0
    
    for table in tables:
        if check_table_exists(table):
            tables_checked += 1
            count = count_supabase_records(table)
            st.write(f"{table}: {count} rows")
    
    if tables_checked > 0:
        st.success(f"Found {tables_checked} tables in Supabase")
    else:
        st.warning("No tables found in Supabase")

# Test connection section
st.subheader("Test Supabase Connection")
if st.button("Test Connection"):
    try:
        response = requests.get(
            f"{project_url}/rest/v1/",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            st.success(f"✅ Connection successful! Status code: {response.status_code}")
        else:
            st.warning(f"⚠️ Connection warning. Status code: {response.status_code}")
            st.write(f"Response: {response.text[:200]}")
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)}")

# Final instructions
st.markdown("---")
st.markdown("""
### Next Steps

After migration is complete:

1. **Verify your data**: Check that all your data has been migrated correctly.
2. **Update your app**: Ensure your app is using the `cloud_db_utils.py` module for database operations.
3. **Deploy to Streamlit Cloud**: Push your code to GitHub and deploy using Streamlit Cloud.
4. **Set up secrets**: Add your Supabase connection information to Streamlit Cloud secrets.

Need help? Check the `README_SUPABASE.md` file for detailed instructions.
""") 