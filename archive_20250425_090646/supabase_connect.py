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
        """Connect to Supabase REST API.
        
        Parameters not explicitly provided will be sourced from secrets.toml
        """
        # Get connection parameters from secrets
        self.project_url = self._secrets.get("project_url")
        self.api_key = self._secrets.get("api_key")
        
        # Override with constructor args if provided
        if "project_url" in kwargs:
            self.project_url = kwargs.pop("project_url")
        if "api_key" in kwargs:
            self.api_key = kwargs.pop("api_key")
            
        # Validate connection parameters
        if not self.project_url or not self.api_key:
            raise ConnectionError("Missing required Supabase connection parameters: project_url and api_key")
            
        # Set up headers for Supabase REST API
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Test connection immediately
        self.test_connection()
    
    def test_connection(self) -> bool:
        """Test the connection to Supabase."""
        try:
            response = requests.get(
                f"{self.project_url}/rest/v1/",
                headers=self.headers,
                timeout=10
            )
            return response.status_code in (200, 201, 204)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Supabase: {str(e)}")
    
    def get_all_tables(self) -> List[str]:
        """Get list of all tables in the database."""
        try:
            # List all tables by querying pg_tables
            rpc_url = f"{self.project_url}/rest/v1/rpc/get_all_tables"
            payload = {}
            
            response = requests.post(
                rpc_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code in (200, 201):
                tables = response.json()
                if isinstance(tables, list):
                    return tables
            return []
        except Exception as e:
            st.warning(f"Could not list tables: {str(e)}")
            return []

    def query(self, table: str, columns: str = "*", filters: Dict = None, limit: int = None) -> pd.DataFrame:
        """Query data from a Supabase table.
        
        Args:
            table: The name of the table to query
            columns: The columns to select (default: "*")
            filters: Dictionary of filter conditions
            limit: Maximum number of rows to return
            
        Returns:
            DataFrame containing the query results
        """
        url = f"{self.project_url}/rest/v1/{table}"
        params = {}
        
        # Add select columns
        params["select"] = columns
        
        # Add filters if provided
        if filters:
            for key, value in filters.items():
                params[key] = value
                
        # Add limit if provided
        if limit:
            params["limit"] = limit
            
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                return pd.DataFrame(data)
            else:
                st.error(f"Query failed: {response.status_code} - {response.text}")
                return pd.DataFrame()
        except Exception as e:
            st.error(f"Query error: {str(e)}")
            return pd.DataFrame()
            
    def insert(self, table: str, data: Dict[str, Any] or List[Dict[str, Any]]) -> Dict:
        """Insert data into a Supabase table.
        
        Args:
            table: The name of the table
            data: Dictionary or list of dictionaries containing the data to insert
            
        Returns:
            Dictionary containing the response from Supabase
        """
        url = f"{self.project_url}/rest/v1/{table}"
        headers = self.headers.copy()
        headers["Prefer"] = "return=representation"
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=15
            )
            
            if response.status_code in (200, 201):
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"{response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update(self, table: str, data: Dict[str, Any], filters: Dict) -> Dict:
        """Update data in a Supabase table.
        
        Args:
            table: The name of the table
            data: Dictionary containing the data to update
            filters: Dictionary of filter conditions
            
        Returns:
            Dictionary containing the response from Supabase
        """
        url = f"{self.project_url}/rest/v1/{table}"
        headers = self.headers.copy()
        headers["Prefer"] = "return=representation"
        
        params = {}
        for key, value in filters.items():
            params[key] = value
            
        try:
            response = requests.patch(
                url,
                headers=headers,
                params=params,
                json=data,
                timeout=15
            )
            
            if response.status_code in (200, 204):
                return {"success": True, "data": response.json() if response.status_code == 200 else None}
            else:
                return {"success": False, "error": f"{response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete(self, table: str, filters: Dict) -> Dict:
        """Delete data from a Supabase table.
        
        Args:
            table: The name of the table
            filters: Dictionary of filter conditions
            
        Returns:
            Dictionary containing the response from Supabase
        """
        url = f"{self.project_url}/rest/v1/{table}"
        headers = self.headers.copy()
        headers["Prefer"] = "return=representation"
        
        params = {}
        for key, value in filters.items():
            params[key] = value
            
        try:
            response = requests.delete(
                url,
                headers=headers,
                params=params,
                timeout=15
            )
            
            if response.status_code in (200, 204):
                return {"success": True, "data": response.json() if response.status_code == 200 else None}
            else:
                return {"success": False, "error": f"{response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def initialize_tables(self) -> Dict:
        """Initialize database tables using an RPC function."""
        try:
            rpc_url = f"{self.project_url}/rest/v1/rpc/initialize_tables"
            payload = {}
            
            response = requests.post(
                rpc_url,
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code in (200, 201, 204):
                return {"success": True, "result": response.json() if response.text else {"message": "Tables initialized"}}
            else:
                return {"success": False, "error": f"{response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Main app
st.title("Supabase Connection Test (Using st.connection)")

# Initialize the connection
try:
    conn = st.connection("supabase", type=SupabaseConnection)
    
    # Display configuration
    if hasattr(conn, 'project_url') and hasattr(conn, 'api_key'):
        st.write(f"Project URL: {conn.project_url}")
        masked_key = conn.api_key[:10] + "..." + conn.api_key[-5:] if len(conn.api_key) > 15 else conn.api_key
        st.write(f"API Key: {masked_key}")
        connection_status = "✅ Connected"
    else:
        connection_status = "❌ Not connected"
    
    st.success(f"Connection Status: {connection_status}")
    
except Exception as e:
    st.error(f"Failed to initialize connection: {str(e)}")
    st.info("Make sure your secrets.toml file contains the necessary connection information.")
    connection_status = "❌ Error"

# Test connection button
if st.button("Test Connection", type="primary"):
    st.write("Testing connection to Supabase...")
    
    try:
        if conn.test_connection():
            st.success("✅ Successfully connected to Supabase REST API!")
            
            # Try to get tables list
            tables = conn.get_all_tables()
            if tables:
                st.success(f"✅ Found {len(tables)} tables in the database!")
                st.write("Tables found:")
                for table in tables:
                    st.write(f"- {table}")
            else:
                st.info("No tables found or insufficient permissions.")
            
            # Attempt to check if specific tables exist
            for table_name in ["stores", "payments", "order_items"]:
                try:
                    data = conn.query(table_name, limit=1)
                    if not data.empty:
                        st.success(f"✅ Table '{table_name}' exists and has data!")
                    else:
                        st.warning(f"Table '{table_name}' exists but may be empty.")
                except Exception as e:
                    st.error(f"Error checking table '{table_name}': {str(e)}")
        else:
            st.error("❌ Failed to connect to Supabase.")
            
    except Exception as e:
        st.error(f"❌ Connection test failed: {str(e)}")

# Initialize Database button
if st.button("Initialize Database", type="primary"):
    st.write("Initializing database tables...")
    
    try:
        result = conn.initialize_tables()
        if result["success"]:
            st.success("✅ Tables initialized successfully!")
            st.write(f"Result: {result['result']}")
        else:
            st.error(f"❌ Failed to initialize tables: {result['error']}")
            st.info("Note: You may need to set up an RPC function named 'initialize_tables' in your Supabase project.")
    except Exception as e:
        st.error(f"❌ Error initializing tables: {str(e)}")
        
# Display help info
st.markdown("---")
st.markdown("""
### Using st.connection with Supabase
This app uses Streamlit's connection API (`st.connection`) with a custom Supabase connection class.
This offers better connection caching and management compared to direct REST API calls.

### Current Configuration
Make sure your secrets.toml file contains:
""")

st.code("""
[connections.supabase]
project_url = "https://your-project-id.supabase.co"
api_key = "your-anon-key"
""", language="toml")

st.markdown("""
### Setting up Database Tables
For this to work fully, you may need to create an RPC function in your Supabase project.
""")

st.markdown("© 2024 Clover Executive Dashboard | Cloud Version") 