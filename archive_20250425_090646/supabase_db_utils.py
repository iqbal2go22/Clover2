import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import json

def get_connection():
    """Get the Supabase connection."""
    return st.connection("supabase")

def get_all_stores():
    """Get all stores from Supabase."""
    conn = get_connection()
    try:
        df = conn.query("stores", columns="*")
        return df
    except Exception as e:
        st.error(f"Error fetching stores: {str(e)}")
        return pd.DataFrame()

def get_store_by_id(store_id):
    """Get store information by ID."""
    conn = get_connection()
    try:
        filters = {"merchant_id": f"eq.{store_id}"}
        df = conn.query("stores", columns="*", filters=filters)
        if not df.empty:
            return df.iloc[0].to_dict()
        return None
    except Exception as e:
        st.error(f"Error fetching store {store_id}: {str(e)}")
        return None

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