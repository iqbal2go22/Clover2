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

def get_all_stores():
    """Get all stores from the database."""
    conn = get_db_connection()
    try:
        # Query all stores
        df = pd.read_sql(text("SELECT * FROM stores ORDER BY name"), conn)
        return df
    finally:
        conn.close()

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