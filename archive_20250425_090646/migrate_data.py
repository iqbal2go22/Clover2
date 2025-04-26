import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

st.title("SQLite to Supabase Data Migration")
st.write("This tool will migrate your data from SQLite to Supabase.")

# Get Supabase SQL connection
supabase_conn = st.connection("supabase_sql", type="sql")

# Define the SQLite database path
sqlite_db_path = "clover_dashboard.db"

# Check if SQLite database exists
if not os.path.exists(sqlite_db_path):
    st.error(f"❌ SQLite database not found at: {sqlite_db_path}")
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

# Function to insert data into Supabase
def insert_into_supabase(table_name, df):
    if df.empty:
        return 0
    
    # Handle datetime columns - convert to ISO format
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate SQL insert statements
    rows_inserted = 0
    
    for _, row in df.iterrows():
        try:
            # Build columns and values for the insert statement
            columns = ", ".join(row.index)
            placeholders = ", ".join(["%s" for _ in row.index])
            values = ", ".join([f"'{str(val).replace("'", "''")}'" if val is not None else "NULL" for val in row.values])
            
            # Create insert statement with ON CONFLICT DO NOTHING for safety
            insert_sql = f"""
            INSERT INTO {table_name} ({columns})
            VALUES ({values})
            ON CONFLICT DO NOTHING
            """
            
            # Execute the query
            supabase_conn.query(insert_sql)
            rows_inserted += 1
        except Exception as e:
            st.error(f"Error inserting row into {table_name}: {str(e)}")
            st.write(f"Problematic row: {row}")
    
    return rows_inserted

# Main migration function
def migrate_data():
    # Tables to migrate
    tables = ['stores', 'payments', 'order_items', 'expenses', 'sync_log']
    
    total_rows_migrated = 0
    migration_results = []
    
    for table in tables:
        with st.status(f"Migrating {table}..."):
            # Get data from SQLite
            st.write(f"Reading data from SQLite table: {table}")
            df = get_sqlite_data(table)
            
            if df.empty:
                st.write(f"No data found in SQLite table: {table}")
                migration_results.append({"table": table, "rows": 0, "status": "No data"})
                continue
            
            st.write(f"Found {len(df)} rows in SQLite table: {table}")
            
            # Insert data into Supabase
            st.write(f"Inserting data into Supabase table: {table}")
            rows_inserted = insert_into_supabase(table, df)
            
            st.write(f"Inserted {rows_inserted} rows into Supabase table: {table}")
            
            total_rows_migrated += rows_inserted
            migration_results.append({"table": table, "rows": rows_inserted, "status": "Success" if rows_inserted > 0 else "Error"})
    
    # Record migration in sync_log
    try:
        sync_time = datetime.now().isoformat()
        supabase_conn.query(f"INSERT INTO sync_log (sync_time, status) VALUES ('{sync_time}', 'data_migration')")
    except Exception as e:
        st.error(f"Error creating migration log: {str(e)}")
    
    return total_rows_migrated, migration_results

# UI
st.subheader("Migration Process")
st.info("""
This will copy all your data from the local SQLite database to Supabase.
Existing data in Supabase won't be affected (no duplicates will be created).
""")

if st.button("Start Migration", type="primary"):
    with st.spinner("Migrating data..."):
        total_migrated, results = migrate_data()
    
    if total_migrated > 0:
        st.success(f"🎉 Migration complete! {total_migrated} rows migrated.")
    else:
        st.warning("⚠️ Migration completed, but no rows were migrated.")
    
    st.subheader("Migration Results")
    st.dataframe(pd.DataFrame(results))
    
    # Check current data in Supabase
    st.subheader("Current Data in Supabase")
    
    tables_df = supabase_conn.query("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    if not tables_df.empty:
        for table in tables_df['table_name']:
            try:
                count_df = supabase_conn.query(f"SELECT COUNT(*) as count FROM {table}")
                st.write(f"{table}: {count_df.iloc[0]['count']} rows")
            except:
                st.write(f"{table}: Error counting rows")

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
    try:
        tables_df = supabase_conn.query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        if not tables_df.empty:
            st.success(f"Found {len(tables_df)} tables")
            for table in tables_df['table_name']:
                try:
                    count_df = supabase_conn.query(f"SELECT COUNT(*) as count FROM {table}")
                    st.write(f"{table}: {count_df.iloc[0]['count']} rows")
                except:
                    st.write(f"{table}: Error counting rows")
        else:
            st.warning("No tables found in Supabase")
    except Exception as e:
        st.error(f"Error querying Supabase: {str(e)}")

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