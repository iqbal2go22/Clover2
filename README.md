# Clover Executive Dashboard

A comprehensive dashboard to monitor sales data and manage expenses for Clover POS systems.

## Features

- **Sales Monitoring**: View total sales, order count, and average order value
- **Date Range Selection**: Filter data by predefined date ranges (Today, Yesterday, Last 7 Days, Last 30 Days, This Month, Last Month)
- **Expense Management**: Add, edit, and delete expenses with categorization
- **Data Visualization**: Interactive charts for sales trends
- **Multi-store Support**: Switch between different store locations
- **Cloud Database**: Utilizes Supabase for secure data storage

## Requirements

The application requires the following Python packages:
- streamlit
- pandas
- plotly
- requests
- python-dotenv
- supabase

See `requirements.txt` for complete dependencies and versions.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure Supabase credentials:
   - Create a `.streamlit/secrets.toml` file with the following content:
   ```
   [supabase]
   url = "YOUR_SUPABASE_URL"
   key = "YOUR_SUPABASE_API_KEY"
   service_role_key = "YOUR_SUPABASE_SERVICE_ROLE_KEY"
   ```

3. Run the application:
   ```
   streamlit run app.py
   ```

## Deployment

See `deploy_to_streamlit_cloud.md` for detailed instructions on deploying to Streamlit Cloud.

## Project Structure

- `app.py`: Main Streamlit application
- `cloud_db_utils.py`: Database interaction utilities
- `requirements.txt`: Project dependencies
- `.streamlit/`: Streamlit configuration directory

## More Information

For detailed information about Supabase connection options, check the `README_SUPABASE.md` file.

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