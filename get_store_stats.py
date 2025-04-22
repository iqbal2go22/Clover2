import sqlite3
from datetime import datetime

def get_store_stats():
    """Get and print order and sales statistics for each store"""
    conn = sqlite3.connect('clover_dashboard.db')
    cursor = conn.cursor()
    
    # Get current year for YTD filter
    current_year = 2025  # Hardcoded for this specific dataset
    ytd_start = f"{current_year}-01-01 00:00:00"
    
    # Get all stores
    cursor.execute("SELECT id, name FROM stores ORDER BY name")
    stores = cursor.fetchall()
    
    # Print dashboard YTD figures for reference
    print("\nDashboard YTD figure from debug output: $161,645.85 sales, 2476 orders\n")
    
    # First show ALL TIME data
    print("="*80)
    print("ALL TIME DATA")
    print("="*80)
    print(f"{'STORE':<12} | {'ORDERS':<10} | {'PAYMENTS':<10} | {'SALES':<15} | {'AVG ORDER':<10}")
    print("-"*80)
    
    for store_id, store_name in stores:
        # Get order count from order_items
        cursor.execute("""
            SELECT COUNT(DISTINCT order_id) 
            FROM order_items 
            WHERE store_id = ?
        """, (store_id,))
        order_count = cursor.fetchone()[0] or 0
        
        # Get payment count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM payments 
            WHERE store_id = ?
        """, (store_id,))
        payment_count = cursor.fetchone()[0] or 0
        
        # Get total sales using COALESCE for quantity
        cursor.execute("""
            SELECT SUM(price * COALESCE(quantity, 1)) 
            FROM order_items 
            WHERE store_id = ?
        """, (store_id,))
        sales = cursor.fetchone()[0] or 0
        
        # Calculate average order value
        avg_order = sales / order_count if order_count > 0 else 0
        
        print(f"{store_name:<12} | {order_count:<10,} | {payment_count:<10,} | ${sales:<14,.2f} | ${avg_order:<9,.2f}")
    
    # Get totals
    cursor.execute("SELECT COUNT(DISTINCT order_id) FROM order_items")
    total_orders = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM payments")
    total_payments = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(price * COALESCE(quantity, 1)) FROM order_items")
    total_sales = cursor.fetchone()[0] or 0
    
    # Calculate overall average order value
    overall_avg = total_sales / total_orders if total_orders > 0 else 0
    
    print("-"*80)
    print(f"{'TOTAL':<12} | {total_orders:<10,} | {total_payments:<10,} | ${total_sales:<14,.2f} | ${overall_avg:<9,.2f}")
    print("="*80)
    
    # Now get the total YTD (2025) data to match dashboard
    print("\nYEAR-TO-DATE (2025) DATA - Should match dashboard")
    print("="*80)
    print(f"{'STORE':<12} | {'ORDERS':<10} | {'PAYMENTS':<10} | {'SALES':<15} | {'AVG ORDER':<10}")
    print("-"*80)
    
    # Get total YTD figures (direct match to dashboard query)
    cursor.execute("""
        SELECT COUNT(DISTINCT order_id) as orders, SUM(price * COALESCE(quantity, 1)) as sales
        FROM order_items
        WHERE created_time >= '2025-01-01 00:00:00'
    """)
    ytd_result = cursor.fetchone()
    ytd_orders = ytd_result[0] or 0
    ytd_sales = ytd_result[1] or 0
    
    # Get per-store YTD data
    store_ytd_data = []
    for store_id, store_name in stores:
        cursor.execute("""
            SELECT COUNT(DISTINCT order_id) as order_count,
                   SUM(price * COALESCE(quantity, 1)) as sales_total
            FROM order_items 
            WHERE store_id = ? AND created_time >= '2025-01-01'
        """, (store_id,))
        store_ytd = cursor.fetchone()
        
        store_ytd_orders = store_ytd[0] or 0
        store_ytd_sales = store_ytd[1] or 0
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM payments 
            WHERE store_id = ? AND created_time >= '2025-01-01'
        """, (store_id,))
        store_ytd_payments = cursor.fetchone()[0] or 0
        
        avg_ytd_order = store_ytd_sales / store_ytd_orders if store_ytd_orders > 0 else 0
        
        store_ytd_data.append((store_name, store_ytd_orders, store_ytd_payments, store_ytd_sales, avg_ytd_order))
        print(f"{store_name:<12} | {store_ytd_orders:<10,} | {store_ytd_payments:<10,} | ${store_ytd_sales:<14,.2f} | ${avg_ytd_order:<9,.2f}")
    
    # Calculate totals
    total_ytd_orders = sum(data[1] for data in store_ytd_data)
    total_ytd_payments = sum(data[2] for data in store_ytd_data)
    total_ytd_sales = sum(data[3] for data in store_ytd_data)
    avg_ytd_order = total_ytd_sales / total_ytd_orders if total_ytd_orders > 0 else 0
    
    print("-"*80)
    print(f"{'TOTAL':<12} | {total_ytd_orders:<10,} | {total_ytd_payments:<10,} | ${total_ytd_sales:<14,.2f} | ${avg_ytd_order:<9,.2f}")
    print("-"*80)
    
    # Double check with direct query for full YTD data
    print(f"Dashboard query: {ytd_orders} orders, ${ytd_sales:,.2f} sales\n")
    
    # Get order count by day for the past 7 days
    print("Order counts by date (last 7 days):")
    cursor.execute("""
        SELECT DATE(created_time) as order_date, COUNT(DISTINCT order_id) as order_count
        FROM order_items
        WHERE created_time >= date('now', '-7 days')
        GROUP BY order_date
        ORDER BY order_date DESC
    """)
    
    date_counts = cursor.fetchall()
    if date_counts:
        for date, count in date_counts:
            print(f"  {date}: {count} orders")
    else:
        print("  No orders in the last 7 days")
    
    conn.close()

if __name__ == "__main__":
    get_store_stats() 