"""
Simple command-line script to migrate data from SQLite to Supabase.
This script uses the REST API and does not require a direct PostgreSQL connection.
"""

import os
import sys
import sqlite3
import requests
import json
import pandas as pd
from datetime import datetime
import time
import toml

print("🔄 SQLite to Supabase Migration Tool")
print("This script will migrate data from SQLite to Supabase using the REST API.\n")

# Load connection details from secrets.toml
try:
    secrets_path = os.path.join('.streamlit', 'secrets.toml')
    secrets = toml.load(secrets_path)
    print(f"✅ Loaded secrets from {secrets_path}")
    
    supabase_admin = secrets.get('connections', {}).get('supabase_admin', {})
    project_url = supabase_admin.get('project_url', '')
    api_key = supabase_admin.get('api_key', '')
    
    if not project_url or not api_key:
        print("❌ Missing project_url or api_key in secrets.toml")
        sys.exit(1)
    
    masked_key = api_key[:10] + "..." + api_key[-5:] if len(api_key) > 15 else api_key
    print(f"Supabase URL: {project_url}")
    print(f"API Key: {masked_key}")
except Exception as e:
    print(f"❌ Error loading secrets: {str(e)}")
    sys.exit(1)

# Set up headers for Supabase REST API
headers = {
    "apikey": api_key,
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Define the SQLite database path
sqlite_db_path = "clover_dashboard.db"

# Check if SQLite database exists
if not os.path.exists(sqlite_db_path):
    print(f"❌ SQLite database not found at: {sqlite_db_path}")
    sys.exit(1)

# Test connection to Supabase
print("\nTesting connection to Supabase...")
try:
    response = requests.get(
        f"{project_url}/rest/v1/",
        headers=headers,
        timeout=10
    )
    if response.status_code == 200:
        print(f"✅ Connection successful! Status code: {response.status_code}")
    else:
        print(f"⚠️ Connection warning. Status code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
    sys.exit(1)

# Function to get data from SQLite
def get_sqlite_data(table_name):
    try:
        conn = sqlite3.connect(sqlite_db_path)
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        conn.close()
        print(f"✅ Read {len(df)} rows from SQLite table {table_name}")
        return df
    except Exception as e:
        print(f"❌ Error reading from SQLite table {table_name}: {str(e)}")
        return pd.DataFrame()

# Function to handle JSON serialization of data
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
    
    print(f"\nMigrating {table_name}: {len(records)} records in {len(batches)} batches")
    
    for batch_idx, batch in enumerate(batches):
        try:
            print(f"  Processing batch {batch_idx+1}/{len(batches)} ({len(batch)} records)...", end="")
            
            response = requests.post(
                f"{project_url}/rest/v1/{table_name}",
                headers=headers,
                json=batch,
                timeout=30
            )
            
            if response.status_code in (200, 201, 202, 204):
                rows_inserted += len(batch)
                print(f" ✅ Inserted successfully")
            else:
                print(f" ❌ Failed: Status {response.status_code}")
                print(f"    Error: {response.text[:200]}")
                
                # Try one by one as fallback
                print("    Trying one-by-one insertion as fallback...")
                single_success = 0
                
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
                            single_success += 1
                        
                        # Add a small delay to avoid overwhelming the API
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"    ❌ Error inserting single record: {str(e)}")
                
                print(f"    ✅ Inserted {single_success}/{len(batch)} records individually")
        
        except Exception as e:
            print(f" ❌ Error: {str(e)}")
    
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
        print(f"❌ Error counting records in {table_name}: {str(e)}")
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
        print(f"❌ Error checking if table {table_name} exists: {str(e)}")
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
        print(f"❌ Error adding sync log entry: {str(e)}")
        return False

# Main migration function
def migrate_data():
    # Tables to migrate
    tables = ['stores', 'payments', 'order_items', 'expenses', 'sync_log']
    
    total_rows_migrated = 0
    migration_results = []
    
    print("\n=== Starting Migration ===")
    
    for table in tables:
        print(f"\nMigrating table: {table}")
        
        # First check if table exists
        print(f"  Checking if table exists in Supabase...")
        if not check_table_exists(table):
            print(f"  ❌ Table {table} does not exist in Supabase")
            migration_results.append({"table": table, "rows": 0, "status": "Table not found"})
            continue
        
        # Get data from SQLite
        print(f"  Reading data from SQLite...")
        df = get_sqlite_data(table)
        
        if df.empty:
            print(f"  ⚠️ No data found in SQLite table")
            migration_results.append({"table": table, "rows": 0, "status": "No data"})
            continue
        
        # Check current count in Supabase
        print(f"  Checking current data in Supabase...")
        current_count = count_supabase_records(table)
        print(f"  Current row count in Supabase: {current_count}")
        
        # Insert data into Supabase
        print(f"  Inserting data into Supabase...")
        rows_inserted = insert_into_supabase(table, df)
        
        # Verify final count
        print(f"  Verifying migration...")
        final_count = count_supabase_records(table)
        print(f"  Final row count in Supabase: {final_count}")
        
        migration_results.append({
            "table": table, 
            "sqlite_rows": len(df),
            "inserted": rows_inserted,
            "final_count": final_count,
            "status": "Success" if rows_inserted > 0 else "Error"
        })
        
        total_rows_migrated += rows_inserted
        
        print(f"  ✅ Migrated {rows_inserted} rows into {table}")
    
    # Record migration in sync_log
    add_sync_log_entry("data_migration_simple")
    
    return total_rows_migrated, migration_results

# Run migration
total_migrated, results = migrate_data()

# Print summary
print("\n=== Migration Summary ===")
print(f"Total records migrated: {total_migrated}")

for result in results:
    print(f"{result['table']}:")
    print(f"  - SQLite rows: {result['sqlite_rows']}")
    print(f"  - Inserted: {result['inserted']}")
    print(f"  - Final count in Supabase: {result['final_count']}")
    print(f"  - Status: {result['status']}")

print("\n✅ Migration completed!")
print("\n🔍 Next Steps:")
print("1. Verify data in Supabase Table Editor or SQL Editor")
print("2. Test your app with the cloud_db_utils.py connection")
print("3. Deploy to Streamlit Cloud") 