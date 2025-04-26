import streamlit as st
import requests
import json
import datetime
import pandas as pd
import time
import uuid
import sys
import os

st.set_page_config(page_title="Complete End-to-End Test", layout="wide", page_icon="🔄")
st.title("🔄 Complete End-to-End Test")
st.write("This app tests the entire flow: Clover API → Supabase → Display")

# Simple debug info
st.sidebar.markdown("### Version Info")
st.sidebar.write(f"Streamlit: {st.__version__}")

# IMPORTANT: All logic is now inside button clicks, so the app loads immediately
st.header("Step 1: Test Connections")

if st.button("Test Supabase Connection"):
    # Only try to connect when button is clicked
    st.write("Testing Supabase connection...")
    
    try:
        # Get credentials from secrets
        if 'connections' in st.secrets and 'supabase' in st.secrets.connections:
            project_url = st.secrets.connections.supabase.project_url
            api_key = st.secrets.connections.supabase.api_key
            st.success("✅ Found Supabase credentials!")
        else:
            project_url = st.secrets.supabase.url
            api_key = st.secrets.supabase.api_key
            st.success("✅ Found Supabase credentials (direct format)!")
        
        # Test connection with a simple request
        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{project_url}/rest/v1/stores?limit=1", 
                               headers=headers, 
                               timeout=10)
        
        if response.status_code == 200:
            st.success("✅ Supabase connection successful!")
            # Store connection in session state for later steps
            st.session_state.supabase = {
                "project_url": project_url,
                "api_key": api_key,
                "headers": headers
            }
            stores = response.json()
            if stores:
                st.write("Found stores:")
                st.write(stores)
        else:
            st.error(f"❌ Supabase connection failed: {response.status_code}")
            st.write(f"Response: {response.text}")
            
    except Exception as e:
        st.error(f"❌ Supabase connection error: {str(e)}")

if st.button("Test Clover API Connection"):
    st.write("Testing Clover API connection...")
    
    try:
        # Get Clover credentials
        if 'store_1' in st.secrets:
            store = st.secrets.store_1
            name = store.name
            merchant_id = store.merchant_id
            access_token = store.access_token
            st.write(f"Using credentials for store: {name}")
        else:
            st.error("❌ No Clover credentials found!")
            st.stop()
        
        # Test Clover connection
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"https://api.clover.com/v3/merchants/{merchant_id}", 
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            st.success("✅ Clover API connection successful!")
            merchant_data = response.json()
            st.write(f"Connected to merchant: {merchant_data.get('name')}")
            
            # Store connection in session state for later steps
            st.session_state.clover = {
                "merchant_id": merchant_id,
                "access_token": access_token,
                "headers": headers
            }
        else:
            st.error(f"❌ Clover API connection failed: {response.status_code}")
            st.write(f"Response: {response.text}")
            
    except Exception as e:
        st.error(f"❌ Clover API connection error: {str(e)}")

# Step 2: Fetch data
st.header("Step 2: Fetch Data from Clover")

if st.button("Fetch Payments"):
    if 'clover' not in st.session_state:
        st.error("⚠️ Please test Clover connection first!")
        st.stop()
    
    st.write("Fetching recent payments from Clover...")
    
    try:
        merchant_id = st.session_state.clover["merchant_id"]
        headers = st.session_state.clover["headers"]
        
        # Fetch some recent payments (no date filter)
        url = f"https://api.clover.com/v3/merchants/{merchant_id}/payments"
        params = {
            'limit': 5,
            'expand': 'order'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            payments = data.get('elements', [])
            
            if payments:
                st.success(f"✅ Successfully fetched {len(payments)} payments!")
                st.session_state.payments = payments
                
                # Show sample payment
                st.subheader("Sample Payment")
                st.json(payments[0])
            else:
                st.warning("No payments found!")
        else:
            st.error(f"❌ Failed to fetch payments: {response.status_code}")
            st.write(f"Response: {response.text}")
    
    except Exception as e:
        st.error(f"❌ Error fetching payments: {str(e)}")

# Step 3: Save to Supabase
st.header("Step 3: Save to Supabase")

if st.button("Process and Save Payment"):
    # Verify prerequisites
    if 'payments' not in st.session_state:
        st.error("⚠️ Please fetch payments first!")
        st.stop()
        
    if 'supabase' not in st.session_state:
        st.error("⚠️ Please test Supabase connection first!")
        st.stop()
    
    st.write("Processing payment data...")
    
    try:
        # Get a payment to process
        payment = st.session_state.payments[0]
        
        # Get Supabase connection details
        supabase = st.session_state.supabase
        project_url = supabase["project_url"]
        
        # Get service role key if available
        if 'connections' in st.secrets and 'supabase_admin' in st.secrets.connections:
            service_key = st.secrets.connections.supabase_admin.api_key
        elif 'supabase' in st.secrets and hasattr(st.secrets.supabase, 'service_role_key'):
            service_key = st.secrets.supabase.service_role_key
        else:
            service_key = supabase["api_key"]  # Fallback to anon key
        
        # Admin headers for write operations
        admin_headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # First, get the store ID from merchant_id
        merchant_id = st.session_state.clover["merchant_id"]
        store_url = f"{project_url}/rest/v1/stores?merchant_id=eq.{merchant_id}"
        
        # Get the store
        store_response = requests.get(store_url, headers=supabase["headers"], timeout=10)
        
        if store_response.status_code != 200:
            st.error(f"❌ Could not find store with merchant_id {merchant_id}")
            st.stop()
            
        stores = store_response.json()
        if not stores:
            st.error(f"❌ No store found with merchant_id {merchant_id}")
            st.stop()
            
        store_id = stores[0].get('id')
        st.write(f"Found store with ID: {store_id}")
        
        # Process payment data
        payment_id = payment.get('id')
        order_id = payment.get('order', {}).get('id')
        amount = payment.get('amount')
        created_time = payment.get('createdTime')
        employee_id = payment.get('employee', {}).get('id', '')
        device_id = payment.get('device', {}).get('id', '')
        tender_type = payment.get('tender', {}).get('label', 'cash')
        card_type = payment.get('cardTransaction', {}).get('cardType', '')
        last_4 = payment.get('cardTransaction', {}).get('last4', '')
        
        # Convert timestamp to datetime
        created_at = datetime.datetime.fromtimestamp(created_time / 1000)
        
        # Format payment for Supabase
        payment_data = {
            'payment_id': payment_id,
            'store_id': store_id,
            'amount': amount,
            'created_time': created_at.isoformat(),
            'employee_id': employee_id,
            'order_id': order_id,
            'device_id': device_id,
            'tender_type': tender_type,
            'card_type': card_type,
            'last_4': last_4,
            'sync_date': datetime.datetime.now().isoformat()
        }
        
        # Check if payment already exists
        check_url = f"{project_url}/rest/v1/payments?payment_id=eq.{payment_id}"
        check_response = requests.get(check_url, headers=supabase["headers"], timeout=10)
        
        if check_response.status_code == 200 and check_response.json():
            st.warning(f"Payment {payment_id} already exists. Using existing record.")
            st.session_state.saved_payment = check_response.json()[0]
            st.success("✅ Payment record ready for testing!")
        else:
            # Insert payment
            insert_url = f"{project_url}/rest/v1/payments"
            insert_response = requests.post(insert_url, headers=admin_headers, json=[payment_data], timeout=15)
            
            if insert_response.status_code == 201 or insert_response.status_code == 200:
                st.success("✅ Payment saved to Supabase!")
                st.session_state.saved_payment = payment_data
            else:
                st.error(f"❌ Failed to save payment: {insert_response.status_code}")
                st.write(f"Response: {insert_response.text}")
                
                # Check if it's a duplicate key issue
                if insert_response.status_code == 409 and "duplicate key" in insert_response.text:
                    st.warning("This appears to be a duplicate key error - the payment might already exist.")
                    # Try to get the existing record
                    existing = requests.get(check_url, headers=supabase["headers"], timeout=10)
                    if existing.status_code == 200 and existing.json():
                        st.session_state.saved_payment = existing.json()[0]
                        st.success("✅ Using existing payment record!")
    
    except Exception as e:
        st.error(f"❌ Error processing payment: {str(e)}")

# Step 4: Verify data in Supabase
st.header("Step 4: Verify Data in Supabase")

if st.button("Retrieve Payment"):
    if 'saved_payment' not in st.session_state:
        st.error("⚠️ Please save a payment first!")
        st.stop()
        
    if 'supabase' not in st.session_state:
        st.error("⚠️ Please test Supabase connection first!")
        st.stop()
    
    st.write("Retrieving payment from Supabase...")
    
    try:
        # Get the payment ID
        payment_id = st.session_state.saved_payment['payment_id']
        
        # Set up the query
        supabase = st.session_state.supabase
        url = f"{supabase['project_url']}/rest/v1/payments?payment_id=eq.{payment_id}"
        
        # Fetch the payment
        response = requests.get(url, headers=supabase["headers"], timeout=10)
        
        if response.status_code == 200:
            payments = response.json()
            if payments:
                st.success("✅ Payment successfully retrieved from Supabase!")
                
                # Compare the records
                st.subheader("Data Verification")
                
                # Create two columns
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("Original Data:")
                    st.json(st.session_state.saved_payment)
                    
                with col2:
                    st.write("Retrieved Data:")
                    st.json(payments[0])
                
                # Confirmation of success
                st.success("🎉 END-TO-END TEST SUCCESSFUL!")
                st.balloons()
                
            else:
                st.error(f"❌ No payment found with ID: {payment_id}")
        else:
            st.error(f"❌ Failed to retrieve payment: {response.status_code}")
            st.write(f"Response: {response.text}")
    
    except Exception as e:
        st.error(f"❌ Error retrieving payment: {str(e)}")

# Add a summary of what's been completed
st.header("Test Progress")

# Track which steps have been completed
steps = {
    "Supabase Connection": "supabase" in st.session_state,
    "Clover API Connection": "clover" in st.session_state,
    "Data Fetched": "payments" in st.session_state,
    "Data Saved": "saved_payment" in st.session_state
}

# Create a simple status table
status_df = pd.DataFrame({
    "Step": steps.keys(),
    "Status": ["✅ Complete" if status else "❌ Incomplete" for status in steps.values()]
})

st.table(status_df) 