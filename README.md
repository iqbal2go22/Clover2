# Clover Merchant Dashboard

A Streamlit dashboard for visualizing sales data from multiple Clover merchant accounts and tracking expenses. This application can be deployed locally or to Streamlit Cloud with Supabase for database storage.

## Features

- Multi-store data aggregation from Clover API
- Sales visualization and analytics
- Expense tracking and management
- Profit & Loss reporting
- Cloud deployment with PostgreSQL database

## Local Setup Instructions

1. Clone this repository:
   ```
   git clone https://github.com/iqbal2go22/CloverDashboard.git
   cd CloverDashboard
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.streamlit/secrets.toml` file with your Clover API credentials:
   ```
   # Store 1
   [store_1]
   name = "Main Store"
   merchant_id = "YOUR_MERCHANT_ID"
   access_token = "YOUR_ACCESS_TOKEN"
   
   # Store 2
   [store_2]
   name = "Second Store"
   merchant_id = "YOUR_MERCHANT_ID_2"
   access_token = "YOUR_ACCESS_TOKEN_2"
   ```

4. Run the application:
   ```
   streamlit run app.py
   ```

## Cloud Deployment

This application can be deployed to Streamlit Cloud with a PostgreSQL database on Supabase:

1. Create a Supabase account and database.
2. Update your `.streamlit/secrets.toml` to include Supabase credentials:
   ```
   [supabase]
   url = "postgresql://username:password@db.yourdatabase.supabase.co:6543/postgres"
   
   [clover]
   merchant_id = "YOUR_MERCHANT_ID"
   api_key = "YOUR_API_KEY"
   access_token = "YOUR_ACCESS_TOKEN"
   ```
3. Deploy to Streamlit Cloud using the `app_supabase.py` as the entry point.
4. See `deployment_guide.md` for detailed deployment instructions.

## Getting Clover API Credentials

1. Go to [Clover Developer Dashboard](https://sandbox.dev.clover.com/developers)
2. Create a new app (or use an existing one)
3. Generate an OAuth token for your merchant account
4. Use that token and merchant ID in the secrets.toml file

## Usage

1. Start the application with `streamlit run app.py`
2. Use the "Sync Data" button to fetch the latest data from Clover
3. Use the dashboard controls to filter and analyze your data
4. Add expenses through the Expenses tab
5. View Profit & Loss reports

## Database Structure

The application uses either SQLite (local) or PostgreSQL (cloud) to store:
- Store information
- Payment data from Clover API
- Order line item details
- User-entered expenses

## Migration from SQLite to Supabase

To migrate your existing SQLite data to Supabase:
```
python migrate_to_supabase.py
```

## Development Roadmap

- [x] Basic data retrieval and storage
- [x] Simple dashboard UI for verification
- [x] Enhanced sales analytics
- [x] Expense tracking functionality
- [x] Cloud deployment with Supabase
- [ ] Detailed P&L reporting
- [ ] Data export functionality 