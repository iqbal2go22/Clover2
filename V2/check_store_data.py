import sqlite3
import pandas as pd
from datetime import datetime

def check_store_data():
    """
    Check and display the current data status for each store in the database.
    Shows information about store configuration, sync status, and data counts.
    """
    try:
        conn = sqlite3.connect('clover_dashboard.db')
        cursor = conn.cursor()
        
        # Check if the database exists and has the stores table
        try:
            cursor.execute("SELECT COUNT(*) FROM stores")
        except sqlite3.OperationalError:
            print("Database not initialized or stores table doesn't exist.")
            return
        
        # Get all stores
        cursor.execute("""
            SELECT id, name, merchant_id, last_sync_date 
            FROM stores 
            ORDER BY name
        """)
        stores = cursor.fetchall()
        
        if not stores:
            print("No stores found in the database.")
            return
        
        print("\n" + "="*80)
        print("STORE DATA STATUS")
        print("="*80)
        
        # Process each store
        for store_id, name, merchant_id, last_sync in stores:
            print(f"\n📊 {name.upper()} (ID: {store_id}, Merchant ID: {merchant_id})")
            
            # Format the last sync date
            if last_sync:
                try:
                    sync_date = datetime.strptime(last_sync, '%Y-%m-%d %H:%M:%S')
                    time_ago = (datetime.now() - sync_date).total_seconds() / 3600  # hours
                    if time_ago < 24:
                        sync_status = f"✅ {sync_date.strftime('%Y-%m-%d %H:%M:%S')} ({time_ago:.1f} hours ago)"
                    else:
                        days_ago = time_ago / 24
                        sync_status = f"⚠️ {sync_date.strftime('%Y-%m-%d %H:%M:%S')} ({days_ago:.1f} days ago)"
                except ValueError:
                    sync_status = f"⚠️ {last_sync} (invalid format)"
            else:
                sync_status = "❌ Never synced"
            
            print(f"Last Sync: {sync_status}")
            
            # Check payment data
            cursor.execute("""
                SELECT COUNT(*) as count, 
                       MIN(created_time) as earliest, 
                       MAX(created_time) as latest
                FROM payments 
                WHERE store_id = ?
            """, (store_id,))
            payment_data = cursor.fetchone()
            
            payment_count = payment_data[0] if payment_data else 0
            payment_earliest = payment_data[1] if payment_data and payment_data[1] else "N/A"
            payment_latest = payment_data[2] if payment_data and payment_data[2] else "N/A"
            
            print(f"Payments: {payment_count:,}")
            if payment_count > 0:
                print(f"  Date Range: {payment_earliest} to {payment_latest}")
            
            # Check order data
            cursor.execute("""
                SELECT COUNT(DISTINCT order_id) as count
                FROM payments 
                WHERE store_id = ?
            """, (store_id,))
            order_count_result = cursor.fetchone()
            order_count = order_count_result[0] if order_count_result else 0
            
            cursor.execute("""
                SELECT COUNT(*) as count, 
                       MIN(created_time) as earliest, 
                       MAX(created_time) as latest
                FROM order_items 
                WHERE store_id = ?
            """, (store_id,))
            order_item_data = cursor.fetchone()
            
            item_count = order_item_data[0] if order_item_data else 0
            item_earliest = order_item_data[1] if order_item_data and order_item_data[1] else "N/A"
            item_latest = order_item_data[2] if order_item_data and order_item_data[2] else "N/A"
            
            # Query again to get the distinct order count
            cursor.execute("""
                SELECT COUNT(DISTINCT order_id) as count
                FROM order_items 
                WHERE store_id = ?
            """, (store_id,))
            distinct_orders_result = cursor.fetchone()
            distinct_orders = distinct_orders_result[0] if distinct_orders_result else 0
            
            print(f"Order Items: {item_count:,}")
            if item_count > 0:
                print(f"  Unique Orders: {distinct_orders:,}")
                print(f"  Date Range: {item_earliest} to {item_latest}")
            
            # Calculate total sales
            cursor.execute("""
                SELECT SUM(price * quantity) as total
                FROM order_items
                WHERE store_id = ?
            """, (store_id,))
            total_sales_result = cursor.fetchone()
            total_sales = total_sales_result[0] if total_sales_result and total_sales_result[0] is not None else 0
            
            if total_sales:
                print(f"Total Sales: ${total_sales:,.2f}")
            
            # Get sync history
            cursor.execute("""
                SELECT sync_date, payments_count, orders_count
                FROM sync_log
                WHERE store_id = ?
                ORDER BY sync_date DESC
                LIMIT 5
            """, (store_id,))
            sync_history = cursor.fetchall()
            
            if sync_history:
                print("\nRecent Sync History:")
                for sync_date, payments, orders in sync_history:
                    print(f"  {sync_date}: {payments} payments, {orders} order items")
        
        # Database summary
        print("\n" + "="*80)
        print("DATABASE SUMMARY")
        print("="*80)
        
        cursor.execute("SELECT COUNT(*) FROM payments")
        total_payments = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM order_items")
        total_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT order_id) FROM payments")
        total_orders = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(price * quantity) FROM order_items")
        total_sales_result = cursor.fetchone()
        total_sales = total_sales_result[0] if total_sales_result and total_sales_result[0] is not None else 0
        
        print(f"Total Stores: {len(stores)}")
        print(f"Total Payments: {total_payments:,}")
        print(f"Total Orders: {total_orders:,}")
        print(f"Total Order Items: {total_items:,}")
        if total_sales:
            print(f"Total Sales Value: ${total_sales:,.2f}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking store data: {str(e)}")

if __name__ == "__main__":
    check_store_data() 