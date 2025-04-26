import os
import sys
import json
import toml
from datetime import datetime
import traceback  # Added for better error reporting

print("🔧 Supabase Database Direct Setup")
print("This script will directly create all necessary tables in your Supabase database.\n")

# Load credentials from secrets.toml
secrets_path = os.path.join('.streamlit', 'secrets.toml')
try:
    secrets = toml.load(secrets_path)
    print(f"✅ Loaded secrets from {secrets_path}")
except Exception as e:
    print(f"❌ Failed to load secrets: {str(e)}")
    print(f"Make sure {secrets_path} exists and contains the required credentials.")
    sys.exit(1)

# Extract database connection details from secrets
db_connection = secrets.get('connections', {}).get('supabase_admin', {})

if not db_connection:
    print("❌ Supabase admin connection details not found in secrets.toml")
    print("Please ensure your secrets.toml contains a [connections.supabase_admin] section")
    sys.exit(1)

# Print connection details (masked)
project_url = db_connection.get('project_url', '')
api_key = db_connection.get('api_key', '')
db_password = db_connection.get('db_password', '')
db_host = db_connection.get('db_host', '')
db_name = db_connection.get('db_name', '')
db_user = db_connection.get('db_user', '')
db_port = db_connection.get('db_port', 5432)

print(f"Project URL: {project_url}")
print(f"API Key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")

# Try alternative approach with connection string
direct_url = db_connection.get('url', '')
if not direct_url:
    # Check if there's a connection string in the supabase_sql section
    sql_connection = secrets.get('connections', {}).get('supabase_sql', {})
    if sql_connection:
        direct_url = sql_connection.get('url', '')
        print("Found connection URL in supabase_sql section")

# Check if we can find a connection string in the main supabase section
if not direct_url:
    supabase_section = secrets.get('supabase', {})
    if supabase_section:
        direct_url = supabase_section.get('direct_url', '')
        if direct_url:
            print("Found direct_url in supabase section")

# Alternative approaches to try
methods_to_try = []

# Method 1: Direct PostgreSQL connection with explicit credentials
if db_host and db_user and db_password:
    print(f"\nMethod 1: Direct PostgreSQL connection")
    print(f"Database Host: {db_host}")
    print(f"Database User: {db_user}")
    print(f"Database Name: {db_name}")
    
    methods_to_try.append({
        'name': 'Direct PostgreSQL connection',
        'type': 'direct',
        'params': {
            'host': db_host,
            'port': db_port,
            'dbname': db_name,
            'user': db_user,
            'password': db_password
        }
    })

# Method 2: Connection URL if available
if direct_url:
    masked_url = direct_url[:20] + "..." + direct_url[-20:] if len(direct_url) > 40 else direct_url
    print(f"\nMethod 2: Connection URL")
    print(f"Connection URL: {masked_url}")
    
    methods_to_try.append({
        'name': 'Connection URL',
        'type': 'url',
        'params': {
            'dsn': direct_url
        }
    })

if not methods_to_try:
    print("❌ No valid connection methods available. Please check your secrets.toml file.")
    sys.exit(1)

# Try each connection method
connection_successful = False
conn = None

for method in methods_to_try:
    print(f"\nTrying {method['name']}...")
    try:
        # We need to import psycopg2 here since it might not be installed
        try:
            import psycopg2
        except ImportError:
            print("❌ psycopg2 module not found. Installing psycopg2-binary...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
            import psycopg2
            print("✅ psycopg2-binary installed successfully")
        
        if method['type'] == 'direct':
            conn = psycopg2.connect(**method['params'])
        else:  # url
            conn = psycopg2.connect(method['params']['dsn'])
            
        print(f"✅ Connected to PostgreSQL database using {method['name']}")
        connection_successful = True
        break
    except Exception as e:
        print(f"❌ Failed to connect using {method['name']}: {str(e)}")
        print("Detailed error:")
        traceback.print_exc()

if not connection_successful:
    print("\n❌ All connection methods failed.")
    print("Please make sure your database credentials are correct and the database is accessible.")
    sys.exit(1)

try:
    # Create cursor
    cursor = conn.cursor()
    
    # SQL statements to create all tables
    create_tables_sql = """
    -- Create stores table
    CREATE TABLE IF NOT EXISTS stores (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        merchant_id TEXT NOT NULL UNIQUE,
        api_key TEXT,
        access_token TEXT,
        last_sync_date TIMESTAMP
    );

    -- Create payments table
    CREATE TABLE IF NOT EXISTS payments (
        id TEXT PRIMARY KEY,
        merchant_id TEXT,
        order_id TEXT,
        amount INTEGER,
        created_at TIMESTAMP
    );

    -- Create order_items table
    CREATE TABLE IF NOT EXISTS order_items (
        id TEXT PRIMARY KEY,
        merchant_id TEXT, 
        order_id TEXT,
        name TEXT,
        price REAL,
        quantity INTEGER,
        created_at TIMESTAMP
    );

    -- Create expenses table
    CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        store_id TEXT,
        date DATE,
        amount REAL,
        category TEXT,
        description TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    );

    -- Create sync_log table
    CREATE TABLE IF NOT EXISTS sync_log (
        id SERIAL PRIMARY KEY,
        sync_time TIMESTAMP,
        status TEXT
    );
    """
    
    # Split SQL into individual statements
    sql_statements = [stmt.strip() for stmt in create_tables_sql.split(';') if stmt.strip()]
    
    # Execute each statement
    success_count = 0
    for i, sql in enumerate(sql_statements):
        try:
            print(f"\nExecuting SQL statement {i+1}:")
            print(f"{sql[:100]}..." if len(sql) > 100 else sql)
            
            cursor.execute(sql)
            conn.commit()
            print(f"✅ SQL statement {i+1} executed successfully")
            success_count += 1
        except Exception as e:
            print(f"❌ Error executing SQL statement {i+1}: {str(e)}")
            traceback.print_exc()
    
    print(f"\n{success_count} of {len(sql_statements)} SQL statements executed successfully.")
    
    # Insert store data
    stores_data = [
        {
            "name": "Laurel",
            "merchant_id": "4VZSM7038BKQ1",
            "access_token": "b9f678d7-9b27-e971-d9e4-feab8b227c96"
        },
        {
            "name": "Algiers",
            "merchant_id": "K25SHP45Z91H1",
            "access_token": "fb51be17-f0c4-c58c-0e08-44bcd4bbc5ab"
        },
        {
            "name": "Hattiesburg",
            "merchant_id": "J3N08YKN8TSD1",
            "access_token": "5608c683-801e-d4cf-092d-abfc907eafcc"
        }
    ]
    
    print("\nInserting store data:")
    stores_success = 0
    for store in stores_data:
        try:
            cursor.execute(
                "INSERT INTO stores (name, merchant_id, access_token) VALUES (%s, %s, %s) ON CONFLICT (merchant_id) DO NOTHING",
                (store["name"], store["merchant_id"], store["access_token"])
            )
            conn.commit()
            print(f"✅ Store {store['name']} added or already exists")
            stores_success += 1
        except Exception as e:
            print(f"❌ Error adding store {store['name']}: {str(e)}")
            traceback.print_exc()
    
    print(f"\n{stores_success} of {len(stores_data)} stores added successfully.")
    
    # Add initial sync log entry
    print("\nCreating sync log entry:")
    try:
        sync_time = datetime.now()
        cursor.execute(
            "INSERT INTO sync_log (sync_time, status) VALUES (%s, %s) RETURNING id",
            (sync_time, "initial_setup")
        )
        sync_id = cursor.fetchone()[0]
        conn.commit()
        print(f"✅ Sync log entry created with ID: {sync_id}")
    except Exception as e:
        print(f"❌ Error creating sync log entry: {str(e)}")
        traceback.print_exc()
    
    # Check table status
    print("\nChecking tables:")
    tables = ["stores", "payments", "order_items", "expenses", "sync_log"]
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ Table '{table}' exists with {count} rows")
        except Exception as e:
            print(f"❌ Error checking table '{table}': {str(e)}")
            traceback.print_exc()
    
    # Close connection
    cursor.close()
    conn.close()
    print("\n✅ All operations completed. Database setup successfully!")
    
except Exception as e:
    print(f"❌ Operation failed: {str(e)}")
    print("Detailed error:")
    traceback.print_exc()
    if conn:
        conn.close()
    sys.exit(1)

print("\n🔍 Next Steps:")
print("1. Verify tables are created in Supabase")
print("2. Run your application with the cloud database connection")
print("3. Consider running a migration script if you need to transfer data from SQLite") 