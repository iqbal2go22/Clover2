import os
import sqlite3
import toml

def clean_stores():
    """
    Clean up the database by removing any demo stores that aren't in the secrets.toml file.
    Only keep the legitimate stores from secrets.toml.
    """
    print("Starting store database cleanup...")
    
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
    
    # Extract merchant IDs from secrets.toml
    valid_merchant_ids = []
    for section in secrets:
        if section.startswith('store_'):
            store_data = secrets[section]
            if isinstance(store_data, dict) and 'merchant_id' in store_data:
                merchant_id = store_data['merchant_id']
                if merchant_id and not merchant_id.startswith('#'):
                    valid_merchant_ids.append(merchant_id)
    
    print(f"Found {len(valid_merchant_ids)} legitimate stores in secrets.toml:")
    for merchant_id in valid_merchant_ids:
        print(f"  - Merchant ID: {merchant_id}")
    
    # Connect to the database
    conn = sqlite3.connect('clover_dashboard.db')
    cursor = conn.cursor()
    
    # Get all stores from database
    cursor.execute("SELECT id, name, merchant_id FROM stores")
    db_stores = cursor.fetchall()
    
    # Identify stores to delete (those not in valid_merchant_ids)
    stores_to_delete = [store for store in db_stores if store[2] not in valid_merchant_ids]
    
    if not stores_to_delete:
        print("No invalid stores found in the database.")
        conn.close()
        return True
    
    print(f"\nFound {len(stores_to_delete)} stores to delete:")
    for store_id, store_name, merchant_id in stores_to_delete:
        print(f"  - ID: {store_id}, Name: {store_name}, Merchant ID: {merchant_id}")
    
    # Ask for confirmation before deleting
    confirm = input("\nDo you want to delete these stores and their data? (y/n): ")
    
    if confirm.lower() != 'y':
        print("Cleanup cancelled")
        conn.close()
        return False
    
    # Delete data for these stores
    store_ids = [store[0] for store in stores_to_delete]
    store_ids_str = ','.join('?' for _ in store_ids)
    
    try:
        # Delete all related data for these stores
        cursor.execute(f"DELETE FROM payments WHERE store_id IN ({store_ids_str})", store_ids)
        payments_deleted = cursor.rowcount
        
        cursor.execute(f"DELETE FROM order_items WHERE store_id IN ({store_ids_str})", store_ids)
        items_deleted = cursor.rowcount
        
        cursor.execute(f"DELETE FROM sync_log WHERE store_id IN ({store_ids_str})", store_ids)
        logs_deleted = cursor.rowcount
        
        # Delete the store entries
        cursor.execute(f"DELETE FROM stores WHERE id IN ({store_ids_str})", store_ids)
        stores_deleted = cursor.rowcount
        
        # Commit changes
        conn.commit()
        
        print(f"\nDeleted {stores_deleted} stores successfully.")
        print(f"Also removed {payments_deleted} payments, {items_deleted} order items, and {logs_deleted} sync logs.")
        
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        conn.rollback()
        conn.close()
        return False
    
    conn.close()
    print("\nStore cleanup completed successfully!")
    return True

if __name__ == "__main__":
    clean_stores() 