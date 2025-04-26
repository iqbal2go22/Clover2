"""
Cloud Database Utilities for Supabase
This module provides database utilities for interacting with a PostgreSQL database on Supabase.
It's a drop-in replacement for db_utils.py but uses Supabase instead of SQLite.
"""

import pandas as pd
from sqlalchemy import create_engine, text
import datetime
import streamlit as st
import os
import time
import json
import requests

# Supabase connection strings - for development and testing
# In production, these will be loaded from Streamlit secrets
# Connection pooling URL (port 6543)
POOLING_URL = "postgresql://postgres.yegrbbtxlsfbrlyavmbg:721AFFTNZmnQ3An7@yegrbbtxlsfbrlyavmbg.supabase.co:6543/postgres"
# Direct connection URL (port 5432)
DIRECT_URL = "postgresql://postgres:721AFFTNZmnQ3An7@db.yegrbbtxlsfbrlyavmbg.supabase.co:5432/postgres"

def get_db_connection(max_retries=3, retry_delay=1):
    """
    Get a database connection to Supabase PostgreSQL.
    
    This function will try the connection pooling URL first, then fall back to the direct connection
    if that fails. It will retry up to max_retries times with a delay between attempts.
    """
    if hasattr(st, 'secrets') and 'supabase' in st.secrets:
        # Use connection strings from Streamlit secrets in production
        pooling_url = st.secrets["supabase"].get("pooling_url", st.secrets["supabase"]["url"])
        direct_url = st.secrets["supabase"].get("direct_url", None)  # Use if provided
    else:
        # Fall back to hardcoded connection strings for development
        pooling_url = POOLING_URL
        direct_url = DIRECT_URL
    
    # Try connection pooling first (faster, more efficient)
    for attempt in range(max_retries):
        try:
            # Create a connection to the database using connection pooling
            engine = create_engine(pooling_url, connect_args={"connect_timeout": 10})
            conn = engine.connect()
            print(f"Connected to Supabase using connection pooling (attempt {attempt + 1})")
            return conn
        except Exception as e:
            if "timeout" in str(e).lower() or "connection refused" in str(e).lower():
                print(f"Connection pooling attempt {attempt + 1} failed with timeout: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
            else:
                # Other error that's not a timeout
                print(f"Connection pooling error (non-timeout): {str(e)}")
                break  # Try direct connection
    
    # If connection pooling fails or direct_url is None, try direct connection
    if direct_url:
        for attempt in range(max_retries):
            try:
                # Try direct connection as a fallback
                engine = create_engine(direct_url, connect_args={"connect_timeout": 15})
                conn = engine.connect()
                print(f"Connected to Supabase using direct connection (attempt {attempt + 1})")
                return conn
            except Exception as e:
                print(f"Direct connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                
    # If we get here, both connection methods failed
    raise Exception("Failed to connect to Supabase database after multiple attempts")

def create_database():
    """Create the necessary tables in the database if they don't exist."""
    conn = get_db_connection()
    
    try:
        # Create stores table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS stores (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            merchant_id TEXT NOT NULL,
            api_key TEXT,
            access_token TEXT,
            last_sync_date TIMESTAMP
        )
        """))
        
        # Create payments table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            store_id INTEGER,
            order_id TEXT,
            amount INTEGER,
            created_time TIMESTAMP
        )
        """))
        
        # Create order_items table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS order_items (
            id TEXT PRIMARY KEY,
            store_id INTEGER, 
            order_id TEXT,
            name TEXT,
            price REAL,
            quantity INTEGER,
            created_time TIMESTAMP
        )
        """))
        
        # Create expenses table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            store_id INTEGER,
            date DATE,
            amount REAL,
            category TEXT,
            description TEXT
        )
        """))
        
        # Create sync_log table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id SERIAL PRIMARY KEY,
            store_id INTEGER,
            sync_date TIMESTAMP,
            items_count INTEGER
        )
        """))
        
        # Commit the transaction
        conn.commit()
    finally:
        conn.close()

def get_sql_connection():
    """Get the Supabase SQL connection."""
    return st.connection("supabase_sql")

def get_all_stores():
    """Get all stores from Supabase."""
    conn = get_sql_connection()
    try:
        return conn.query("SELECT * FROM stores ORDER BY name;")
    except Exception as e:
        st.error(f"Error fetching stores: {str(e)}")
        return pd.DataFrame()

def get_store_by_id(store_id):
    """Get store information by ID."""
    conn = get_sql_connection()
    try:
        df = conn.query(f"SELECT * FROM stores WHERE merchant_id = '{store_id}';")
        if not df.empty:
            return df.iloc[0].to_dict()
        return None
    except Exception as e:
        st.error(f"Error fetching store {store_id}: {str(e)}")
        return None

def get_orders_by_date_range(start_date, end_date, store_id=None):
    """Get orders within a date range, optionally filtered by store ID."""
    conn = get_sql_connection()
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    query = f"""
        SELECT * FROM order_items 
        WHERE DATE(created_at) BETWEEN '{start_str}' AND '{end_str}'
    """
    
    if store_id:
        query += f" AND merchant_id = '{store_id}'"
        
    try:
        return conn.query(query)
    except Exception as e:
        st.error(f"Error fetching orders: {str(e)}")
        return pd.DataFrame()

def get_payments_by_date_range(start_date, end_date, store_id=None):
    """Get payments within a date range, optionally filtered by store ID."""
    conn = get_sql_connection()
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    query = f"""
        SELECT * FROM payments 
        WHERE DATE(created_at) BETWEEN '{start_str}' AND '{end_str}'
    """
    
    if store_id:
        query += f" AND merchant_id = '{store_id}'"
        
    try:
        return conn.query(query)
    except Exception as e:
        st.error(f"Error fetching payments: {str(e)}")
        return pd.DataFrame()

def get_store_expenses(store_id):
    """Get expenses for a specific store."""
    conn = get_sql_connection()
    try:
        return conn.query(f"SELECT * FROM expenses WHERE store_id = '{store_id}' ORDER BY date DESC;")
    except Exception as e:
        st.error(f"Error fetching expenses: {str(e)}")
        return pd.DataFrame()

def add_expense(store_id, date, amount, category, description):
    """Add a new expense for a store."""
    conn = get_sql_connection()
    
    date_str = date.strftime("%Y-%m-%d")
    now_str = datetime.now().isoformat()
    
    query = f"""
        INSERT INTO expenses 
        (store_id, date, amount, category, description, created_at)
        VALUES 
        ('{store_id}', '{date_str}', {float(amount)}, '{category}', '{description}', '{now_str}')
        RETURNING id;
    """
    
    try:
        result = conn.query(query)
        return len(result) > 0
    except Exception as e:
        st.error(f"Error adding expense: {str(e)}")
        return False

def update_expense(expense_id, date, amount, category, description):
    """Update an existing expense."""
    conn = get_sql_connection()
    
    date_str = date.strftime("%Y-%m-%d")
    now_str = datetime.now().isoformat()
    
    query = f"""
        UPDATE expenses
        SET date = '{date_str}', 
            amount = {float(amount)}, 
            category = '{category}', 
            description = '{description}', 
            updated_at = '{now_str}'
        WHERE id = {expense_id}
        RETURNING id;
    """
    
    try:
        result = conn.query(query)
        return len(result) > 0
    except Exception as e:
        st.error(f"Error updating expense: {str(e)}")
        return False

def delete_expense(expense_id):
    """Delete an expense."""
    conn = get_sql_connection()
    
    query = f"""
        DELETE FROM expenses
        WHERE id = {expense_id}
        RETURNING id;
    """
    
    try:
        result = conn.query(query)
        return len(result) > 0
    except Exception as e:
        st.error(f"Error deleting expense: {str(e)}")
        return False

def get_last_sync_time():
    """Get the last time data was synced."""
    conn = get_sql_connection()
    
    try:
        df = conn.query("SELECT sync_time FROM sync_log ORDER BY sync_time DESC LIMIT 1;")
        if not df.empty:
            return pd.to_datetime(df.iloc[0]['sync_time'])
        return None
    except Exception as e:
        st.error(f"Error fetching last sync time: {str(e)}")
        return None

def update_sync_log(sync_time=None):
    """Update the sync log with current time."""
    if sync_time is None:
        sync_time = datetime.now()
        
    conn = get_sql_connection()
    sync_time_str = sync_time.isoformat()
    
    query = f"""
        INSERT INTO sync_log (sync_time, status)
        VALUES ('{sync_time_str}', 'completed')
        RETURNING id;
    """
    
    try:
        result = conn.query(query)
        return len(result) > 0
    except Exception as e:
        st.error(f"Error updating sync log: {str(e)}")
        return False

def execute_raw_query(query_text, params=None):
    """Execute a raw SQL query.
    
    Args:
        query_text: SQL query to execute
        params: Parameters for the query (not used in this implementation)
        
    Returns:
        DataFrame with query results
    """
    conn = get_sql_connection()
    
    try:
        return conn.query(query_text)
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
        return pd.DataFrame()

def save_expense(store_id, amount, category, description, date):
    """Save an expense to the database."""
    conn = get_db_connection()
    try:
        # Insert expense
        query = text("""
        INSERT INTO expenses (store_id, amount, category, description, date)
        VALUES (:store_id, :amount, :category, :description, :date)
        RETURNING id
        """)
        
        result = conn.execute(query, {
            'store_id': store_id,
            'amount': amount,
            'category': category,
            'description': description,
            'date': date
        })
        
        # Get the ID of the inserted expense
        expense_id = result.fetchone()[0]
        conn.commit()
        return expense_id
    finally:
        conn.close()

def get_expense_categories():
    """Get all expense categories."""
    return ["Rent", "Utilities", "Salaries", "Inventory", "Marketing", "Insurance", "Taxes", "Maintenance", "Supplies", "Other"]

def get_store_expenses_by_period(store_id=None, start_date=None, end_date=None):
    """Get store expenses for a given period."""
    conn = get_db_connection()
    try:
        # Build query based on parameters
        query_parts = ["SELECT SUM(amount) FROM expenses WHERE 1=1"]
        params = {}
        
        if store_id:
            query_parts.append("AND store_id = :store_id")
            params['store_id'] = store_id
        
        if start_date:
            query_parts.append("AND date >= :start_date")
            params['start_date'] = start_date
        
        if end_date:
            query_parts.append("AND date <= :end_date")
            params['end_date'] = end_date
        
        # Execute the query
        query = text(" ".join(query_parts))
        result = conn.execute(query, params)
        amount = result.fetchone()[0]
        
        # Return 0 if no expenses found
        return amount or 0
    finally:
        conn.close()

def save_store(name, merchant_id, api_key, access_token):
    """Save a store to the database."""
    conn = get_db_connection()
    try:
        # Check if store already exists
        check_query = text("SELECT id FROM stores WHERE merchant_id = :merchant_id")
        result = conn.execute(check_query, {'merchant_id': merchant_id})
        existing = result.fetchone()
        
        if existing:
            # Update existing store
            update_query = text("""
            UPDATE stores
            SET name = :name, api_key = :api_key, access_token = :access_token
            WHERE merchant_id = :merchant_id
            RETURNING id
            """)
            
            result = conn.execute(update_query, {
                'name': name,
                'merchant_id': merchant_id,
                'api_key': api_key,
                'access_token': access_token
            })
            store_id = result.fetchone()[0]
        else:
            # Insert new store
            insert_query = text("""
            INSERT INTO stores (name, merchant_id, api_key, access_token)
            VALUES (:name, :merchant_id, :api_key, :access_token)
            RETURNING id
            """)
            
            result = conn.execute(insert_query, {
                'name': name,
                'merchant_id': merchant_id,
                'api_key': api_key,
                'access_token': access_token
            })
            store_id = result.fetchone()[0]
        
        conn.commit()
        return store_id
    finally:
        conn.close()

def get_store_data_by_id(store_id):
    """Get store data by ID."""
    conn = get_db_connection()
    try:
        query = text("SELECT * FROM stores WHERE id = :store_id")
        df = pd.read_sql(query, conn, params={'store_id': store_id})
        return df.iloc[0] if not df.empty else None
    finally:
        conn.close()

def update_store_sync_date(store_id, sync_date=None):
    """Update the last sync date for a store."""
    if sync_date is None:
        sync_date = datetime.datetime.now()
    
    conn = get_db_connection()
    try:
        query = text("""
        UPDATE stores
        SET last_sync_date = :sync_date
        WHERE id = :store_id
        """)
        
        conn.execute(query, {
            'store_id': store_id,
            'sync_date': sync_date
        })
        
        conn.commit()
    finally:
        conn.close()

def save_payment(store_id, payment_id, order_id, amount, created_time):
    """Save a payment to the database."""
    conn = get_db_connection()
    try:
        # Check if payment already exists
        check_query = text("SELECT id FROM payments WHERE id = :payment_id")
        result = conn.execute(check_query, {'payment_id': payment_id})
        existing = result.fetchone()
        
        if not existing:
            # Insert new payment
            query = text("""
            INSERT INTO payments (id, store_id, order_id, amount, created_time)
            VALUES (:payment_id, :store_id, :order_id, :amount, :created_time)
            """)
            
            conn.execute(query, {
                'payment_id': payment_id,
                'store_id': store_id,
                'order_id': order_id,
                'amount': amount,
                'created_time': created_time
            })
            
            conn.commit()
    finally:
        conn.close()

def save_order_item(store_id, item_id, order_id, name, price, quantity, created_time):
    """Save an order item to the database."""
    conn = get_db_connection()
    try:
        # Check if order item already exists
        check_query = text("SELECT id FROM order_items WHERE id = :item_id")
        result = conn.execute(check_query, {'item_id': item_id})
        existing = result.fetchone()
        
        if not existing:
            # Insert new order item
            query = text("""
            INSERT INTO order_items (id, store_id, order_id, name, price, quantity, created_time)
            VALUES (:item_id, :store_id, :order_id, :name, :price, :quantity, :created_time)
            """)
            
            conn.execute(query, {
                'item_id': item_id,
                'store_id': store_id,
                'order_id': order_id,
                'name': name,
                'price': price,
                'quantity': quantity,
                'created_time': created_time
            })
            
            conn.commit()
    finally:
        conn.close()

def save_sync_log(store_id, items_count, sync_date=None):
    """Save a sync log entry."""
    if sync_date is None:
        sync_date = datetime.datetime.now()
    
    conn = get_db_connection()
    try:
        query = text("""
        INSERT INTO sync_log (store_id, items_count, sync_date)
        VALUES (:store_id, :items_count, :sync_date)
        """)
        
        conn.execute(query, {
            'store_id': store_id,
            'items_count': items_count,
            'sync_date': sync_date
        })
        
        conn.commit()
    finally:
        conn.close()

def clear_orders_for_store(store_id):
    """Clear all orders for a store."""
    conn = get_db_connection()
    try:
        # Delete order items
        conn.execute(text("DELETE FROM order_items WHERE store_id = :store_id"), {'store_id': store_id})
        
        # Delete payments
        conn.execute(text("DELETE FROM payments WHERE store_id = :store_id"), {'store_id': store_id})
        
        # Delete sync logs
        conn.execute(text("DELETE FROM sync_log WHERE store_id = :store_id"), {'store_id': store_id})
        
        conn.commit()
    finally:
        conn.close()

def get_connection():
    """Get the Supabase connection."""
    return st.connection("supabase")

def get_orders_by_date_range(start_date, end_date, store_id=None):
    """Get orders within a date range, optionally filtered by store ID."""
    conn = get_connection()
    
    # Format dates for Supabase filtering
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    try:
        filters = {"created_at": f"gte.{start_str}", "created_at": f"lte.{end_str}"}
        if store_id:
            filters["merchant_id"] = f"eq.{store_id}"
            
        return conn.query("order_items", columns="*", filters=filters)
    except Exception as e:
        st.error(f"Error fetching orders: {str(e)}")
        return pd.DataFrame()

def get_payments_by_date_range(start_date, end_date, store_id=None):
    """Get payments within a date range, optionally filtered by store ID."""
    conn = get_connection()
    
    # Format dates for Supabase filtering
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    try:
        filters = {"created_at": f"gte.{start_str}", "created_at": f"lte.{end_str}"}
        if store_id:
            filters["merchant_id"] = f"eq.{store_id}"
            
        return conn.query("payments", columns="*", filters=filters)
    except Exception as e:
        st.error(f"Error fetching payments: {str(e)}")
        return pd.DataFrame()

def get_store_expenses(store_id):
    """Get expenses for a specific store."""
    conn = get_connection()
    try:
        filters = {"store_id": f"eq.{store_id}"}
        return conn.query("expenses", columns="*", filters=filters)
    except Exception as e:
        st.error(f"Error fetching expenses: {str(e)}")
        return pd.DataFrame()

def add_expense(store_id, date, amount, category, description):
    """Add a new expense for a store."""
    conn = get_connection()
    
    data = {
        "store_id": store_id,
        "date": date.strftime("%Y-%m-%d"),
        "amount": float(amount),
        "category": category,
        "description": description,
        "created_at": datetime.now().isoformat()
    }
    
    try:
        result = conn.insert("expenses", data)
        return result["success"]
    except Exception as e:
        st.error(f"Error adding expense: {str(e)}")
        return False

def update_expense(expense_id, date, amount, category, description):
    """Update an existing expense."""
    conn = get_connection()
    
    data = {
        "date": date.strftime("%Y-%m-%d"),
        "amount": float(amount),
        "category": category,
        "description": description,
        "updated_at": datetime.now().isoformat()
    }
    
    try:
        filters = {"id": f"eq.{expense_id}"}
        result = conn.update("expenses", data, filters)
        return result["success"]
    except Exception as e:
        st.error(f"Error updating expense: {str(e)}")
        return False

def delete_expense(expense_id):
    """Delete an expense."""
    conn = get_connection()
    
    try:
        filters = {"id": f"eq.{expense_id}"}
        result = conn.delete("expenses", filters)
        return result["success"]
    except Exception as e:
        st.error(f"Error deleting expense: {str(e)}")
        return False

def get_last_sync_time():
    """Get the last time data was synced."""
    conn = get_connection()
    
    try:
        df = conn.query("sync_log", columns="*", limit=1)
        if not df.empty:
            return datetime.fromisoformat(df.iloc[0]["sync_time"])
        return None
    except Exception as e:
        st.error(f"Error fetching last sync time: {str(e)}")
        return None

def update_sync_log(sync_time=None):
    """Update the sync log with current time."""
    if sync_time is None:
        sync_time = datetime.now()
        
    conn = get_connection()
    
    data = {
        "sync_time": sync_time.isoformat(),
        "status": "completed"
    }
    
    try:
        result = conn.insert("sync_log", data)
        return result["success"]
    except Exception as e:
        st.error(f"Error updating sync log: {str(e)}")
        return False

def execute_raw_query(query_text, params=None):
    """Execute a raw SQL query via RPC function.
    
    Note: This requires setting up an RPC function in Supabase.
    """
    conn = get_connection()
    
    try:
        rpc_url = f"{conn.project_url}/rest/v1/rpc/execute_query"
        payload = {
            "query_text": query_text,
            "params": json.dumps(params) if params else "[]"
        }
        
        response = requests.post(
            rpc_url,
            headers=conn.headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code in (200, 201):
            result = response.json()
            return pd.DataFrame(result) if result else pd.DataFrame()
        else:
            st.error(f"Query execution failed: {response.status_code} - {response.text}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
        return pd.DataFrame()

def get_supabase_client():
    """Get Supabase connection details from secrets"""
    if not hasattr(st.session_state, "supabase_client"):
        # Get connection details from secrets
        project_url = st.secrets.connections.supabase.get("project_url")
        api_key = st.secrets.connections.supabase.get("api_key")
        
        # Set up headers for Supabase REST API
        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        st.session_state.supabase_client = {
            "project_url": project_url,
            "headers": headers
        }
    
    return st.session_state.supabase_client

def execute_query(query, params=None):
    """Execute a REST query against Supabase"""
    client = get_supabase_client()
    url = f"{client['project_url']}/rest/v1/{query}"
    
    try:
        response = requests.get(url, headers=client["headers"], params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None

def execute_post(endpoint, data):
    """Execute a POST request against Supabase"""
    client = get_supabase_client()
    url = f"{client['project_url']}/rest/v1/{endpoint}"
    
    try:
        response = requests.post(url, headers=client["headers"], json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None

def execute_update(endpoint, data, id_value):
    """Execute a PATCH request against Supabase"""
    client = get_supabase_client()
    url = f"{client['project_url']}/rest/v1/{endpoint}?id=eq.{id_value}"
    
    try:
        # Add the prefer header to return the updated record
        headers = {**client["headers"], "Prefer": "return=representation"}
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None

def execute_delete(endpoint, id_value):
    """Execute a DELETE request against Supabase"""
    client = get_supabase_client()
    url = f"{client['project_url']}/rest/v1/{endpoint}?id=eq.{id_value}"
    
    try:
        headers = {**client["headers"], "Prefer": "return=representation"}
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return False

def get_store_by_merchant_id(merchant_id):
    """Get a store by merchant ID"""
    results = execute_query(f"stores?merchant_id=eq.{merchant_id}")
    if results and len(results) > 0:
        return results[0]
    return None

def update_store_last_sync(merchant_id, sync_date=None):
    """Update the last sync date for a store"""
    if sync_date is None:
        sync_date = datetime.now().isoformat()
    
    store = get_store_by_merchant_id(merchant_id)
    if store:
        execute_update("stores", {"last_sync_date": sync_date}, store["id"])
        return True
    return False

def get_payments_by_merchant(merchant_id, start_date=None, end_date=None):
    """Get payments for a merchant with optional date range"""
    query = f"payments?merchant_id=eq.{merchant_id}"
    
    if start_date and end_date:
        # Format dates as ISO strings for the API
        start_iso = start_date.isoformat() if isinstance(start_date, datetime) else start_date
        end_iso = end_date.isoformat() if isinstance(end_date, datetime) else end_date
        query += f"&created_at=gte.{start_iso}&created_at=lte.{end_iso}"
    
    results = execute_query(query)
    if results:
        return pd.DataFrame(results)
    return pd.DataFrame()

def get_payments_count_by_merchant(merchant_id, start_date=None, end_date=None):
    """Get count of payments for a merchant with optional date range"""
    query = f"payments?merchant_id=eq.{merchant_id}&select=id"
    
    if start_date and end_date:
        start_iso = start_date.isoformat() if isinstance(start_date, datetime) else start_date
        end_iso = end_date.isoformat() if isinstance(end_date, datetime) else end_date
        query += f"&created_at=gte.{start_iso}&created_at=lte.{end_iso}"
    
    # Use the prefer header to get count
    client = get_supabase_client()
    url = f"{client['project_url']}/rest/v1/{query}"
    
    try:
        headers = {**client["headers"], "Prefer": "count=exact"}
        response = requests.get(url, headers=headers)
        
        if "content-range" in response.headers:
            count = response.headers["content-range"].split("/")[1]
            return int(count)
        return 0
    except Exception as e:
        st.error(f"Error getting payment count: {str(e)}")
        return 0

def save_payments(payments_data):
    """Save multiple payments to the database"""
    if not payments_data or len(payments_data) == 0:
        return 0
    
    # Convert payments to list of dicts if it's a DataFrame
    if isinstance(payments_data, pd.DataFrame):
        payments_list = payments_data.to_dict('records')
    else:
        payments_list = payments_data
    
    # Insert in batches of 50
    batch_size = 50
    success_count = 0
    
    for i in range(0, len(payments_list), batch_size):
        batch = payments_list[i:i+batch_size]
        result = execute_post("payments", batch)
        if result:
            success_count += len(result)
    
    return success_count

def get_order_items_by_merchant(merchant_id, start_date=None, end_date=None):
    """Get order items for a merchant with optional date range"""
    query = f"order_items?merchant_id=eq.{merchant_id}"
    
    if start_date and end_date:
        start_iso = start_date.isoformat() if isinstance(start_date, datetime) else start_date
        end_iso = end_date.isoformat() if isinstance(end_date, datetime) else end_date
        query += f"&created_at=gte.{start_iso}&created_at=lte.{end_iso}"
    
    results = execute_query(query)
    if results:
        return pd.DataFrame(results)
    return pd.DataFrame()

def save_order_items(items_data):
    """Save multiple order items to the database"""
    if not items_data or len(items_data) == 0:
        return 0
    
    # Convert to list of dicts if it's a DataFrame
    if isinstance(items_data, pd.DataFrame):
        items_list = items_data.to_dict('records')
    else:
        items_list = items_data
    
    # Insert in batches of 50
    batch_size = 50
    success_count = 0
    
    for i in range(0, len(items_list), batch_size):
        batch = items_list[i:i+batch_size]
        result = execute_post("order_items", batch)
        if result:
            success_count += len(result)
    
    return success_count

def get_expenses_by_store(store_id, start_date=None, end_date=None):
    """Get expenses for a store with optional date range"""
    query = f"expenses?store_id=eq.{store_id}"
    
    if start_date and end_date:
        start_str = start_date.strftime("%Y-%m-%d") if isinstance(start_date, datetime) else start_date
        end_str = end_date.strftime("%Y-%m-%d") if isinstance(end_date, datetime) else end_date
        query += f"&date=gte.{start_str}&date=lte.{end_str}"
    
    # Add order by date descending
    query += "&order=date.desc"
    
    results = execute_query(query)
    if results:
        return pd.DataFrame(results)
    return pd.DataFrame()

def add_expense(store_id, date, amount, category, description):
    """Add a new expense"""
    expense_data = {
        "store_id": store_id,
        "date": date.strftime("%Y-%m-%d") if isinstance(date, datetime) else date,
        "amount": float(amount),
        "category": category,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    result = execute_post("expenses", expense_data)
    return result is not None

def update_expense(expense_id, data):
    """Update an expense"""
    # Make sure data includes updated_at
    data["updated_at"] = datetime.now().isoformat()
    
    result = execute_update("expenses", data, expense_id)
    return result is not None

def delete_expense(expense_id):
    """Delete an expense"""
    return execute_delete("expenses", expense_id)

def add_sync_log(status, details=None):
    """Add a sync log entry"""
    log_data = {
        "sync_time": datetime.now().isoformat(),
        "status": status
    }
    
    if details:
        log_data["details"] = json.dumps(details)
    
    result = execute_post("sync_log", log_data)
    return result is not None

def get_last_sync():
    """Get the last sync log entry"""
    results = execute_query("sync_log?order=sync_time.desc&limit=1")
    if results and len(results) > 0:
        return results[0]
    return None 