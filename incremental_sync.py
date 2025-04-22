import os
import sqlite3
import time
from datetime import datetime, timedelta
import clover_data_fetcher
import db_utils

def get_store_last_sync_date(store_id):
    """Get the last successful sync date for a store"""
    conn = sqlite3.connect('clover_dashboard.db')
    cursor = conn.cursor()
    
    # Query the last sync date from the stores table
    cursor.execute("SELECT last_sync_date FROM stores WHERE id = ?", (store_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or not result[0]:
        return None
    
    try:
        # Parse the timestamp
        last_sync = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
        return last_sync
    except (ValueError, TypeError):
        return None

def incremental_sync(overlap_days=1):
    """
    Performs incremental sync for all stores, only fetching data since the last sync.
    
    Args:
        overlap_days (int): Number of days to overlap with previous sync to ensure no data is missed
    """
    print("\n" + "="*80)
    print("INCREMENTAL DATA SYNC")
    print("="*80)
    
    # Initialize database if needed
    if not os.path.exists('clover_dashboard.db'):
        print("Database doesn't exist. Creating and performing full initial sync...")
        db_utils.create_database()
        # For initial sync, use the full historical data loader
        import load_historical_data
        return load_historical_data.load_all_historical_data()
    
    # Get all stores from database
    conn = sqlite3.connect('clover_dashboard.db')
    stores_df = db_utils.get_all_stores()
    conn.close()
    
    # Keep track of sync results
    sync_results = {}
    
    # Get store credentials from config
    store_configs = clover_data_fetcher.get_store_credentials()
    
    # Create a mapping of merchant_id to credentials
    store_credentials = {}
    for store in store_configs:
        store_credentials[store['merchant_id']] = store
    
    # Process each store in the database
    for _, store_row in stores_df.iterrows():
        store_id = store_row['id']
        store_name = store_row['name']
        merchant_id = store_row['merchant_id']
        
        print(f"\n📊 Processing store: {store_name} (ID: {store_id})")
        
        # Skip if we don't have credentials for this store
        if merchant_id not in store_credentials:
            print(f"⚠️ No credentials found for {store_name} in secrets.toml. Skipping.")
            continue
        
        # Get last sync date
        last_sync = get_store_last_sync_date(store_id)
        
        # Determine start date for sync
        if last_sync:
            # Use last sync date minus overlap days to ensure no data is missed
            start_date = (last_sync - timedelta(days=overlap_days)).strftime('%Y-%m-%d')
            print(f"Last successful sync: {last_sync.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Syncing data from {start_date} to present (with {overlap_days} day overlap)")
        else:
            # If never synced, use a default start date
            start_date = "2024-01-01"  # Starting from beginning of 2024
            print(f"No previous sync found. Syncing all data from {start_date}")
        
        # Get credentials for this store
        store_creds = store_credentials[merchant_id]
        
        # Create a fetcher for this store
        fetcher = clover_data_fetcher.CloverDataFetcher(
            merchant_id=merchant_id,
            access_token=store_creds['access_token'],
            store_name=store_name
        )
        
        try:
            # Add a small delay to avoid API rate limits when processing multiple stores
            time.sleep(1)
            
            # Execute the sync
            result = fetcher.fetch_store_data(start_date)
            
            # Store the results
            sync_results[store_name] = {
                'success': True,
                'payments': result['payments'],
                'orders': result['orders'],
                'start_date': start_date
            }
            
            print(f"✅ Successfully synced {result['payments']} payments and {result['orders']} order items")
            
        except Exception as e:
            print(f"❌ Error syncing {store_name}: {str(e)}")
            sync_results[store_name] = {
                'success': False,
                'error': str(e),
                'start_date': start_date
            }
            
            # For rate limit errors, pause before continuing to the next store
            if "429" in str(e) or "Too Many Requests" in str(e):
                print("Rate limit exceeded. Pausing for 60 seconds before continuing...")
                time.sleep(60)
    
    # Print summary
    print("\n" + "="*80)
    print("SYNC SUMMARY")
    print("="*80)
    
    for store_name, result in sync_results.items():
        if result['success']:
            print(f"{store_name}: ✅ Synced {result['payments']} payments and {result['orders']} orders from {result['start_date']}")
        else:
            print(f"{store_name}: ❌ Failed - {result.get('error', 'Unknown error')}")
    
    # Run check_store_data for a quick status update
    print("\nCurrent database status:")
    try:
        import check_store_data
        check_store_data.check_store_data()
    except Exception as e:
        print(f"Error generating status report: {str(e)}")
    
    return True

if __name__ == "__main__":
    incremental_sync() 