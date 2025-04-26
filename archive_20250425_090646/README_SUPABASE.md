# Streamlit Supabase Connection Guide

This guide explains how to use Streamlit's `st.connection` feature to connect to Supabase, enabling better management and caching of database connections.

## Two Approaches

There are two ways to connect to Supabase from Streamlit:

1. **SQL Connection** (Recommended): Uses Streamlit's built-in `SQLConnection` class to connect directly to Supabase's PostgreSQL database.
2. **Custom Supabase Connection**: Uses a custom connection class that connects to Supabase's REST API.

## 1. SQL Connection (Recommended)

This approach connects directly to Supabase's PostgreSQL database using Streamlit's built-in SQL connection functionality.

### Configuration

Add this to your `.streamlit/secrets.toml` file:

```toml
[connections.supabase_sql]
type = "postgresql"
url = "postgresql://postgres.yourprojectref:password@yourprojectref.supabase.co:6543/postgres"
```

Notes:
- Use port `6543` for connection pooling (recommended)
- Use port `5432` for direct connection
- Get your connection string from Supabase Dashboard → Project Settings → Database → Connection string

### Usage

```python
import streamlit as st
import pandas as pd

# Initialize the connection
conn = st.connection("supabase_sql")

# Use the connection to query data
df = conn.query("SELECT * FROM your_table;")
st.dataframe(df)
```

## 2. Custom Supabase Connection

This approach uses a custom connection class to connect to Supabase's REST API.

### Configuration

Add this to your `.streamlit/secrets.toml` file:

```toml
[connections.supabase]
project_url = "https://yourprojectref.supabase.co"
api_key = "your-anon-key"
```

### Custom Connection Class

Create a file named `supabase_connect.py` with the following code:

```python
import streamlit as st
import requests
import pandas as pd
from streamlit.connections import BaseConnection
from typing import Dict, List, Any, Optional

class SupabaseConnection(BaseConnection):
    """A Streamlit connection to Supabase using the REST API."""
    
    def __init__(self, connection_name: str, **kwargs):
        super().__init__(connection_name, **kwargs)
        self._connect(**kwargs)
    
    def _connect(self, **kwargs) -> None:
        # Get connection parameters from secrets
        self.project_url = self._secrets.get("project_url")
        self.api_key = self._secrets.get("api_key")
        
        # Override with constructor args if provided
        if "project_url" in kwargs:
            self.project_url = kwargs.pop("project_url")
        if "api_key" in kwargs:
            self.api_key = kwargs.pop("api_key")
            
        # Set up headers for Supabase REST API
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def query(self, table: str, columns: str = "*", filters: Dict = None, limit: int = None) -> pd.DataFrame:
        """Query data from a Supabase table."""
        url = f"{self.project_url}/rest/v1/{table}"
        params = {"select": columns}
        
        if filters:
            for key, value in filters.items():
                params[key] = value
                
        if limit:
            params["limit"] = limit
            
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return pd.DataFrame(data)
            else:
                return pd.DataFrame()
        except Exception as e:
            return pd.DataFrame()
```

### Usage

```python
import streamlit as st
import pandas as pd
from supabase_connect import SupabaseConnection

# Initialize the connection
conn = st.connection("supabase", type=SupabaseConnection)

# Use the connection to query data
df = conn.query("your_table", limit=10)
st.dataframe(df)
```

## Database Utilities

For a more comprehensive solution, check out the `cloud_db_utils.py` file which provides a set of helper functions for common database operations using the SQL connection approach.

## Testing

To test your connection, run one of the test scripts:

```bash
streamlit run sql_supabase.py  # Tests SQL connection
streamlit run test_cloud_db.py  # Tests database utilities
```

## Requirements

Make sure your `requirements.txt` includes:

```
streamlit>=1.44.0  # For st.connection support
pandas
psycopg2-binary  # For SQL connection
requests  # For REST API connection
```

## Troubleshooting

1. **Connection Issues**: Verify your connection string or API key in the secrets.toml file.
2. **Missing Tables**: Ensure your tables exist in the public schema of your Supabase database.
3. **Permission Errors**: Check that your API key has the necessary permissions for the operations you're trying to perform.

---

For more information, refer to the [Streamlit Connections documentation](https://docs.streamlit.io/library/api-reference/connections). 