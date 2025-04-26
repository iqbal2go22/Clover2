import streamlit as st
import requests
import json
import datetime
import pandas as pd
import time
import uuid

st.set_page_config(page_title="Complete End-to-End Test", layout="wide")
st.title("🔄 Complete End-to-End Test")
st.write("This app tests the entire flow: Clover API → Supabase → Display")

# Step 1: Set up connections
st.header("1. Setting Up Connections")

# Supabase credentials
supabase_project_url = "https://yegrbbtxlsfbrlyavmbg.supabase.co"
supabase_anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ3JiYnR4bHNmYnJseWF2bWJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUzNDEzMTksImV4cCI6MjA2MDkxNzMxOX0.WsdfCwJd9dJ305uzmYcENHpspi_SFKVf71UKuZKCGaY"
supabase_service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ3JiYnR4bHNmYnJseWF2bWJnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTM0MTMxOSwiZXhwIjoyMDYwOTE3MzE5fQ.2A5WSRFBG-9ufAutAUm1fwZ44w-NGxuTRCg-n3y5tUo"

# Clover credentials for Laurel store
laurel_merchant_id = "4VZSM7038BKQ1"
laurel_access_token = "b9f678d7-9b27-e971-d9e4-feab8b227c96"

# Create status columns
col1, col2 = st.columns(2)

# Check Supabase connection
with col1:
    st.subheader("Supabase Connection")
    supabase_headers = {
        "apikey": supabase_anon_key,
        "Authorization": f"Bearer {supabase_anon_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{supabase_project_url}/rest/v1/stores?limit=1", headers=supabase_headers)
        response.raise_for_status()
        st.success("✅ Connected to Supabase successfully!")
        supabase_connected = True
    except Exception as e:
        st.error(f"❌ Supabase connection failed: {str(e)}")
        supabase_connected = False

# Check Clover connection
with col2:
    st.subheader("Clover API Connection")
    clover_headers = {
        'Authorization': f'Bearer {laurel_access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"https://api.clover.com/v3/merchants/{laurel_merchant_id}", headers=clover_headers)
        response.raise_for_status()
        merchant_data = response.json()
        st.success(f"✅ Connected to Clover API for: {merchant_data.get('name')}")
        clover_connected = True
    except Exception as e:
        st.error(f"❌ Clover API connection failed: {str(e)}")
        clover_connected = False

if not (supabase_connected and clover_connected):
    st.error("Cannot proceed with test due to connection issues")
    st.stop()

# Step 2: Fetch data from Clover API
st.header("2. Fetching Data from Clover API")

@st.cache_data(ttl=300)
def fetch_clover_data(merchant_id, access_token, days=2):
    """Fetch payment data from Clover API"""
    # Calculate date range (last X days)
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days)
    
    # Format dates for Clover API - use millisecond timestamps instead of ISO strings
    start_ms = int(start_date.timestamp() * 1000)
    end_ms = int(end_date.timestamp() * 1000)
    
    # Set up API request
    base_url = "https://api.clover.com/v3"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Fetch payments with order information
    payments_url = f"{base_url}/merchants/{merchant_id}/payments"
    
    # Just use the fallback method since it works reliably
    params = {
        'limit': 10,
        'expand': 'order'
    }
    
    st.write(f"Fetching recent payments without date filter")
    
    try:
        # Get payments
        response = requests.get(payments_url, headers=headers, params=params)
        
        # Show response status for debugging
        st.write(f"Response status: {response.status_code}")
        
        response.raise_for_status()
        data = response.json()
        
        # If we need to filter by date, we can do it client-side
        elements = data.get('elements', [])
        st.write(f"Successfully fetched {len(elements)} payments")
        
        return elements
    except Exception as e:
        st.error(f"Error fetching from Clover API: {str(e)}")
        return []

# Fetch data button
if st.button("Fetch Data from Clover"):
    with st.spinner("Fetching data from Clover API..."):
        payments = fetch_clover_data(laurel_merchant_id, laurel_access_token)
        
        if payments:
            st.success(f"✅ Successfully fetched {len(payments)} payments from Clover API")
            
            # Show sample payment
            st.subheader("Sample Payment Data")
            st.json(payments[0])
            
            # Store in session state for next steps
            st.session_state.payments = payments
        else:
            st.warning("No payment data found in the selected date range.")
            st.session_state.payments = []

# Step 3: Process and save to Supabase
st.header("3. Saving Data to Supabase")

@st.cache_data(ttl=300)
def get_store_id(merchant_id):
    """Get the numeric store_id for a merchant_id from the stores table"""
    try:
        supabase_headers = {
            "apikey": supabase_anon_key,
            "Authorization": f"Bearer {supabase_anon_key}",
            "Content-Type": "application/json"
        }
        
        # Query the stores table to get the numeric ID
        url = f"{supabase_project_url}/rest/v1/stores?merchant_id=eq.{merchant_id}"
        response = requests.get(url, headers=supabase_headers)
        response.raise_for_status()
        
        stores = response.json()
        if stores and len(stores) > 0:
            # Return the numeric ID
            return stores[0].get('id')
        else:
            st.error(f"Store with merchant_id {merchant_id} not found in the database")
            return None
            
    except Exception as e:
        st.error(f"Error getting store ID: {str(e)}")
        return None

def process_payments(merchant_id, payments):
    """Process payment data for storage"""
    # First get the numeric store_id
    store_id = get_store_id(merchant_id)
    
    if not store_id:
        st.error("Cannot process payments without a valid store_id")
        return []
        
    st.success(f"Found store_id: {store_id} for merchant_id: {merchant_id}")
    
    payments_processed = []
    
    for payment in payments:
        # Extract payment data
        payment_id = payment.get('id')
        order_id = payment.get('order', {}).get('id')
        amount = payment.get('amount')
        created_time = payment.get('createdTime')
        employee_id = payment.get('employee', {}).get('id', '')
        device_id = payment.get('device', {}).get('id', '')
        tender_type = payment.get('tender', {}).get('label', 'cash')
        card_type = payment.get('cardTransaction', {}).get('cardType', '')
        last_4 = payment.get('cardTransaction', {}).get('last4', '')
        
        if payment_id and amount is not None and created_time:
            # Convert timestamp to datetime
            created_at = datetime.datetime.fromtimestamp(created_time / 1000)
            
            # Format for Supabase - use the correct schema
            payment_data = {
                'payment_id': payment_id,
                'store_id': store_id,  # Use numeric store_id
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
            payments_processed.append(payment_data)
    
    return payments_processed

def save_to_supabase(data, table="payments"):
    """Save test data to Supabase"""
    supabase_headers = {
        "apikey": supabase_service_key,  # Use service key for write operations
        "Authorization": f"Bearer {supabase_service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # Use the existing payments table
    url = f"{supabase_project_url}/rest/v1/{table}"
    
    # No need to create test table since we're using the existing payments table
    
    # Insert data
    st.write(f"Saving to table: {table}")
    response = requests.post(url, headers=supabase_headers, json=data)
    
    # Log any error details
    if response.status_code != 200:
        st.error(f"Error response: {response.text}")
        
    response.raise_for_status()
    
    return response.json()

# Process and save button - only show if we have payments
if 'payments' in st.session_state and st.session_state.payments:
    if st.button("Process and Save to Supabase"):
        with st.spinner("Processing and saving payments..."):
            # Process payments
            processed_payments = process_payments(laurel_merchant_id, st.session_state.payments)
            
            if processed_payments:
                st.write(f"Processed {len(processed_payments)} payments")
                
                # Show one processed payment
                st.subheader("Sample Processed Payment")
                st.write(processed_payments[0])
                
                # Try to save to Supabase
                try:
                    # Save one payment for testing
                    result = save_to_supabase([processed_payments[0]])
                    
                    if result:
                        st.success("✅ Successfully saved payment to Supabase")
                        st.session_state.saved_payment = processed_payments[0]
                    else:
                        st.error("Failed to save payment to Supabase")
                except Exception as e:
                    st.error(f"Error saving to Supabase: {str(e)}")
            else:
                st.warning("No payments to process")

# Step 4: Retrieve from Supabase and verify
st.header("4. Retrieving Data from Supabase")

def get_from_supabase(payment_id, table="payments"):
    """Retrieve test payment from Supabase"""
    supabase_headers = {
        "apikey": supabase_anon_key,
        "Authorization": f"Bearer {supabase_anon_key}",
        "Content-Type": "application/json"
    }
    
    # Use payment_id, not id
    url = f"{supabase_project_url}/rest/v1/{table}?payment_id=eq.{payment_id}"
    response = requests.get(url, headers=supabase_headers)
    response.raise_for_status()
    
    return response.json()

# Retrieve button - only show if we have a saved payment
if 'saved_payment' in st.session_state:
    if st.button("Retrieve from Supabase"):
        with st.spinner("Retrieving payment from Supabase..."):
            payment_id = st.session_state.saved_payment['payment_id']
            
            try:
                retrieved_data = get_from_supabase(payment_id)
                
                if retrieved_data and len(retrieved_data) > 0:
                    st.success("✅ Successfully retrieved payment from Supabase")
                    
                    # Display comparison
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Original Data Sent")
                        st.write(st.session_state.saved_payment)
                    
                    with col2:
                        st.subheader("Data Retrieved from Supabase")
                        st.write(retrieved_data[0])
                    
                    # Final success message
                    st.success("🎉 FULL END-TO-END TEST SUCCESSFUL!")
                    st.balloons()
                else:
                    st.error("No data found in Supabase")
            except Exception as e:
                st.error(f"Error retrieving from Supabase: {str(e)}")

# Summary section
st.header("Test Summary")

# Check which steps have been completed
test_steps = {
    "Supabase Connection": supabase_connected,
    "Clover API Connection": clover_connected,
    "Data Fetched from Clover": 'payments' in st.session_state and len(st.session_state.payments) > 0,
    "Data Saved to Supabase": 'saved_payment' in st.session_state,
    "Data Retrieved from Supabase": 'saved_payment' in st.session_state and st.button("Retrieve from Supabase")
}

# Create a DataFrame for the results
results_df = pd.DataFrame({
    "Test Step": test_steps.keys(),
    "Status": ["✅ COMPLETE" if status else "❌ INCOMPLETE" for status in test_steps.values()]
})

st.table(results_df)

# Next steps guidance
st.subheader("Next Steps")
st.write("""
1. If all tests passed, your application is correctly configured and should work properly.
2. If any test failed, check the error messages for troubleshooting.
3. Deploy your main application to Streamlit Cloud.
""")

# Footer with more information
st.markdown("---")
st.write("This test confirms that the complete data flow works: Clover API → Supabase → Application display")
if not 'payments' in st.session_state:
    st.info("👆 Start by clicking 'Fetch Data from Clover' to begin the test") 