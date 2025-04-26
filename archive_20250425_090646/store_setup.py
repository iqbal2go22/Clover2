import os
import sqlite3
import toml
from datetime import datetime

def setup_stores():
    """
    Set up all stores from the secrets.toml file.
    This function will read the secrets.toml file and add all stores to the database.
    """
    # Path to the secrets.toml file
    secrets_path = os.path.join('.streamlit', 'secrets.toml')
    
    # Check if the file exists
    if not os.path.exists(secrets_path):
        print(f"Error: {secrets_path} does not exist.")
        return False
    
    # Read the secrets.toml file
    try:
        secrets = toml.load(secrets_path)
    except Exception as e:
        print(f"Error reading {secrets_path}: {str(e)}")
        return False
    
    # Connect to the database
    conn = sqlite3.connect('clover_dashboard.db')
    cursor = conn.cursor()
    
    # Get a list of store sections from the secrets file
    store_sections = [section for section in secrets.keys() if section.startswith('store_')]
    
    if not store_sections:
        print("No store sections found in secrets.toml")
        conn.close()
        return False
    
    # Check the actual structure of the stores table
    cursor.execute("PRAGMA table_info(stores)")
    columns = [column[1] for column in cursor.fetchall()]
    print(f"Existing columns in the stores table: {columns}")
    
    # Create table if it doesn't exist
    if not columns:
        print("Creating stores table...")
        cursor.execute("""
        CREATE TABLE stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            access_token TEXT NOT NULL,
            last_sync_date TEXT
        )
        """)
        columns = ['id', 'merchant_id', 'name', 'access_token', 'last_sync_date']
    
    # Get existing store merchant_ids
    cursor.execute("SELECT merchant_id FROM stores")
    existing_merchant_ids = [row[0] for row in cursor.fetchall()]
    
    # Add each store to the database
    stores_added = 0
    stores_updated = 0
    
    for section in store_sections:
        store_data = secrets[section]
        
        # Skip if this section is commented out or missing required fields
        if not isinstance(store_data, dict) or 'merchant_id' not in store_data or 'name' not in store_data or 'access_token' not in store_data:
            print(f"Skipping store section {section}: Missing required fields or commented out")
            continue
        
        merchant_id = store_data.get('merchant_id')
        name = store_data.get('name')
        access_token = store_data.get('access_token')
        
        # Skip if any required field is missing
        if not merchant_id or not name or not access_token:
            print(f"Skipping store section {section}: Missing required fields")
            continue
        
        # Check if the store already exists
        if merchant_id in existing_merchant_ids:
            # Update the store
            cursor.execute("""
            UPDATE stores 
            SET name = ?, access_token = ?
            WHERE merchant_id = ?
            """, (name, access_token, merchant_id))
            stores_updated += 1
            print(f"Updated store: {name} (Merchant ID: {merchant_id})")
        else:
            # Add the store - using only columns that exist in the table
            cursor.execute("""
            INSERT INTO stores (merchant_id, name, access_token)
            VALUES (?, ?, ?)
            """, (merchant_id, name, access_token))
            stores_added += 1
            print(f"Added store: {name} (Merchant ID: {merchant_id})")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Store setup complete: {stores_added} stores added, {stores_updated} stores updated.")
    return stores_added + stores_updated > 0

if __name__ == "__main__":
    # Run the store setup
    setup_stores() 