import os
import sqlite3
import clover_data_fetcher
from datetime import datetime
import time

def load_algiers_data(start_date="2024-01-01"):
    """
    Load all historical data for Algiers store with additional delays to avoid rate limits.
    """
    print("="*80)
    print(f"Starting historical data load for Algiers from {start_date}")
    print("="*80)
    
    # Initialize database if needed
    if not os.path.exists('clover_dashboard.db'):
        print("Creating database...")
        import db_utils
        db_utils.create_database()
    
    # Get store credentials from the config
    stores = clover_data_fetcher.get_store_credentials()
    
    # Find Algiers in the store list
    algiers_store = None
    for store in stores:
        if store['name'] == 'Algiers':
            algiers_store = store
            break
    
    if not algiers_store:
        print("⚠️ Error: Algiers store not found in the configuration.")
        return False
    
    print(f"Found Algiers store (Merchant ID: {algiers_store['merchant_id']})")
    
    # Add extra delay to avoid rate limits
    print("Adding longer delays between API calls to avoid rate limits...")
    
    # Create a custom version of the CloverDataFetcher with longer delays
    class DelayedCloverDataFetcher(clover_data_fetcher.CloverDataFetcher):
        def get_order_details(self, order_id):
            """Override to add extra delay between calls"""
            result = super().get_order_details(order_id)
            time.sleep(0.5)  # Add a longer delay (0.5 seconds) 
            return result
        
        def get_payments_window(self, start_date, end_date):
            """Override to add extra delay between window fetches"""
            result = super().get_payments_window(start_date, end_date)
            time.sleep(2)  # Add a longer delay (2 seconds) between payment window fetches
            return result
    
    try:
        # Create fetcher for this store with added delays
        fetcher = DelayedCloverDataFetcher(
            merchant_id=algiers_store['merchant_id'],
            access_token=algiers_store['access_token'],
            store_name=algiers_store['name']
        )
        
        # Use a smaller window size to reduce the number of orders per window
        print(f"Fetching data from {start_date} to today with extra delays and smaller window size...")
        fetcher.fetch_store_data(start_date, window_size=60)  # Use 60-day windows instead of 90
        print(f"✅ Completed data load for Algiers")
        
        # Verify the data
        conn = sqlite3.connect('clover_dashboard.db')
        cursor = conn.cursor()
        
        # Get store-specific counts
        cursor.execute("""
            SELECT COUNT(*) FROM payments WHERE store_id = (
                SELECT id FROM stores WHERE name = 'Algiers'
            )
        """)
        payments_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT order_id) FROM payments WHERE store_id = (
                SELECT id FROM stores WHERE name = 'Algiers'
            )
        """)
        orders_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM order_items WHERE store_id = (
                SELECT id FROM stores WHERE name = 'Algiers'
            )
        """)
        items_count = cursor.fetchone()[0]
        
        print(f"\nAlgiers Data Summary:")
        print(f"Payments: {payments_count}")
        print(f"Unique Orders: {orders_count}")
        print(f"Order Items: {items_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error loading data for Algiers: {str(e)}")
        return False

if __name__ == "__main__":
    load_algiers_data() 