import os
import sys
import sqlite3
import requests
import json
import toml
from datetime import datetime

print("🔄 SQLite to Supabase Migration Tool")
print("This script will migrate data from SQLite to Supabase.\n")

# Load credentials from secrets.toml
secrets_path = os.path.join('.streamlit', 'secrets.toml')
try:
    secrets = toml.load(secrets_path)
    print(f"✅ Loaded secrets from {secrets_path}")
except Exception as e:
    print(f"❌ Failed to load secrets: {str(e)}")
    print(f"Make sure {secrets_path} exists and contains the required credentials.")
    sys.exit(1)

# Get SQLite path
sqlite_config = secrets.get('connections', {}).get('sqlite', {})
if not sqlite_config:
    print("❌ SQLite connection details not found in secrets.toml")
    sys.exit(1)

sqlite_path = sqlite_config.get('path', '')
if not sqlite_path:
    print("❌ SQLite path not found in secrets.toml")
    sys.exit(1)

print(f"SQLite DB path: {sqlite_path}")

# Check if the SQLite file exists
if not os.path.exists(sqlite_path):
    print(f"❌ SQLite database file not found at {sqlite_path}")
    sys.exit(1)

# Get Supabase admin connection details
supabase_admin = secrets.get('connections', {}).get('supabase_admin', {})
if not supabase_admin:
    print("❌ Supabase admin connection details not found in secrets.toml")
    sys.exit(1)

project_url = supabase_admin.get('project_url', '')
api_key = supabase_admin.get('api_key', '')

if not project_url or not api_key:
    print("❌ Missing project_url or api_key in secrets.toml")
    sys.exit(1)

print(f"Supabase URL: {project_url}")
masked_key = api_key[:10] + "..." + api_key[-5:] if len(api_key) > 15 else api_key
print(f"API Key: {masked_key}")

# Set up headers for Supabase REST API
headers = {
    "apikey": api_key,
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Helper function to convert SQLite Row to a regular dict
def dict_from_row(row):
    """Convert a sqlite3.Row to a regular dictionary"""
    if row is None:
        return {}
    return {key: row[key] for key in row.keys()}

# Test connection to Supabase
print("\nTesting connection to Supabase...")
try:
    response = requests.get(
        f"{project_url}/rest/v1/",
        headers=headers,
        timeout=10
    )
    if response.status_code == 200:
        print(f"✅ Supabase connection successful! Status code: {response.status_code}")
    else:
        print(f"⚠️ Supabase connection warning. Status code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Supabase connection failed: {str(e)}")
    sys.exit(1)

# Connect to SQLite database
print("\nConnecting to SQLite database...")
try:
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row  # This enables column access by name
    print("✅ SQLite connection successful!")
except Exception as e:
    print(f"❌ SQLite connection failed: {str(e)}")
    sys.exit(1)

# Migration function
def migrate_table(table_name, id_column='id', batch_size=50, exclude_columns=None):
    if exclude_columns is None:
        exclude_columns = []
    
    cursor = sqlite_conn.cursor()
    
    # Get total count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_records = cursor.fetchone()[0]
    print(f"\nMigrating {table_name}: {total_records} records")
    
    if total_records == 0:
        print(f"ℹ️ No records to migrate in {table_name}")
        return 0
    
    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall() if column[1] not in exclude_columns]
    columns_str = ', '.join(columns)
    
    # Fetch all records and insert into Supabase in batches
    cursor.execute(f"SELECT {columns_str} FROM {table_name}")
    
    success_count = 0
    error_count = 0
    batch_count = 0
    
    records = cursor.fetchall()
    
    for start_idx in range(0, len(records), batch_size):
        batch = records[start_idx:start_idx + batch_size]
        batch_count += 1
        
        # Convert SQLite Row objects to regular dictionaries
        batch_data = []
        for record in batch:
            # Convert SQLite row to dict explicitly
            row_dict = dict_from_row(record)
            batch_data.append(row_dict)
        
        # Insert batch into Supabase
        try:
            response = requests.post(
                f"{project_url}/rest/v1/{table_name}",
                headers=headers,
                json=batch_data,
                timeout=30
            )
            
            if response.status_code in (200, 201, 202, 204):
                success_count += len(batch)
                print(f"✅ Batch {batch_count}: Inserted {len(batch)} records successfully")
            else:
                error_count += len(batch)
                print(f"❌ Batch {batch_count}: Failed to insert {len(batch)} records. Status: {response.status_code}")
                print(f"Error: {response.text[:200]}...")
                
                # Try sending one by one
                print("Trying to insert records one by one...")
                for record in batch:
                    try:
                        # Convert SQLite row to dict explicitly
                        record_dict = dict_from_row(record)
                        
                        single_response = requests.post(
                            f"{project_url}/rest/v1/{table_name}",
                            headers=headers,
                            json=record_dict,
                            timeout=10
                        )
                        
                        if single_response.status_code in (200, 201, 202, 204):
                            success_count += 1
                            error_count -= 1
                        else:
                            print(f"  ❌ Failed to insert record with {id_column}={record_dict.get(id_column, 'unknown')}")
                            print(f"  Error: {single_response.text[:100]}...")
                    except Exception as e:
                        print(f"  ❌ Error inserting single record: {str(e)}")
        
        except Exception as e:
            error_count += len(batch)
            print(f"❌ Batch {batch_count}: Error: {str(e)}")
    
    # Verify migration
    try:
        # Check count in Supabase
        verify_response = requests.get(
            f"{project_url}/rest/v1/{table_name}?select=count",
            headers={**headers, "Prefer": "count=exact"},
            timeout=10
        )
        
        if "content-range" in verify_response.headers:
            supabase_count = int(verify_response.headers["content-range"].split("/")[1])
            print(f"Verification: Supabase has {supabase_count} records of {total_records} from SQLite")
            
            if supabase_count >= total_records:
                print(f"✅ Table '{table_name}' migration complete and verified!")
            else:
                print(f"⚠️ Table '{table_name}' migration incomplete. {supabase_count}/{total_records} records migrated.")
        else:
            print(f"⚠️ Unable to verify record count in Supabase for table '{table_name}'")
    except Exception as e:
        print(f"⚠️ Error verifying migration: {str(e)}")
    
    print(f"Migration results for {table_name}:")
    print(f"  - Total records: {total_records}")
    print(f"  - Successfully migrated: {success_count}")
    print(f"  - Failed: {error_count}")
    
    return success_count

print("\n=== Starting Migration ===")

# Migrate tables
tables_to_migrate = [
    {"name": "stores", "id_column": "id"},
    {"name": "payments", "id_column": "id"},
    {"name": "order_items", "id_column": "id"},
    {"name": "expenses", "id_column": "id"},
    {"name": "sync_log", "id_column": "id"}
]

total_success = 0
for table in tables_to_migrate:
    records_migrated = migrate_table(
        table["name"], 
        id_column=table["id_column"]
    )
    total_success += records_migrated

print("\n=== Migration Summary ===")
print(f"Total records migrated: {total_success}")

# Close connections
sqlite_conn.close()
print("\n✅ Migration completed!")

print("\n🔍 Next Steps:")
print("1. Verify data in Supabase Table Editor or SQL Editor")
print("2. Test your app with the Supabase connection")
print("3. Deploy to Streamlit Cloud") 