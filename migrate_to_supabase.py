import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

print("=" * 80)
print("SQLITE TO SUPABASE MIGRATION UTILITY")
print("=" * 80)

# Supabase connection - UPDATE THIS with your actual connection string
# Using connection pooling which is more likely to work with Streamlit Cloud
DATABASE_URL = "postgresql://postgres.yegrbbtxlsfbrlyavmbg:721AFFTNZmnQ3An7@yegrbbtxlsfbrlyavmbg.supabase.co:6543/postgres"

print("\nStep 1: Connecting to databases...")

try:
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('clover_dashboard.db')
    print("✅ Connected to SQLite database")
    
    # Connect to Supabase
    engine = create_engine(DATABASE_URL)
    pg_conn = engine.connect()
    print("✅ Connected to Supabase database")
    
    # Tables to migrate
    tables = [
        'stores',
        'payments',
        'order_items',
        'expenses',
        'sync_log'
    ]
    
    print("\nStep 2: Creating tables in Supabase...")
    
    # Create tables if they don't exist
    try:
        # Create stores table
        pg_conn.execute(text("""
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            merchant_id TEXT NOT NULL,
            api_key TEXT,
            access_token TEXT,
            last_sync_date TIMESTAMP
        )
        """))
        
        # Create payments table
        pg_conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            store_id INTEGER,
            order_id TEXT,
            amount INTEGER,
            created_time TIMESTAMP
        )
        """))
        
        # Create order_items table
        pg_conn.execute(text("""
        CREATE TABLE IF NOT EXISTS order_items (
            id TEXT PRIMARY KEY,
            store_id INTEGER, 
            order_id TEXT,
            name TEXT,
            price REAL,
            quantity INTEGER,
            created_time TIMESTAMP
        )
        """))
        
        # Create expenses table
        pg_conn.execute(text("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            store_id INTEGER,
            date DATE,
            amount REAL,
            category TEXT,
            description TEXT
        )
        """))
        
        # Create sync_log table
        pg_conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id SERIAL PRIMARY KEY,
            store_id INTEGER,
            sync_date TIMESTAMP,
            items_count INTEGER
        )
        """))
        print("✅ Tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise
    
    print("\nStep 3: Migrating data...")
    
    # Migrate each table
    for table in tables:
        print(f"  Migrating '{table}'...")
        try:
            # Read from SQLite
            df = pd.read_sql(f"SELECT * FROM {table}", sqlite_conn)
            if len(df) == 0:
                print(f"  ⚠️ No data found in '{table}' table")
                continue
                
            print(f"  - Read {len(df)} rows from SQLite")
            
            # Fix any column type issues
            for col in df.columns:
                if df[col].dtype == 'object' and col != 'id':
                    # Convert any 'None' strings to None
                    df[col] = df[col].replace('None', None)
            
            # Write to PostgreSQL
            df.to_sql(table, engine, if_exists='replace', index=False)
            print(f"  ✅ Wrote {len(df)} rows to Supabase")
        except Exception as e:
            print(f"  ❌ Error migrating '{table}': {e}")
    
    print("\nStep 4: Verifying migration...")
    
    # Verify data was migrated
    for table in tables:
        try:
            count_df = pd.read_sql(text(f"SELECT COUNT(*) FROM {table}"), pg_conn)
            print(f"  - '{table}': {count_df.iloc[0, 0]} rows")
        except Exception as e:
            print(f"  ❌ Error verifying '{table}': {e}")
    
    print("\n✅ Migration completed successfully!")
    
except Exception as e:
    print(f"\n❌ Migration failed: {e}")
finally:
    # Close connections
    try:
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()
    except:
        pass

print("\n" + "=" * 80)
print("\nNext steps:")
print("1. Update your app to use Supabase instead of SQLite")
print("2. Deploy your app to Streamlit Cloud")
print("=" * 80) 