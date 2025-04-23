import streamlit as st
import psycopg2
import time

st.title("Supabase Direct Connection Test")

# Connection parameters
pooling_params = {
    "host": "yegrbbtxlsfbrlyavmbg.supabase.co",
    "port": "6543",
    "dbname": "postgres",
    "user": "postgres.yegrbbtxlsfbrlyavmbg",
    "password": "721AFFTNZmnQ3An7",
    "connect_timeout": 10
}

direct_params = {
    "host": "db.yegrbbtxlsfbrlyavmbg.supabase.co",
    "port": "5432",
    "dbname": "postgres",
    "user": "postgres",
    "password": "721AFFTNZmnQ3An7",
    "connect_timeout": 15
}

if st.button("Test Connection Pooling (Port 6543)", type="primary"):
    st.write("Attempting connection via connection pooling...")
    try:
        conn = psycopg2.connect(**pooling_params)
        st.success("✅ Connected successfully!")
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        st.write(f"Database version: {version[0]}")
        
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Connection failed: {str(e)}")

if st.button("Test Direct Connection (Port 5432)", type="primary"):
    st.write("Attempting direct connection...")
    try:
        conn = psycopg2.connect(**direct_params)
        st.success("✅ Connected successfully!")
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        st.write(f"Database version: {version[0]}")
        
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Connection failed: {str(e)}")

if st.button("Test Connection With Retry", type="primary"):
    max_retries = 3
    methods = [
        {"name": "Connection Pooling", "params": pooling_params},
        {"name": "Direct Connection", "params": direct_params}
    ]
    
    for method in methods:
        st.write(f"Trying {method['name']}...")
        
        for attempt in range(max_retries):
            try:
                st.write(f"Attempt {attempt + 1}...")
                conn = psycopg2.connect(**method['params'])
                st.success(f"✅ Connected successfully using {method['name']}!")
                
                # Test query
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                st.write(f"Database version: {version[0]}")
                
                cursor.close()
                conn.close()
                break
            except Exception as e:
                st.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    st.write(f"Waiting 2 seconds before retry...")
                    time.sleep(2)

st.markdown("---")
st.write("If all connection methods fail, it may indicate network restrictions between Streamlit Cloud and Supabase.") 