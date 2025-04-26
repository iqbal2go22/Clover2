import sqlite3
import clover_data_fetcher
from datetime import datetime
import time

def sync_new_stores():
    """
    Sync data for newly added stores, starting from January 1st, 2025.
    This is a one-time operation to populate the database with historical data for new stores.
    """
    print("Starting one-time sync for new stores (from January 1st, 2025)")
    
    # Connect to the database
    conn = sqlite3.connect('clover_dashboard.db')
    cursor = conn.cursor()
    
    # Get all stores except ID 1 (assuming ID 1 is the original store)
    cursor.execute("""
    SELECT id, name, merchant_id, access_token FROM stores 
    WHERE id > 1 ORDER BY id
    """)
    stores = cursor.fetchall()
    
    if not stores:
        print("No new stores found to sync")
        conn.close()
        return False
    
    print(f"Found {len(stores)} new store(s) to sync:")
    for store in stores:
        store_id, store_name, merchant_id, access_token = store
        print(f"  - ID: {store_id}, Name: {store_name}, Merchant ID: {merchant_id}")
    
    # Start date for sync - January 1st, 2025
    start_date = "2025-01-01"
    
    # Clear existing data for these stores to avoid duplicates
    store_ids = [store[0] for store in stores]
    store_ids_str = ','.join('?' for _ in store_ids)
    
    # Ask for confirmation before deleting data
    print("\nWARNING: This will DELETE existing data for these stores and re-sync from January 1st, 2025.")
    confirm = input("Continue? (y/n): ")
    
    if confirm.lower() != 'y':
        print("Sync cancelled")
        conn.close()
        return False
    
    print("\nClearing existing data for new stores...")
    try:
        cursor.execute(f"DELETE FROM payments WHERE store_id IN ({store_ids_str})", store_ids)
        print(f"Cleared {cursor.rowcount} payment records")
        
        cursor.execute(f"DELETE FROM order_items WHERE store_id IN ({store_ids_str})", store_ids)
        print(f"Cleared {cursor.rowcount} order item records")
        
        cursor.execute(f"DELETE FROM sync_log WHERE store_id IN ({store_ids_str})", store_ids)
        print(f"Cleared sync logs for these stores")
        
        # Commit the deletions
        conn.commit()
    except Exception as e:
        print(f"Error clearing data: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
    
    # Sync each store using CloverDataFetcher
    total_success = True
    for store in stores:
        store_id, store_name, merchant_id, access_token = store
        print(f"\nSyncing data for {store_name} (ID: {store_id})...")
        
        try:
            # Use the CloverDataFetcher to sync the store
            fetcher = clover_data_fetcher.CloverDataFetcher(
                merchant_id=merchant_id,
                access_token=access_token,
                store_name=store_name
            )
            
            # Fetch all data from January 1st, 2025
            result = fetcher.fetch_store_data(start_date)
            
            if result:
                payments_count = result.get('payments', 0)
                orders_count = result.get('orders', 0)
                print(f"Successfully synced {payments_count} payments and {orders_count} order items for {store_name}")
            else:
                print(f"Failed to sync data for {store_name}")
                total_success = False
                
            # Add a delay between store syncs to avoid rate limiting
            time.sleep(5)
            
        except Exception as e:
            print(f"Error syncing {store_name}: {str(e)}")
            total_success = False
    
    if total_success:
        print("\nAll stores synced successfully!")
    else:
        print("\nSync completed with some errors. Please check the logs.")
    
    return total_success

if __name__ == "__main__":
    sync_new_stores() 