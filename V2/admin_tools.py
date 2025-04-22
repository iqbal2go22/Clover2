import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import clover_data_fetcher
import db_utils
import load_historical_data
import incremental_sync

def show_menu():
    """Display the admin tools menu"""
    print("\n" + "="*80)
    print("CLOVER DASHBOARD ADMIN TOOLS")
    print("="*80)
    print("1. Check Database Status")
    print("2. Incremental Data Sync")
    print("3. Full Data Resync")
    print("4. Sync Specific Store")
    print("5. Repair Store Record")
    print("6. Clean Up Demo Stores")
    print("7. Exit")
    print("="*80)
    choice = input("Choose an option (1-7): ")
    return choice

def check_database():
    """Check database status"""
    try:
        import check_store_data
        check_store_data.check_store_data()
    except Exception as e:
        print(f"Error checking database: {str(e)}")

def full_resync():
    """Perform a full data resync from beginning of year"""
    confirm = input("⚠️ Warning: This will delete ALL existing data and reload from scratch. Continue? (y/n): ")
    if confirm.lower() != 'y':
        print("Resync cancelled.")
        return
    
    try:
        # Wipe existing data
        conn = sqlite3.connect('clover_dashboard.db')
        cursor = conn.cursor()
        
        print("Deleting existing data...")
        cursor.execute("DELETE FROM payments WHERE 1=1")
        cursor.execute("DELETE FROM order_items WHERE 1=1")
        cursor.execute("DELETE FROM sync_log WHERE 1=1")
        
        # Reset sync dates
        cursor.execute("UPDATE stores SET last_sync_date = NULL WHERE 1=1")
        
        conn.commit()
        conn.close()
        
        print("Data wiped. Starting full reload from January 1, 2024...")
        load_historical_data.load_all_historical_data("2024-01-01")
        print("Full resync completed!")
    except Exception as e:
        print(f"Error during full resync: {str(e)}")

def sync_specific_store():
    """Sync data for a specific store"""
    # Get available stores
    stores = db_utils.get_all_stores()
    
    if stores.empty:
        print("No stores found in the database.")
        return
    
    print("\nAvailable stores:")
    for idx, (_, store) in enumerate(stores.iterrows(), 1):
        print(f"{idx}. {store['name']} (ID: {store['id']}, Merchant ID: {store['merchant_id']})")
    
    try:
        choice = int(input("\nSelect store number to sync: "))
        if choice < 1 or choice > len(stores):
            print("Invalid selection.")
            return
        
        store_idx = choice - 1
        store_id = stores.iloc[store_idx]['id']
        store_name = stores.iloc[store_idx]['name']
        merchant_id = stores.iloc[store_idx]['merchant_id']
        
        print(f"\nSelected store: {store_name}")
        sync_type = input("Sync type (1=Incremental, 2=Full history): ")
        
        if sync_type == '1':
            # Incremental sync
            days_overlap = int(input("Days of overlap for incremental sync (default: 2): ") or "2")
            
            # Get last sync date
            last_sync = incremental_sync.get_store_last_sync_date(store_id)
            
            if last_sync:
                start_date = (last_sync - timedelta(days=days_overlap)).strftime('%Y-%m-%d')
                print(f"Incremental sync from {start_date} (with {days_overlap} days overlap)...")
            else:
                start_date = input("No previous sync found. Enter start date (YYYY-MM-DD, default: 2024-01-01): ") or "2024-01-01"
                print(f"Full sync from {start_date}...")
        else:
            # Full sync
            start_date = input("Enter start date (YYYY-MM-DD, default: 2024-01-01): ") or "2024-01-01"
            
            # Clear existing data for this store
            confirm = input(f"Clear existing data for {store_name}? (y/n): ")
            if confirm.lower() == 'y':
                conn = sqlite3.connect('clover_dashboard.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM payments WHERE store_id = ?", (store_id,))
                cursor.execute("DELETE FROM order_items WHERE store_id = ?", (store_id,))
                cursor.execute("DELETE FROM sync_log WHERE store_id = ?", (store_id,))
                cursor.execute("UPDATE stores SET last_sync_date = NULL WHERE id = ?", (store_id,))
                deleted_counts = [cursor.rowcount]
                conn.commit()
                conn.close()
                print(f"Deleted existing data for {store_name}.")
        
        # Get store credentials
        store_configs = clover_data_fetcher.get_store_credentials()
        store_creds = None
        for config in store_configs:
            if config['merchant_id'] == merchant_id:
                store_creds = config
                break
        
        if not store_creds:
            print(f"⚠️ Error: No credentials found for {store_name} in secrets.toml.")
            return
        
        # Create fetcher for this store
        fetcher = clover_data_fetcher.CloverDataFetcher(
            merchant_id=merchant_id,
            access_token=store_creds['access_token'],
            store_name=store_name
        )
        
        # Execute the sync
        print(f"Syncing data for {store_name} from {start_date}...")
        result = fetcher.fetch_store_data(start_date)
        print(f"✅ Sync completed: {result['payments']} payments and {result['orders']} order items")
        
    except (ValueError, IndexError) as e:
        print(f"Error: {str(e)}")

def repair_store_record():
    """Repair store records with missing data"""
    stores = db_utils.get_all_stores()
    
    if stores.empty:
        print("No stores found in the database.")
        return
    
    print("\nStore records:")
    for idx, (_, store) in enumerate(stores.iterrows(), 1):
        last_sync = store.get('last_sync_date', 'Never')
        print(f"{idx}. {store['name']} (ID: {store['id']}, Last sync: {last_sync})")
    
    try:
        choice = int(input("\nSelect store to repair (0 to cancel): "))
        if choice == 0:
            return
        if choice < 1 or choice > len(stores):
            print("Invalid selection.")
            return
        
        store_idx = choice - 1
        store_id = stores.iloc[store_idx]['id']
        store_name = stores.iloc[store_idx]['name']
        
        print(f"\nRepairing store: {store_name}")
        
        # Options for repair
        print("1. Reset last sync date")
        print("2. Update store name")
        print("3. Check for missing order data")
        
        repair_choice = input("Select repair option (1-3): ")
        
        if repair_choice == '1':
            conn = sqlite3.connect('clover_dashboard.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE stores SET last_sync_date = NULL WHERE id = ?", (store_id,))
            conn.commit()
            conn.close()
            print(f"Reset last sync date for {store_name}.")
            
        elif repair_choice == '2':
            new_name = input("Enter new name for store: ")
            conn = sqlite3.connect('clover_dashboard.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE stores SET name = ? WHERE id = ?", (new_name, store_id))
            conn.commit()
            conn.close()
            print(f"Updated store name to: {new_name}")
            
        elif repair_choice == '3':
            conn = sqlite3.connect('clover_dashboard.db')
            
            # Find orders without line items
            query = """
            SELECT DISTINCT p.order_id
            FROM payments p
            LEFT JOIN order_items o ON p.order_id = o.order_id AND p.store_id = o.store_id
            WHERE p.store_id = ? AND o.id IS NULL
            """
            
            missing_orders = pd.read_sql(query, conn, params=[store_id])
            
            if missing_orders.empty:
                print("No missing order data found.")
            else:
                print(f"Found {len(missing_orders)} orders with missing line items.")
                confirm = input("Attempt to refetch missing orders? (y/n): ")
                
                if confirm.lower() == 'y':
                    # Get store credentials
                    merchant_id = stores.iloc[store_idx]['merchant_id']
                    store_configs = clover_data_fetcher.get_store_credentials()
                    store_creds = None
                    
                    for config in store_configs:
                        if config['merchant_id'] == merchant_id:
                            store_creds = config
                            break
                    
                    if not store_creds:
                        print(f"⚠️ Error: No credentials found for {store_name} in secrets.toml.")
                        return
                    
                    # Create fetcher
                    fetcher = clover_data_fetcher.CloverDataFetcher(
                        merchant_id=merchant_id,
                        access_token=store_creds['access_token'],
                        store_name=store_name
                    )
                    
                    fixed_count = 0
                    for order_id in missing_orders['order_id']:
                        try:
                            print(f"Fetching order: {order_id}")
                            order_data = fetcher.get_order_details(order_id)
                            
                            if order_data:
                                line_items = clover_data_fetcher.extract_line_items_from_order(order_data, store_id)
                                if line_items:
                                    db_utils.save_order_items(line_items, store_id)
                                    fixed_count += 1
                            
                            # Avoid rate limits
                            time.sleep(0.5)
                        except Exception as e:
                            print(f"Error fetching order {order_id}: {str(e)}")
                    
                    print(f"Fixed {fixed_count} orders with missing data.")
            
            conn.close()
        
    except (ValueError, IndexError) as e:
        print(f"Error: {str(e)}")

def clean_up_demo_stores():
    """Clean up demo stores from the database"""
    try:
        import clean_stores
        clean_stores.clean_stores()
    except Exception as e:
        print(f"Error cleaning up demo stores: {str(e)}")

def main():
    while True:
        choice = show_menu()
        
        if choice == '1':
            check_database()
        elif choice == '2':
            overlap = input("Days of overlap for incremental sync (default: 1): ") or "1"
            incremental_sync.incremental_sync(overlap_days=int(overlap))
        elif choice == '3':
            full_resync()
        elif choice == '4':
            sync_specific_store()
        elif choice == '5':
            repair_store_record()
        elif choice == '6':
            clean_up_demo_stores()
        elif choice == '7':
            print("Exiting admin tools.")
            break
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 