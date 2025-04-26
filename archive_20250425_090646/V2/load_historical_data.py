import os
import sys
import sqlite3
import clover_data_fetcher
from datetime import datetime
import streamlit as st
from tqdm import tqdm

def load_all_historical_data(start_date="2024-01-01"):
    """
    Load all historical data for all stores from the specified start date.
    This function will:
    1. Check which stores are in the database
    2. Load data for all stores from the specified start date
    3. Show progress for each store
    """
    print("="*80)
    print(f"Starting historical data load from {start_date} to present for all stores")
    print("="*80)
    
    # Initialize database if needed
    if not os.path.exists('clover_dashboard.db'):
        print("Creating database...")
        import db_utils
        db_utils.create_database()
    
    # Get all stores from the secrets file
    stores = clover_data_fetcher.get_store_credentials()
    
    if not stores:
        print("⚠️ Error: No store credentials found in the secrets.toml file.")
        print("Make sure your .streamlit/secrets.toml file contains valid store configurations.")
        return False
    
    print(f"Found {len(stores)} stores in configuration:")
    for store in stores:
        print(f"  - {store['name']} (Merchant ID: {store['merchant_id']})")
    
    for i, store in enumerate(stores, 1):
        print(f"\n[{i}/{len(stores)}] Processing store: {store['name']}")
        
        # Create fetcher for this store
        fetcher = clover_data_fetcher.CloverDataFetcher(
            merchant_id=store['merchant_id'],
            access_token=store['access_token'],
            store_name=store['name']
        )
        
        try:
            # Fetch all historical data for this store
            print(f"Fetching data from {start_date} to today...")
            fetcher.fetch_store_data(start_date)
            print(f"✅ Completed data load for {store['name']}")
        except Exception as e:
            print(f"❌ Error loading data for {store['name']}: {str(e)}")
    
    # Verify the data
    conn = sqlite3.connect('clover_dashboard.db')
    cursor = conn.cursor()
    
    # Get store data
    cursor.execute("SELECT id, name, merchant_id, last_sync_date FROM stores")
    stores_data = cursor.fetchall()
    
    # Get payment and order counts
    cursor.execute("SELECT COUNT(*) FROM payments")
    payments_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM order_items")
    orders_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT order_id) FROM payments")
    unique_orders = cursor.fetchone()[0]
    
    print("\n" + "="*80)
    print("Data Load Summary")
    print("="*80)
    print(f"Total Stores: {len(stores_data)}")
    for store_id, name, merchant_id, last_sync in stores_data:
        # Get store-specific counts
        cursor.execute("SELECT COUNT(*) FROM payments WHERE store_id = ?", (store_id,))
        store_payments = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT order_id) FROM payments WHERE store_id = ?", (store_id,))
        store_orders = cursor.fetchone()[0]
        
        print(f"  - {name} (ID: {store_id})")
        print(f"    Last Sync: {last_sync}")
        print(f"    Payments: {store_payments}")
        print(f"    Orders: {store_orders}")
    
    print(f"\nTotal Payments: {payments_count}")
    print(f"Total Order Items: {orders_count}")
    print(f"Total Unique Orders: {unique_orders}")
    print("="*80)
    
    conn.close()
    return True

if __name__ == "__main__":
    # Allow custom start date from command line argument
    start_date = sys.argv[1] if len(sys.argv) > 1 else "2024-01-01"
    load_all_historical_data(start_date) 