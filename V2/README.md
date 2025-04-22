# Clover Dashboard - Version 2

This directory contains the complete codebase for Version 2 of the Clover Dashboard application.

## Features Included in V2

- **Multi-Store Support**: Dashboard supports Laurel, Algiers, and Hattiesburg stores
- **Individual Store Cards**: Visual display of performance metrics for each store
- **Optimized Data Queries**: Consistent query approach for accurate sales and order counts
- **Incremental Data Sync**: Smart syncing that only fetches new data since last sync
- **Admin Tools**: Utilities for managing store data, including repair options
- **Store Cleanup**: Tool to remove demo stores and keep only legitimate ones
- **Historical Data Loading**: Ability to load all historical data when needed

## Files Included

- `app.py` - Main Streamlit application
- `clover_data_fetcher.py` - API integration with Clover
- `db_utils.py` - Database utilities
- `incremental_sync.py` - Smart incremental data synchronization
- `get_store_stats.py` - Tool to generate store statistics
- `check_store_data.py` - Check database status
- `load_historical_data.py` - Historical data loader
- `admin_tools.py` - Admin utilities interface
- `clean_stores.py` - Tool to remove demo stores
- `load_algiers_data.py` - Special loader for Algiers with rate limiting

## How to Revert to V2

If you need to revert to this version from a future version:

1. Stop any running Streamlit instances
2. Copy all files from this directory to the main application directory:

```powershell
Copy-Item V2/* -Destination ./ -Force
```

3. Restart the application:

```powershell
py -m streamlit run app.py
```

## Database Schema

The application uses a SQLite database (`clover_dashboard.db`) with the following key tables:

- `stores` - Store information
- `payments` - Payment transactions
- `order_items` - Order line items
- `sync_log` - Records of data synchronization

## Query Pattern

For consistency, all sales and order count metrics use this standardized query pattern:

```sql
SELECT COUNT(DISTINCT order_id) as orders, 
       SUM(price * COALESCE(quantity, 1)) as sales
FROM order_items
WHERE created_time >= ? AND created_time <= ?
``` 