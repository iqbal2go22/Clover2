import requests
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm
import time
import toml
import os
import db_utils

def convert_ms_to_dt(ms):
    """Convert milliseconds timestamp to datetime string"""
    return datetime.fromtimestamp(ms / 1000).strftime('%Y-%m-%d %H:%M:%S') if ms else None

def date_to_ms(date_obj):
    """Convert datetime object to milliseconds timestamp"""
    return int(date_obj.timestamp() * 1000)

def flatten_payment(p, store_id):
    """Convert payment data to flat dictionary"""
    return {
        'payment_id': p.get('id'),
        'store_id': store_id,
        'amount': p.get('amount'),
        'created_time': convert_ms_to_dt(p.get('createdTime')),
        'employee_id': p.get('employee', {}).get('id'),
        'order_id': p.get('order', {}).get('id'),
        'device_id': p.get('device', {}).get('id'),
        'tender_type': p.get('tender', {}).get('label'),
        'card_type': p.get('cardTransaction', {}).get('cardType'),
        'last_4': p.get('cardTransaction', {}).get('last4'),
    }

def extract_line_items_from_order(order, store_id):
    """Extract line items from order data"""
    line_items = order.get('lineItems', {}).get('elements', [])
    refunds_block = order.get('refunds', {})
    refunds_list = refunds_block.get('elements', []) if isinstance(refunds_block, dict) else []
    refund_ids = {r.get('payment', {}).get('id') for r in refunds_list if r.get('payment')}

    rows = []
    for item in line_items:
        payment_id = item.get('payment', {}).get('id')
        rows.append({
            'store_id': store_id,
            'order_id': order.get('id'),
            'item_id': item.get('id'),
            'name': item.get('name'),
            'price': item.get('price'),
            'quantity': item.get('quantity'),
            'created_time': convert_ms_to_dt(item.get('createdTime')),
            'employee_id': item.get('employee', {}).get('id'),
            'is_refunded': 'Yes' if payment_id in refund_ids else 'No',
            'discount_amount': item.get('discountAmount'),
        })
    return rows

class CloverDataFetcher:
    def __init__(self, merchant_id, access_token, store_name="Store"):
        self.merchant_id = merchant_id
        self.access_token = access_token
        self.store_name = store_name
        self.headers = {'Authorization': f'Bearer {self.access_token}'}
        self.base_payments = f"https://api.clover.com/v3/merchants/{self.merchant_id}/payments"
        self.base_orders = f"https://api.clover.com/v3/merchants/{self.merchant_id}/orders"
        
        # Save store to database and get store_id
        self.store_id = db_utils.save_store(merchant_id, store_name, access_token)
        
    def get_payments_window(self, start_date, end_date):
        """Fetch payments within a date window"""
        payments = []
        limit = 100
        offset = 0
        start_ms = date_to_ms(start_date)
        end_ms = date_to_ms(end_date)

        print(f"📅 Fetching payments for {self.store_name} from {start_date.date()} to {end_date.date()}")

        while True:
            url = f"{self.base_payments}?limit={limit}&offset={offset}&filter=createdTime>{start_ms}&filter=createdTime<{end_ms}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            batch = data.get('elements', [])
            if not batch:
                break
            payments.extend(batch)
            offset += limit
        print(f"✅ Pulled {len(payments)} payments from this window\n")
        return payments
        
    def get_order_details(self, order_id):
        """Fetch details for a specific order"""
        url = f"{self.base_orders}/{order_id}?expand=lineItems,discounts,refunds"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️ Order {order_id} failed: {e}")
            return None
            
    def fetch_store_data(self, start_date, end_date=None, window_size=90):
        """Fetch all data for this store within date range"""
        all_payments = []
        all_order_items = []
        seen_orders = set()
        
        if end_date is None:
            end_date = datetime.today()
            
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
        window_size = timedelta(days=window_size)
        
        print(f"🚀 Starting data extract for {self.store_name}...\n")
        
        current_start = start_date
        while current_start < end_date:
            current_end = min(current_start + window_size, end_date)
            payments = self.get_payments_window(current_start, current_end)
            
            # Process payments
            all_payments.extend([flatten_payment(p, self.store_id) for p in payments])

            # Get unique order IDs from payments
            unique_order_ids = {p.get('order', {}).get('id') for p in payments if p.get('order')}
            new_orders = [oid for oid in unique_order_ids if oid and oid not in seen_orders]

            print(f"🔎 Fetching {len(new_orders)} new order(s) in this window...")

            for oid in tqdm(new_orders, desc=f"📦 Processing Orders {current_start.date()} to {current_end.date()}"):
                order_data = self.get_order_details(oid)
                if order_data:
                    all_order_items.extend(extract_line_items_from_order(order_data, self.store_id))
                seen_orders.add(oid)
                time.sleep(0.1)  # prevent rate-limiting

            current_start = current_end
        
        # Save data to database
        payments_count = db_utils.save_payments(all_payments, self.store_id)
        orders_count = db_utils.save_order_items(all_order_items, self.store_id)
        
        # Log sync
        db_utils.log_sync(self.store_id, payments_count, orders_count)
        
        print(f"\n✅ Data sync complete for {self.store_name}: {payments_count} payments and {orders_count} order items")
        return {
            'payments': payments_count,
            'orders': orders_count
        }

def load_config():
    """Load configuration from secrets.toml file"""
    if os.path.exists('.streamlit/secrets.toml'):
        return toml.load('.streamlit/secrets.toml')
    else:
        print("⚠️ No secrets.toml file found. Using environment variables or defaults.")
        return {}

def get_store_credentials():
    """Get store credentials from config"""
    config = load_config()
    stores = []
    
    # Look for store configurations in the config file
    for key in config:
        if key.startswith('store_'):
            store_num = key.split('_')[1]
            merchant_id = config.get(f'store_{store_num}', {}).get('merchant_id')
            access_token = config.get(f'store_{store_num}', {}).get('access_token')
            store_name = config.get(f'store_{store_num}', {}).get('name', f'Store {store_num}')
            
            if merchant_id and access_token:
                stores.append({
                    'merchant_id': merchant_id,
                    'access_token': access_token,
                    'name': store_name
                })
    
    return stores

def sync_all_stores(start_date=None):
    """Sync data for all configured stores"""
    # Initialize database
    db_utils.create_database()
    
    # Get store credentials
    stores = get_store_credentials()
    
    if not stores:
        print("⚠️ No store credentials found. Please set up your secrets.toml file.")
        return
    
    # Default to 30 days ago if no start date provided
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Process each store
    for store in stores:
        fetcher = CloverDataFetcher(
            merchant_id=store['merchant_id'],
            access_token=store['access_token'],
            store_name=store['name']
        )
        
        fetcher.fetch_store_data(start_date)

if __name__ == '__main__':
    # Example: Sync all stores for the last 30 days
    sync_all_stores() 