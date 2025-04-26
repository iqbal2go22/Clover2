import streamlit as st
import requests
import json
import datetime
import pandas as pd
import time

st.set_page_config(page_title="Full Integration Test", layout="wide")
st.title("🧪 Clover to Supabase Integration Test")

# Step 1: Test Supabase Connection
st.header("1. Supabase Connection Test")

def get_supabase_client():
    """Get Supabase connection details from secrets"""
    try:
        # Get connection details from secrets
        if hasattr(st, 'secrets') and 'connections' in st.secrets and 'supabase' in st.secrets.connections:
            project_url = st.secrets.connections.supabase.get("project_url")
            api_key = st.secrets.connections.supabase.get("api_key")
            st.write("✅ Using connections.supabase format")
        else:
            # Fallback to older format
            project_url = st.secrets.supabase.url if hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase') and hasattr(st.secrets.supabase, 'url') else None
            api_key = st.secrets.supabase.api_key if hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase') and hasattr(st.secrets.supabase, 'api_key') else None
            
            # Second fallback for key names
            if not api_key and hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase') and hasattr(st.secrets.supabase, 'key'):
                api_key = st.secrets.supabase.key
                
            st.write("✅ Using direct supabase format")
        
        if not project_url or not api_key:
            st.error("Supabase connection details not found in Streamlit secrets")
            return None
        
        # Set up headers for Supabase REST API
        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        client = {
            "project_url": project_url,
            "headers": headers
        }
        
        # Test connection
        test_url = f"{project_url}/rest/v1/stores?limit=1"
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        st.success(f"✅ Supabase connection successful!")
        return client
        
    except Exception as e:
        st.error(f"❌ Supabase connection failed: {str(e)}")
        return None

supabase_client = get_supabase_client()

if not supabase_client:
    st.stop()

# Step 2: Get Store Configuration and test Clover API
st.header("2. Clover API Connection Test")

def get_store_configs():
    """Get store configurations from Streamlit secrets"""
    stores = []
    
    if hasattr(st, 'secrets'):
        for key in st.secrets:
            if key.startswith('store_'):
                store_config = st.secrets[key]
                if isinstance(store_config, dict) and 'merchant_id' in store_config and 'access_token' in store_config:
                    stores.append({
                        'name': store_config.get('name', f"Store {len(stores)+1}"),
                        'merchant_id': store_config['merchant_id'],
                        'access_token': store_config['access_token']
                    })
    
    return stores

stores = get_store_configs()

if not stores:
    st.error("❌ No store configurations found in secrets")
    st.stop()

st.write(f"Found {len(stores)} stores in configuration")

# Test Clover API for one store
selected_store = stores[0]
st.write(f"Testing with store: {selected_store['name']}")

def test_clover_connection(merchant_id, access_token):
    """Test connection to Clover API"""
    try:
        # Base URL for Clover API
        base_url = "https://api.clover.com/v3"
        
        # Headers for authorization
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Test with a simple query
        test_url = f"{base_url}/merchants/{merchant_id}"
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        merchant_data = response.json()
        st.success(f"✅ Connected to Clover API for merchant: {merchant_data.get('name', merchant_id)}")
        return True
    except Exception as e:
        st.error(f"❌ Clover API connection failed: {str(e)}")
        return False

clover_connected = test_clover_connection(
    selected_store['merchant_id'], 
    selected_store['access_token']
)

if not clover_connected:
    st.stop()

# Step 3: Fetch data from Clover
st.header("3. Fetch Sample Data from Clover")

def fetch_clover_sample(merchant_id, access_token):
    """Fetch a small sample of data from Clover API"""
    try:
        # Get data for the last 2 days
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=2)
        
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
        
        # Fetch payments (limit to just 5 for testing)
        payments_url = f"{base_url}/merchants/{merchant_id}/payments"
        params = {
            'filter': f'createdTime>={start_str} and createdTime<={end_str}',
            'expand': 'order',
            'limit': 5
        }
        
        response = requests.get(payments_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'elements' in data and len(data['elements']) > 0:
            payments = data['elements']
            st.success(f"✅ Successfully fetched {len(payments)} payments from Clover API")
            
            # Display sample payment data
            sample_payment = payments[0]
            st.write("Sample payment data:")
            st.json(sample_payment)
            
            return payments
        else:
            st.warning("No payment data found in the selected date range. This is not an error, but we need data to proceed.")
            # Try with a larger date range
            st.write("Trying with a larger date range...")
            
            # Get data for the last 30 days
            start_date = end_date - datetime.timedelta(days=30)
            start_str = start_date.strftime("%Y-%m-%dT00:00:00.000Z")
            
            params = {
                'filter': f'createdTime>={start_str} and createdTime<={end_str}',
                'expand': 'order',
                'limit': 5
            }
            
            response = requests.get(payments_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'elements' in data and len(data['elements']) > 0:
                payments = data['elements']
                st.success(f"✅ Successfully fetched {len(payments)} payments from Clover API with extended date range")
                
                # Display sample payment data
                sample_payment = payments[0]
                st.write("Sample payment data:")
                st.json(sample_payment)
                
                return payments
            else:
                st.error("No payment data found even with extended date range. Cannot proceed with test.")
                return []
        
    except Exception as e:
        st.error(f"❌ Error fetching data from Clover API: {str(e)}")
        return []

payments = fetch_clover_sample(
    selected_store['merchant_id'], 
    selected_store['access_token']
)

if not payments:
    st.stop()

# Step 4: Process and save to Supabase
st.header("4. Save Data to Supabase")

def process_payments(merchant_id, payments):
    """Process payment data for storage"""
    payments_processed = []
    
    for payment in payments:
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
                'merchant_id': merchant_id,
                'order_id': order_id,
                'amount': amount,
                'created_at': created_at.isoformat()
            }
            payments_processed.append(payment_data)
    
    return payments_processed

def save_to_supabase(client, table, data):
    """Save data to Supabase"""
    try:
        url = f"{client['project_url']}/rest/v1/{table}"
        response = requests.post(url, headers=client["headers"], json=data)
        response.raise_for_status()
        
        st.success(f"✅ Successfully saved data to Supabase table: {table}")
        return response.json()
    except Exception as e:
        # If error is due to duplicate keys, this is actually expected and OK
        if "duplicate key" in str(e).lower():
            st.warning(f"Data already exists in Supabase (duplicate key). This is OK for testing.")
            return True
        
        st.error(f"❌ Error saving data to Supabase: {str(e)}")
        return None

processed_payments = process_payments(selected_store['merchant_id'], payments)
st.write(f"Processed {len(processed_payments)} payments")

if processed_payments:
    # Save only the first payment for testing
    test_payment = processed_payments[0]
    st.write("Saving test payment to Supabase:")
    st.json(test_payment)
    
    save_result = save_to_supabase(supabase_client, "payments", [test_payment])
    
    if not save_result:
        st.stop()
else:
    st.error("No processed payments to save")
    st.stop()

# Step 5: Retrieve data from Supabase
st.header("5. Retrieve Data from Supabase")

def retrieve_from_supabase(client, query):
    """Retrieve data from Supabase"""
    try:
        url = f"{client['project_url']}/rest/v1/{query}"
        response = requests.get(url, headers=client["headers"])
        response.raise_for_status()
        
        data = response.json()
        st.success(f"✅ Successfully retrieved data from Supabase")
        return data
    except Exception as e:
        st.error(f"❌ Error retrieving data from Supabase: {str(e)}")
        return None

# Try to retrieve the payment we just saved
payment_id = processed_payments[0]['id']
retrieve_query = f"payments?id=eq.{payment_id}"
retrieved_data = retrieve_from_supabase(supabase_client, retrieve_query)

if retrieved_data and len(retrieved_data) > 0:
    st.write("Retrieved payment data from Supabase:")
    st.json(retrieved_data)
    
    st.success("🎉 FULL INTEGRATION TEST SUCCESSFUL! All critical components are working correctly.")
else:
    st.error("Failed to retrieve payment data from Supabase.")

# Provide summary of test results
st.header("Test Summary")

test_results = {
    "Supabase Connection": supabase_client is not None,
    "Clover API Connection": clover_connected,
    "Data Fetching from Clover": len(payments) > 0,
    "Data Processing": len(processed_payments) > 0,
    "Data Saving to Supabase": save_result is not None,
    "Data Retrieval from Supabase": retrieved_data is not None and len(retrieved_data) > 0
}

# Create a simple table for results
results_df = pd.DataFrame({"Test": test_results.keys(), "Result": ["✅ PASS" if result else "❌ FAIL" for result in test_results.values()]})
st.table(results_df)

# Show overall result
all_passed = all(test_results.values())
if all_passed:
    st.success("🎉 ALL TESTS PASSED - Your application should work correctly!")
else:
    st.error("❌ SOME TESTS FAILED - Check the issues above before deploying") 