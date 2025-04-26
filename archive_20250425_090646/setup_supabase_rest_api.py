import os
import sys
import requests
import json
import toml
from datetime import datetime

print("🔧 Supabase Database Setup via REST API")
print("This script will attempt to create tables using Supabase REST API.\n")

# Load credentials from secrets.toml
secrets_path = os.path.join('.streamlit', 'secrets.toml')
try:
    secrets = toml.load(secrets_path)
    print(f"✅ Loaded secrets from {secrets_path}")
except Exception as e:
    print(f"❌ Failed to load secrets: {str(e)}")
    print(f"Make sure {secrets_path} exists and contains the required credentials.")
    sys.exit(1)

# Extract connection details from secrets
supabase_admin = secrets.get('connections', {}).get('supabase_admin', {})
if not supabase_admin:
    print("❌ Supabase admin connection details not found in secrets.toml")
    sys.exit(1)

project_url = supabase_admin.get('project_url', '')
api_key = supabase_admin.get('api_key', '')

if not project_url or not api_key:
    print("❌ Missing project_url or api_key in secrets.toml")
    sys.exit(1)

print(f"Project URL: {project_url}")
masked_key = api_key[:10] + "..." + api_key[-5:] if len(api_key) > 15 else api_key
print(f"API Key: {masked_key}")

# Set up headers for Supabase REST API
headers = {
    "apikey": api_key,
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Test connection
print("\nTesting connection to Supabase REST API...")
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

# Try to open the SQL Editor in a browser
sql_editor_url = f"{project_url.replace('.co', '.co/project/sql')}"
print(f"\nTo set up tables manually, open the SQL Editor: {sql_editor_url}")

# Try to use Functions API to run SQL statements
print("\nAttempting to create tables using Supabase Edge Functions (if available)...")
print("If this fails, please use the SQL Editor method described in setup_supabase_via_sql_editor.md")

# Using rpc endpoint to try to run SQL (if available)
sql_statements = [
    """
    CREATE TABLE IF NOT EXISTS stores (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        merchant_id TEXT NOT NULL UNIQUE,
        api_key TEXT,
        access_token TEXT,
        last_sync_date TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS payments (
        id TEXT PRIMARY KEY,
        merchant_id TEXT,
        order_id TEXT,
        amount INTEGER,
        created_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS order_items (
        id TEXT PRIMARY KEY,
        merchant_id TEXT, 
        order_id TEXT,
        name TEXT,
        price REAL,
        quantity INTEGER,
        created_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        store_id TEXT,
        date DATE,
        amount REAL,
        category TEXT,
        description TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sync_log (
        id SERIAL PRIMARY KEY,
        sync_time TIMESTAMP,
        status TEXT
    )
    """,
    """
    INSERT INTO stores (name, merchant_id, access_token) VALUES
    ('Laurel', '4VZSM7038BKQ1', 'b9f678d7-9b27-e971-d9e4-feab8b227c96'),
    ('Algiers', 'K25SHP45Z91H1', 'fb51be17-f0c4-c58c-0e08-44bcd4bbc5ab'),
    ('Hattiesburg', 'J3N08YKN8TSD1', '5608c683-801e-d4cf-092d-abfc907eafcc')
    ON CONFLICT (merchant_id) DO NOTHING
    """,
    """
    INSERT INTO sync_log (sync_time, status) VALUES (NOW(), 'initial_setup')
    """
]

# Try various methods to run SQL
methods = [
    {"name": "rpc endpoint", "url": f"{project_url}/rest/v1/rpc/execute_sql", "param_name": "sql"},
    {"name": "pg_dump endpoint", "url": f"{project_url}/rest/v1/pg_dump", "param_name": "query"},
    {"name": "sql endpoint", "url": f"{project_url}/rest/v1/sql", "param_name": "query"}
]

# Try each SQL statement with each method
success = False
for sql in sql_statements:
    print(f"\nSQL: {sql[:50]}...")
    sql_success = False
    
    for method in methods:
        if sql_success:
            break
            
        print(f"  Trying {method['name']}...")
        try:
            response = requests.post(
                method["url"],
                headers=headers,
                json={method["param_name"]: sql},
                timeout=15
            )
            
            if response.status_code in (200, 201, 202, 204):
                print(f"  ✅ Success with {method['name']}!")
                sql_success = True
                success = True
            else:
                print(f"  ❌ Failed with {method['name']}: {response.status_code}")
                if response.text:
                    print(f"  Response: {response.text[:100]}...")
        except Exception as e:
            print(f"  ❌ Error with {method['name']}: {str(e)}")

if not success:
    print("\n❌ Failed to create tables using REST API methods.")
    print("Please use the SQL Editor method described in setup_supabase_via_sql_editor.md")
else:
    print("\n✅ At least some operations succeeded!")
    print("To verify that all tables were created correctly, check the Supabase Table Editor or SQL Editor.")

# Check if tables exist using REST API
print("\nAttempting to verify tables via REST API...")
tables = ["stores", "payments", "order_items", "expenses", "sync_log"]
table_success = 0

for table in tables:
    try:
        print(f"Checking table '{table}'...")
        response = requests.get(
            f"{project_url}/rest/v1/{table}?limit=1",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Table '{table}' exists")
            table_success += 1
            
            # Try to count rows
            try:
                count_response = requests.get(
                    f"{project_url}/rest/v1/{table}?select=count",
                    headers={**headers, "Prefer": "count=exact"},
                    timeout=5
                )
                
                if "content-range" in count_response.headers:
                    count = count_response.headers["content-range"].split("/")[1]
                    print(f"   - Row count: {count}")
            except:
                pass
        else:
            print(f"❌ Table '{table}' not found or not accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking table '{table}': {str(e)}")

print(f"\n{table_success} of {len(tables)} tables verified via REST API.")

print("\n🔍 Next Steps:")
if table_success == len(tables):
    print("✅ All tables were created and verified successfully!")
    print("1. Run your application with the cloud database connection")
    print("2. Consider running a migration script if you need to transfer data from SQLite")
else:
    print("⚠️ Some tables may not have been created successfully.")
    print("1. Use the SQL Editor to manually create any missing tables")
    print("2. Refer to setup_supabase_via_sql_editor.md for SQL commands to run") 