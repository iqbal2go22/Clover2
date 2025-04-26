"""
Cloud Database Utilities for Supabase
This module provides database utilities for interacting with a PostgreSQL database on Supabase.
It's a drop-in replacement for db_utils.py but uses Supabase instead of SQLite.
"""

import pandas as pd
import datetime
import streamlit as st
import os
import time
import json
import requests

def get_supabase_client():
    """Get Supabase connection details from secrets"""
    if not hasattr(st.session_state, "supabase_client"):
        try:
            # Get connection details from secrets
            if hasattr(st, 'secrets') and 'connections' in st.secrets and 'supabase' in st.secrets.connections:
                project_url = st.secrets.connections.supabase.get("project_url")
                api_key = st.secrets.connections.supabase.get("api_key")
            else:
                # Fallback to older format if needed
                project_url = st.secrets.supabase.url if hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase') and hasattr(st.secrets.supabase, 'url') else None
                api_key = st.secrets.supabase.api_key if hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase') and hasattr(st.secrets.supabase, 'api_key') else None
                
                # Second fallback for key names
                if not api_key and hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase') and hasattr(st.secrets.supabase, 'key'):
                    api_key = st.secrets.supabase.key
            
            if not project_url or not api_key:
                st.error("Supabase connection details not found in Streamlit secrets")
                st.write("Please configure the following in your secrets:")
                st.code("""
[connections.supabase]
project_url = "https://your-project-id.supabase.co"
api_key = "your_anon_key"
                """)
                raise Exception("Missing Supabase connection details in secrets")
            
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
            
            # Test connection to make sure it works
            test_url = f"{project_url}/rest/v1/sync_log?limit=1"
            response = requests.get(test_url, headers=headers, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            st.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
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

def get_all_stores():
    """Get all stores from Supabase."""
    try:
        results = execute_query("stores?order=name")
        if results:
            return pd.DataFrame(results)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching stores: {str(e)}")
        return pd.DataFrame()

def get_store_by_merchant_id(merchant_id):
    """Get a store by merchant ID"""
    results = execute_query(f"stores?merchant_id=eq.{merchant_id}")
    if results and len(results) > 0:
        return results[0]
    return None

def update_store_last_sync(merchant_id, sync_date=None):
    """Update the last sync date for a store"""
    if sync_date is None:
        sync_date = datetime.datetime.now().isoformat()
    
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
        start_iso = start_date.isoformat() if isinstance(start_date, datetime.datetime) else start_date
        end_iso = end_date.isoformat() if isinstance(end_date, datetime.datetime) else end_date
        query += f"&created_at=gte.{start_iso}&created_at=lte.{end_iso}"
    
    results = execute_query(query)
    if results:
        return pd.DataFrame(results)
    return pd.DataFrame()

def get_payments_count_by_merchant(merchant_id, start_date=None, end_date=None):
    """Get count of payments for a merchant with optional date range"""
    query = f"payments?merchant_id=eq.{merchant_id}&select=id"
    
    if start_date and end_date:
        start_iso = start_date.isoformat() if isinstance(start_date, datetime.datetime) else start_date
        end_iso = end_date.isoformat() if isinstance(end_date, datetime.datetime) else end_date
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
        start_iso = start_date.isoformat() if isinstance(start_date, datetime.datetime) else start_date
        end_iso = end_date.isoformat() if isinstance(end_date, datetime.datetime) else end_date
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
        start_str = start_date.strftime("%Y-%m-%d") if isinstance(start_date, datetime.datetime) else start_date
        end_str = end_date.strftime("%Y-%m-%d") if isinstance(end_date, datetime.datetime) else end_date
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
        "date": date.strftime("%Y-%m-%d") if isinstance(date, datetime.datetime) else date,
        "amount": float(amount),
        "category": category,
        "description": description,
        "created_at": datetime.datetime.now().isoformat(),
        "updated_at": datetime.datetime.now().isoformat()
    }
    
    result = execute_post("expenses", expense_data)
    return result is not None

def update_expense(expense_id, data):
    """Update an expense"""
    # Make sure data includes updated_at
    data["updated_at"] = datetime.datetime.now().isoformat()
    
    result = execute_update("expenses", data, expense_id)
    return result is not None

def delete_expense(expense_id):
    """Delete an expense"""
    return execute_delete("expenses", expense_id)

def add_sync_log(status, details=None):
    """Add a sync log entry"""
    log_data = {
        "sync_time": datetime.datetime.now().isoformat(),
        "status": status
    }
    
    if details:
        log_data["details"] = details if isinstance(details, str) else json.dumps(details)
    
    result = execute_post("sync_log", log_data)
    return result is not None

def get_last_sync():
    """Get the last sync log entry"""
    results = execute_query("sync_log?order=sync_time.desc&limit=1")
    if results and len(results) > 0:
        return results[0]
    return None

def get_expense_categories():
    """Get all expense categories."""
    return ["Rent", "Utilities", "Salaries", "Inventory", "Marketing", "Insurance", "Taxes", "Maintenance", "Supplies", "Other"]

# Clover API Integration Functions
def fetch_clover_data(merchant_id, access_token, start_date, end_date):
    """
    Fetch payment data from Clover API for a specific merchant and date range.
    
    Args:
        merchant_id: The Clover merchant ID
        access_token: The Clover access token
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        
    Returns:
        Dictionary containing payments and order data
    """
    # Format dates for Clover API
    start_str = start_date.strftime("%Y-%m-%dT00:00:00.000Z")
    end_str = end_date.strftime("%Y-%m-%dT23:59:59.999Z")
    
    # Base URL for Clover API
    base_url = "https://api.clover.com/v3"
    
    # Headers for authorization
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Fetch payments
    payments_url = f"{base_url}/merchants/{merchant_id}/payments"
    params = {
        'filter': f'createdTime>={start_str} and createdTime<={end_str}',
        'expand': 'order',
        'limit': 1000  # Maximum allowed by Clover API
    }
    
    all_payments = []
    has_more = True
    offset = 0
    
    # Paginate through all results
    while has_more:
        params['offset'] = offset
        try:
            response = requests.get(payments_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'elements' in data:
                payments = data['elements']
                all_payments.extend(payments)
                
                # Check if there are more pages
                if len(payments) < 1000:
                    has_more = False
                else:
                    offset += 1000
            else:
                has_more = False
        except Exception as e:
            st.error(f"Error fetching payments from Clover API: {str(e)}")
            break
    
    # Get order items for all orders
    order_items = []
    order_ids = set()
    
    # Extract unique order IDs from payments
    for payment in all_payments:
        if 'order' in payment and payment['order'] and 'id' in payment['order']:
            order_ids.add(payment['order']['id'])
    
    # Fetch line items for each order
    for order_id in order_ids:
        try:
            items_url = f"{base_url}/merchants/{merchant_id}/orders/{order_id}/line_items"
            response = requests.get(items_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if 'elements' in data:
                for item in data['elements']:
                    item['orderId'] = order_id
                    order_items.append(item)
        except Exception as e:
            st.error(f"Error fetching order items for order {order_id}: {str(e)}")
    
    return {
        'payments': all_payments,
        'order_items': order_items
    }

def process_and_save_clover_data(store_id, clover_data):
    """
    Process and save Clover data to Supabase.
    
    Args:
        store_id: Merchant ID for the store
        clover_data: Dictionary containing payments and order_items from Clover API
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Process payments
        payments_processed = []
        for payment in clover_data['payments']:
            # Extract payment data
            payment_id = payment.get('id')
            order_id = payment.get('order', {}).get('id')
            amount = payment.get('amount')
            created_time = payment.get('createdTime')
            
            if payment_id and amount is not None and created_time:
                # Convert timestamp to datetime
                created_at = datetime.datetime.fromtimestamp(created_time / 1000)
                
                # Format for Supabase
                payment_data = {
                    'id': payment_id,
                    'merchant_id': store_id,
                    'order_id': order_id,
                    'amount': amount,
                    'created_at': created_at.isoformat()
                }
                payments_processed.append(payment_data)
        
        # Process order items
        items_processed = []
        for item in clover_data['order_items']:
            item_id = item.get('id')
            order_id = item.get('orderId')
            name = item.get('name')
            price = item.get('price')
            quantity = item.get('quantity', 1)
            
            if item_id and order_id:
                # Format for Supabase
                item_data = {
                    'id': item_id,
                    'merchant_id': store_id,
                    'order_id': order_id,
                    'name': name,
                    'price': price / 100 if price else 0,  # Convert cents to dollars
                    'quantity': quantity,
                    'created_at': datetime.datetime.now().isoformat()  # Use current time as fallback
                }
                items_processed.append(item_data)
        
        # Save to Supabase
        payments_saved = 0
        if payments_processed:
            payments_saved = save_payments(payments_processed)
        
        items_saved = 0
        if items_processed:
            items_saved = save_order_items(items_processed)
        
        # Update sync log
        add_sync_log("completed", f"Synced {payments_saved} payments and {items_saved} order items")
        
        return True
    
    except Exception as e:
        st.error(f"Error processing and saving Clover data: {str(e)}")
        # Log the error
        add_sync_log("failed", str(e))
        return False

def sync_clover_data(store_id=None, start_date=None, end_date=None):
    """
    Main function to sync data from Clover API to Supabase.
    
    Args:
        store_id: Specific store ID to sync, or None for all stores
        start_date: Start date for data sync
        end_date: End date for data sync
        
    Returns:
        Dict with success status and message
    """
    if start_date is None:
        # Default to 30 days ago
        start_date = datetime.datetime.now() - datetime.timedelta(days=30)
    
    if end_date is None:
        end_date = datetime.datetime.now()
    
    # Get stores to sync
    try:
        # Track overall sync results
        results = {
            "total_stores": 0,
            "successful_stores": 0,
            "failed_stores": 0,
            "total_payments": 0,
            "total_order_items": 0
        }
        
        # Get stores to sync - either specific store or all stores
        stores = []
        if store_id:
            # Get specific store
            store = get_store_by_merchant_id(store_id)
            if store:
                stores = [store]
            else:
                # Store not found in database, check if we have it in secrets
                if hasattr(st, 'secrets'):
                    for key in st.secrets:
                        # Look for any key that might be a store config
                        if key.startswith('store_') or 'store' in key:
                            store_config = st.secrets[key]
                            if isinstance(store_config, dict) and 'merchant_id' in store_config:
                                if store_config['merchant_id'] == store_id:
                                    stores = [{
                                        'merchant_id': store_config['merchant_id'],
                                        'name': store_config.get('name', f"Store {store_id}"),
                                        'access_token': store_config.get('access_token')
                                    }]
                                    break
                
                if not stores:
                    return {"success": False, "message": f"Store with ID {store_id} not found"}
        else:
            # Get all stores from database
            stores_df = get_all_stores()
            if not stores_df.empty:
                stores = stores_df.to_dict('records')
            
            # Also check secrets for any additional stores
            if hasattr(st, 'secrets'):
                merchant_ids = set(store['merchant_id'] for store in stores) if stores else set()
                
                for key in st.secrets:
                    if key.startswith('store_') or 'store' in key:
                        store_config = st.secrets[key]
                        if isinstance(store_config, dict) and 'merchant_id' in store_config:
                            # Only add if not already in the list
                            if store_config['merchant_id'] not in merchant_ids:
                                stores.append({
                                    'merchant_id': store_config['merchant_id'],
                                    'name': store_config.get('name', f"Store {len(stores)+1}"),
                                    'access_token': store_config.get('access_token')
                                })
                                merchant_ids.add(store_config['merchant_id'])
            
            if not stores:
                return {"success": False, "message": "No stores found in database or secrets"}
        
        results["total_stores"] = len(stores)
        
        # Sync each store
        for store in stores:
            merchant_id = store['merchant_id']
            access_token = store.get('access_token')
            
            # If access token not in store record, check secrets
            if not access_token:
                # First check for direct store reference
                store_key = f"store_{merchant_id}"
                if hasattr(st, 'secrets') and store_key in st.secrets:
                    access_token = st.secrets[store_key].get('access_token')
                else:
                    # Check all store configs
                    for key in st.secrets:
                        if key.startswith('store_') or 'store' in key:
                            store_config = st.secrets[key]
                            if isinstance(store_config, dict) and store_config.get('merchant_id') == merchant_id:
                                access_token = store_config.get('access_token')
                                break
                
                # Numbered store format (store_1, store_2, etc)
                if not access_token:
                    for i in range(1, 20):  # Check up to 20 stores
                        store_key = f'store_{i}'
                        if hasattr(st, 'secrets') and store_key in st.secrets:
                            if st.secrets[store_key].get('merchant_id') == merchant_id:
                                access_token = st.secrets[store_key].get('access_token')
                                break
            
            if not access_token:
                st.warning(f"No access token found for store {store.get('name', merchant_id)}")
                results["failed_stores"] += 1
                continue
            
            # Fetch data from Clover API
            try:
                clover_data = fetch_clover_data(merchant_id, access_token, start_date, end_date)
                
                # Process and save data
                if clover_data['payments'] or clover_data['order_items']:
                    success = process_and_save_clover_data(merchant_id, clover_data)
                    
                    if success:
                        results["successful_stores"] += 1
                        results["total_payments"] += len(clover_data['payments'])
                        results["total_order_items"] += len(clover_data['order_items'])
                        
                        # Update store's last sync date
                        update_store_last_sync(merchant_id)
                    else:
                        results["failed_stores"] += 1
                else:
                    # No data found but not an error
                    st.info(f"No new data found for store {store.get('name', merchant_id)}")
                    results["successful_stores"] += 1
            except Exception as e:
                st.error(f"Error syncing store {store.get('name', merchant_id)}: {str(e)}")
                results["failed_stores"] += 1
        
        # Overall success if at least one store synced successfully
        success = results["successful_stores"] > 0
        
        # Create summary message
        message = f"Synced {results['total_payments']} payments from {results['successful_stores']} stores"
        if results["failed_stores"] > 0:
            message += f" ({results['failed_stores']} stores failed)"
        
        return {
            "success": success,
            "message": message,
            "results": results
        }
        
    except Exception as e:
        error_message = f"Error syncing Clover data: {str(e)}"
        add_sync_log("failed", error_message)
        return {"success": False, "message": error_message} 