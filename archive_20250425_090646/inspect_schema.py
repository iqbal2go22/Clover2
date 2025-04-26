"""
Script to inspect and compare schemas between SQLite and Supabase
"""

import os
import sys
import sqlite3
import requests
import json
import pandas as pd
import toml

# Load connection details from secrets.toml
try:
    secrets_path = os.path.join('.streamlit', 'secrets.toml')
    secrets = toml.load(secrets_path)
    
    supabase_admin = secrets.get('connections', {}).get('supabase_admin', {})
    project_url = supabase_admin.get('project_url', '')
    api_key = supabase_admin.get('api_key', '')
    
    if not project_url or not api_key:
        print("❌ Missing project_url or api_key in secrets.toml")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error loading secrets: {str(e)}")
    sys.exit(1)

# Set up headers for Supabase REST API
headers = {
    "apikey": api_key,
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Define the SQLite database path
sqlite_db_path = "clover_dashboard.db"

# Check if SQLite database exists
if not os.path.exists(sqlite_db_path):
    print(f"❌ SQLite database not found at: {sqlite_db_path}")
    sys.exit(1)

def get_sqlite_tables():
    """Get all table names from SQLite database"""
    try:
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        return [table[0] for table in tables]
    except Exception as e:
        print(f"❌ Error getting SQLite tables: {str(e)}")
        return []

def get_sqlite_schema(table_name):
    """Get schema for a specific SQLite table with sample data"""
    try:
        conn = sqlite3.connect(sqlite_db_path)
        # Get schema
        schema_df = pd.read_sql(f"PRAGMA table_info({table_name})", conn)
        
        # Get sample data (first row)
        sample_df = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 1", conn)
        conn.close()
        
        return schema_df, sample_df
    except Exception as e:
        print(f"❌ Error getting SQLite schema for {table_name}: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

def get_supabase_schema(table_name):
    """Get schema for a specific Supabase table with sample data"""
    try:
        response = requests.get(
            f"{project_url}/rest/v1/{table_name}?limit=1",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # Create a DataFrame from the sample data
                sample_df = pd.DataFrame([data[0]])
                # Extract column names and types
                columns = list(data[0].keys())
                return columns, sample_df
            else:
                # Table exists but is empty
                return [], pd.DataFrame()
        else:
            print(f"❌ Error getting Supabase schema for {table_name}: Status {response.status_code}")
            return [], pd.DataFrame()
    except Exception as e:
        print(f"❌ Error getting Supabase schema for {table_name}: {str(e)}")
        return [], pd.DataFrame()

def compare_schemas():
    """Compare schemas between SQLite and Supabase"""
    # Get all SQLite tables
    sqlite_tables = get_sqlite_tables()
    
    for table in sqlite_tables:
        print(f"\n{'='*80}")
        print(f"TABLE: {table}")
        print(f"{'='*80}")
        
        # Get SQLite schema and sample data
        sqlite_schema, sqlite_sample = get_sqlite_schema(table)
        
        if not sqlite_schema.empty:
            print("\nSQLite Schema:")
            print(f"{'Column Name':<20} {'Type':<10} {'Not Null':<10} {'Primary Key':<12}")
            print('-' * 60)
            for _, row in sqlite_schema.iterrows():
                print(f"{row['name']:<20} {row['type']:<10} {row['notnull']:<10} {row['pk']:<12}")
                
            print("\nSQLite Sample Data:")
            if not sqlite_sample.empty:
                print(sqlite_sample.iloc[0].to_dict())
            else:
                print("No data in table")
        else:
            print("\nCould not retrieve SQLite schema")
            
        # Get Supabase schema and sample data
        supabase_columns, supabase_sample = get_supabase_schema(table)
        
        if supabase_columns:
            print("\nSupabase Schema:")
            print(f"{'Column Name':<20}")
            print('-' * 20)
            for column in supabase_columns:
                print(f"{column:<20}")
                
            print("\nSupabase Sample Data:")
            if not supabase_sample.empty:
                print(supabase_sample.iloc[0].to_dict())
            else:
                print("No data in table")
        else:
            print("\nCould not retrieve Supabase schema or table doesn't exist")
        
        # Compare columns
        if not sqlite_schema.empty and supabase_columns:
            sqlite_columns = sqlite_schema['name'].tolist()
            print("\nColumn Comparison:")
            print(f"{'Column Name':<20} {'In SQLite':<10} {'In Supabase':<12}")
            print('-' * 50)
            
            # All columns from both sources
            all_columns = list(set(sqlite_columns + supabase_columns))
            all_columns.sort()
            
            for column in all_columns:
                in_sqlite = "✓" if column in sqlite_columns else "✗"
                in_supabase = "✓" if column in supabase_columns else "✗"
                print(f"{column:<20} {in_sqlite:<10} {in_supabase:<12}")
    
    print("\nSchema comparison completed!")

# Execute the comparison
compare_schemas() 