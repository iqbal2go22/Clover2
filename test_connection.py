import psycopg2
import pandas as pd
import socket

print("=" * 80)
print("SUPABASE CONNECTION TEST - UPDATED CREDENTIALS")
print("=" * 80)

# Connection parameters - updated with new password
connection_methods = [
    {
        "name": "Direct Connection",
        "params": {
            "host": "db.yegrbbtxlsfbrlyavmbg.supabase.co",
            "port": "5432",
            "dbname": "postgres",
            "user": "postgres",
            "password": "721AFFTNZmnQ3An7",  # Updated password
            "connect_timeout": 10
        }
    },
    {
        "name": "Connection Pooling",
        "params": {
            "host": "yegrbbtxlsfbrlyavmbg.supabase.co",
            "port": "6543",
            "dbname": "postgres",
            "user": "postgres.yegrbbtxlsfbrlyavmbg",
            "password": "721AFFTNZmnQ3An7",  # Updated password
            "connect_timeout": 10
        }
    }
]

for method in connection_methods:
    print(f"\nTrying {method['name']}:")
    print(f"  Host: {method['params']['host']}")
    print(f"  Port: {method['params']['port']}")
    print(f"  Database: {method['params']['dbname']}")
    print(f"  User: {method['params']['user']}")
    print(f"  Password: {'*' * len(method['params']['password'])}")
    
    # First try to check if the hostname can be resolved
    print(f"  Checking if host is reachable:")
    try:
        # Set a timeout for DNS resolution
        socket.setdefaulttimeout(5)
        ip = socket.gethostbyname(method['params']['host'])
        print(f"    ✅ Host resolves to IP: {ip}")
        
        # Try to connect
        try:
            conn = psycopg2.connect(**method['params'])
            
            # Test the connection
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()[0]
            
            print(f"    ✅ Connection successful!")
            print(f"    Test query result: {result}")
            
            # Get PostgreSQL version
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"    PostgreSQL version: {version}")
            
            # Close cursor and connection
            cursor.close()
            conn.close()
            
            print(f"\n  Your Supabase database is ready to use with {method['name']}.")
            
            # Write the successful connection details
            with open(f"supabase_{method['name'].lower().replace(' ', '_')}.txt", "w") as f:
                for key, value in method['params'].items():
                    if key != "connect_timeout":
                        f.write(f"{key}={value}\n")
            
            print(f"  Connection details saved to supabase_{method['name'].lower().replace(' ', '_')}.txt")
            
        except Exception as e:
            print(f"    ❌ Connection failed: {e}")
            
    except socket.gaierror as e:
        print(f"    ❌ Could not resolve hostname: {e}")

print("\nTROUBLESHOOTING TIPS:")
print("1. Check if the new password is correct")
print("2. Verify network connectivity to Supabase servers")
print("3. Consider adding your IP to Supabase's allow list")
print("4. When ready to deploy to Streamlit Cloud, add these credentials to the secrets management")

print("=" * 80) 