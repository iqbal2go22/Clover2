"""
Supabase Connection Helper

This script helps obtain and validate Supabase connection details.
"""

print("=" * 80)
print("SUPABASE CONNECTION HELPER")
print("=" * 80)
print("\nThis script will help you get the correct connection details for your Supabase database.")
print("\nPlease follow these steps:")
print("\n1. Open your Supabase project dashboard in your web browser")
print("2. Click on 'Project Settings' in the left sidebar")
print("3. Click on 'Database' in the settings menu")
print("4. Scroll down to the 'Connection string' section")
print("5. Look for one of the following:")
print("   - 'Connection string (psql)'")
print("   - 'Connection string (URI)'")
print("   - 'Connection pooling'")
print("\nYou should see a string that starts with either:")
print("   postgresql://postgres:password@...")
print("   OR")
print("   postgres://postgres:password@...")
print("\nCopy this entire string, and then:")
print("1. Replace 'password' with your actual password: 'Runbut22!!'")
print("2. The hostname should be something like: 'db.abcdefghijklm.supabase.co'")
print("3. Make sure the port is '5432' or '6543' depending on what Supabase shows")
print("\nExample of a correct connection string:")
print("postgresql://postgres:Runbut22!!@db.abcdefghijklm.supabase.co:5432/postgres")

print("\n" + "=" * 80)
print("VERIFY YOUR CONNECTION DETAILS")
print("=" * 80)

# Ask for input
print("\nPlease paste your full connection string here (password will be hidden):")
connection_string = input("> ")

# Extract host for verification
import re
host_match = re.search(r'@([^:]+):', connection_string)
if host_match:
    host = host_match.group(1)
    print(f"\nExtracted host: {host}")
    
    # Test if host is resolvable
    import socket
    try:
        ip_address = socket.gethostbyname(host)
        print(f"✅ Host resolves to IP: {ip_address}")
    except socket.gaierror:
        print(f"❌ Could not resolve host: {host}")
        print("Please double-check your Supabase hostname.")
else:
    print("Could not extract hostname from connection string.")
    
# Update test_connection.py with the provided string
try:
    import urllib.parse
    
    # Extract password to hide it in output
    password_match = re.search(r'postgres:([^@]+)@', connection_string)
    if password_match:
        password = password_match.group(1)
        masked_connection = connection_string.replace(password, "********")
    else:
        masked_connection = connection_string
    
    with open('test_connection.py', 'w') as f:
        f.write("""from sqlalchemy import create_engine
import pandas as pd

# Your Supabase connection string
DATABASE_URL = "{}"

print("Testing connection to Supabase...")
print("Connecting to: {}")

try:
    # Create connection
    engine = create_engine(DATABASE_URL)
    
    # Test the connection with a simple query
    result = pd.read_sql("SELECT 1 as test", engine)
    
    print("✅ Connection successful!")
    print("Your Supabase database is ready to use.")
    
except Exception as e:
    print("❌ Connection failed:")
    print(e)
""".format(connection_string, masked_connection))
    
    print("\n✅ Updated test_connection.py with your connection string.")
    print("Run it with: py test_connection.py")
except Exception as e:
    print(f"\n❌ Error updating test_connection.py: {e}")
    
print("\n" + "=" * 80) 