import sqlite3
import os
import pandas as pd
from datetime import datetime

def create_database():
    """Create SQLite database with required tables if they don't exist"""
    
    # Create database file if it doesn't exist
    if not os.path.exists('clover_dashboard.db'):
        print("Creating new database...")
    
    conn = sqlite3.connect('clover_dashboard.db')
    cursor = conn.cursor()
    
    # Create stores table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        merchant_id TEXT UNIQUE,
        name TEXT,
        access_token TEXT,
        last_sync_date TEXT
    )
    ''')
    
    # Create payments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        payment_id TEXT PRIMARY KEY,
        store_id INTEGER,
        amount REAL,
        created_time TEXT,
        employee_id TEXT,
        order_id TEXT,
        device_id TEXT,
        tender_type TEXT,
        card_type TEXT,
        last_4 TEXT,
        sync_date TEXT,
        FOREIGN KEY (store_id) REFERENCES stores(id)
    )
    ''')
    
    # Create order_items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        item_id TEXT,
        store_id INTEGER,
        name TEXT,
        price REAL,
        quantity INTEGER,
        created_time TEXT,
        employee_id TEXT,
        is_refunded TEXT,
        discount_amount REAL,
        sync_date TEXT,
        FOREIGN KEY (store_id) REFERENCES stores(id)
    )
    ''')
    
    # Create expenses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER,
        amount REAL,
        category TEXT,
        description TEXT,
        date TEXT,
        created_at TEXT,
        FOREIGN KEY (store_id) REFERENCES stores(id)
    )
    ''')
    
    # Create sync_log table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sync_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER,
        sync_date TEXT,
        payments_count INTEGER,
        orders_count INTEGER,
        FOREIGN KEY (store_id) REFERENCES stores(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database setup complete.")

def save_store(merchant_id, name, access_token):
    """Save or update store information in the database"""
    conn = sqlite3.connect('clover_dashboard.db')
    cursor = conn.cursor()
    
    # Check if store exists
    cursor.execute("SELECT id FROM stores WHERE merchant_id = ?", (merchant_id,))
    result = cursor.fetchone()
    
    if result:
        # Update existing store
        cursor.execute(
            "UPDATE stores SET name = ?, access_token = ? WHERE merchant_id = ?", 
            (name, access_token, merchant_id)
        )
        store_id = result[0]
    else:
        # Insert new store
        cursor.execute(
            "INSERT INTO stores (merchant_id, name, access_token) VALUES (?, ?, ?)",
            (merchant_id, name, access_token)
        )
        store_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return store_id

def save_payments(payments_data, store_id):
    """Save payments data to database, converting cents to dollars"""
    if not payments_data:
        print("No payments data to save")
        return 0
        
    conn = sqlite3.connect('clover_dashboard.db')
    cursor = conn.cursor()
    
    # Convert to DataFrame
    df = pd.DataFrame(payments_data)
    
    # Add store_id and sync_date
    current_date = datetime.now().strftime('%Y-%m-%d')
    df['store_id'] = store_id
    df['sync_date'] = current_date
    
    # Convert cents to dollars for monetary values
    if 'amount' in df.columns:
        df['amount'] = df['amount'] / 100.0
    
    # Check which payment_ids already exist in the database
    existing_payment_ids = []
    if not df.empty:
        payment_ids = df['payment_id'].tolist()
        placeholders = ','.join(['?' for _ in payment_ids])
        cursor.execute(f"SELECT payment_id FROM payments WHERE payment_id IN ({placeholders})", payment_ids)
        existing_payment_ids = [row[0] for row in cursor.fetchall()]
    
    # Split the dataframe into new and existing payments
    if existing_payment_ids:
        new_payments = df[~df['payment_id'].isin(existing_payment_ids)]
        print(f"Skipping {len(existing_payment_ids)} existing payments")
    else:
        new_payments = df
    
    # Only insert new payments
    if not new_payments.empty:
        new_payments.to_sql('payments', conn, if_exists='append', index=False)
        print(f"Added {len(new_payments)} new payments")
    
    count = len(df)  # Return total processed count
    conn.close()
    return count

def save_order_items(order_items_data, store_id):
    """Save order items data to database, converting cents to dollars"""
    if not order_items_data:
        print("No order items data to save")
        return 0
        
    conn = sqlite3.connect('clover_dashboard.db')
    cursor = conn.cursor()
    
    # Convert to DataFrame
    df = pd.DataFrame(order_items_data)
    
    # Add store_id and sync_date
    current_date = datetime.now().strftime('%Y-%m-%d')
    df['store_id'] = store_id
    df['sync_date'] = current_date
    
    # Convert cents to dollars for monetary values
    if 'price' in df.columns:
        df['price'] = df['price'] / 100.0
    if 'discount_amount' in df.columns:
        df['discount_amount'] = df['discount_amount'] / 100.0
    
    # Check which items already exist (using order_id and item_id combination)
    existing_items = []
    if not df.empty and 'order_id' in df.columns and 'item_id' in df.columns:
        # Create a unique identifier for each item
        df['item_key'] = df['order_id'] + '_' + df['item_id']
        
        # Get all possible item keys
        item_keys = df['item_key'].tolist()
        
        # Check which ones already exist
        for i in range(0, len(item_keys), 100):  # Process in batches to avoid huge SQL queries
            batch = item_keys[i:i+100]
            placeholders = ','.join(['?' for _ in batch])
            cursor.execute(f"""
                SELECT order_id || '_' || item_id as item_key 
                FROM order_items 
                WHERE order_id || '_' || item_id IN ({placeholders})
            """, batch)
            existing_items.extend([row[0] for row in cursor.fetchall()])
    
    # Filter out existing items
    if existing_items:
        new_items = df[~df['item_key'].isin(existing_items)]
        print(f"Skipping {len(existing_items)} existing order items")
        
        # Remove the temporary item_key column before saving
        if 'item_key' in new_items.columns:
            new_items = new_items.drop(columns=['item_key'])
    else:
        new_items = df
        # Remove the temporary item_key column if it exists
        if 'item_key' in new_items.columns:
            new_items = new_items.drop(columns=['item_key'])
    
    # Only insert new items
    if not new_items.empty:
        new_items.to_sql('order_items', conn, if_exists='append', index=False)
        print(f"Added {len(new_items)} new order items")
    
    count = len(df)  # Return total processed count
    conn.close()
    return count

def log_sync(store_id, payments_count, orders_count):
    """Log synchronization activity"""
    conn = sqlite3.connect('clover_dashboard.db')
    cursor = conn.cursor()
    
    sync_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        "INSERT INTO sync_log (store_id, sync_date, payments_count, orders_count) VALUES (?, ?, ?, ?)",
        (store_id, sync_date, payments_count, orders_count)
    )
    
    # Update last_sync_date in stores table
    cursor.execute(
        "UPDATE stores SET last_sync_date = ? WHERE id = ?",
        (sync_date, store_id)
    )
    
    conn.commit()
    conn.close()

def get_last_sync_date(store_id):
    """Get the last synchronization date for a store"""
    conn = sqlite3.connect('clover_dashboard.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT last_sync_date FROM stores WHERE id = ?", (store_id,))
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result and result[0] else None

def get_all_stores():
    """Get list of all stores in the database"""
    conn = sqlite3.connect('clover_dashboard.db')
    stores = pd.read_sql("SELECT * FROM stores", conn)
    conn.close()
    return stores

def get_store_sales(store_id=None, start_date=None, end_date=None):
    """Get sales data for visualization"""
    conn = sqlite3.connect('clover_dashboard.db')
    
    query = """
    SELECT 
        p.store_id,
        s.name as store_name,
        strftime('%Y-%m-%d', p.created_time) as date,
        SUM(p.amount) as daily_sales
    FROM 
        payments p
    JOIN
        stores s ON p.store_id = s.id
    """
    
    params = []
    where_clauses = []
    
    if store_id:
        where_clauses.append("p.store_id = ?")
        params.append(store_id)
    
    if start_date:
        where_clauses.append("p.created_time >= ?")
        params.append(start_date)
    
    if end_date:
        where_clauses.append("p.created_time <= ?")
        params.append(end_date)
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    query += " GROUP BY p.store_id, date ORDER BY date"
    
    sales_data = pd.read_sql(query, conn, params=params)
    conn.close()
    
    return sales_data

def get_store_expenses(store_id=None, start_date=None, end_date=None):
    """Get expense data for visualization"""
    conn = sqlite3.connect('clover_dashboard.db')
    
    query = """
    SELECT 
        e.store_id,
        s.name as store_name,
        e.date,
        SUM(e.amount) as daily_expenses,
        e.category
    FROM 
        expenses e
    JOIN
        stores s ON e.store_id = s.id
    """
    
    params = []
    where_clauses = []
    
    if store_id:
        where_clauses.append("e.store_id = ?")
        params.append(store_id)
    
    if start_date:
        where_clauses.append("e.date >= ?")
        params.append(start_date)
    
    if end_date:
        where_clauses.append("e.date <= ?")
        params.append(end_date)
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    query += " GROUP BY e.store_id, e.date, e.category ORDER BY e.date"
    
    expenses_data = pd.read_sql(query, conn, params=params)
    conn.close()
    
    return expenses_data

def save_expense(store_id, amount, category, description, date):
    """
    Save a new expense entry to the database
    
    Args:
        store_id (int): ID of the store
        amount (float): Expense amount
        category (str): Expense category (rent, salary, purchase, other)
        description (str): Description of the expense
        date (str): Date of the expense in YYYY-MM-DD format
    
    Returns:
        int: ID of the newly created expense
    """
    conn = sqlite3.connect('clover_dashboard.db')
    cursor = conn.cursor()
    
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        "INSERT INTO expenses (store_id, amount, category, description, date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (store_id, amount, category, description, date, created_at)
    )
    
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return expense_id

def get_expense_categories():
    """Get list of predefined expense categories"""
    return ["Rent", "Utilities", "Salary", "Inventory", "Equipment", "Marketing", "Insurance", "Taxes", "Other"]

def get_store_expenses_by_period(store_id=None, start_date=None, end_date=None):
    """
    Get total expenses for a store or all stores within a date range
    
    Args:
        store_id (int, optional): Store ID to filter by
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        
    Returns:
        float: Total expenses amount
    """
    conn = sqlite3.connect('clover_dashboard.db')
    cursor = conn.cursor()
    
    query = "SELECT SUM(amount) FROM expenses WHERE 1=1"
    params = []
    
    if store_id:
        query += " AND store_id = ?"
        params.append(store_id)
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    
    cursor.execute(query, params)
    result = cursor.fetchone()
    total_expenses = result[0] if result and result[0] is not None else 0
    
    conn.close()
    return total_expenses 