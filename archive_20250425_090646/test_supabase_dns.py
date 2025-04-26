import socket
import requests
import time
import streamlit as st

st.title("Supabase Connection Diagnostic")

# Check DNS resolution for the hostname
hostnames = [
    "yegrbbtxlsfbrlyavmbg.supabase.co",
    "db.yegrbbtxlsfbrlyavmbg.supabase.co"
]

st.subheader("DNS Resolution Test")
for hostname in hostnames:
    try:
        st.write(f"Testing hostname: **{hostname}**")
        start_time = time.time()
        ip_address = socket.gethostbyname(hostname)
        resolution_time = time.time() - start_time
        st.success(f"✅ DNS Resolution successful: {hostname} → {ip_address} (took {resolution_time:.2f}s)")
    except socket.gaierror as e:
        st.error(f"❌ DNS Resolution failed: {hostname} - Error: {str(e)}")

# Try connecting to Supabase API
st.subheader("Supabase API Connection Test")
try:
    url = "https://yegrbbtxlsfbrlyavmbg.supabase.co/rest/v1/?apikey=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ3JiYnR4bHNmYnJseWF2bWJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTQ2OTA4NTcsImV4cCI6MjAxMDI2Njg1N30.CQRKj-CzkPWtdWgIOuRKUeXVfZUK5j77l_3X9M5-V2Y"
    
    st.write(f"Testing API URL: {url}")
    start_time = time.time()
    response = requests.get(
        url,
        headers={
            "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ3JiYnR4bHNmYnJseWF2bWJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTQ2OTA4NTcsImV4cCI6MjAxMDI2Njg1N30.CQRKj-CzkPWtdWgIOuRKUeXVfZUK5j77l_3X9M5-V2Y",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ3JiYnR4bHNmYnJseWF2bWJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTQ2OTA4NTcsImV4cCI6MjAxMDI2Njg1N30.CQRKj-CzkPWtdWgIOuRKUeXVfZUK5j77l_3X9M5-V2Y"
        },
        timeout=5
    )
    connection_time = time.time() - start_time
    
    if response.status_code in (200, 201, 204):
        st.success(f"✅ API Connection successful (status code: {response.status_code}, took {connection_time:.2f}s)")
    else:
        st.warning(f"⚠️ API Connection returned status code: {response.status_code}, message: {response.text}")
except Exception as e:
    st.error(f"❌ API Connection failed: {str(e)}")

# Try postgres port check
st.subheader("PostgreSQL Port Check")
for port in [5432, 6543]:
    try:
        st.write(f"Testing connection to **yegrbbtxlsfbrlyavmbg.supabase.co:{port}**")
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('yegrbbtxlsfbrlyavmbg.supabase.co', port))
        connection_time = time.time() - start_time
        
        if result == 0:
            st.success(f"✅ Port {port} is open (took {connection_time:.2f}s)")
        else:
            st.error(f"❌ Port {port} is closed or filtered (took {connection_time:.2f}s)")
        
        sock.close()
    except Exception as e:
        st.error(f"❌ Error checking port {port}: {str(e)}")

# Provide alternatives
st.subheader("Alternative Connection Methods")
st.markdown("""
### 1. Use the REST API Connection Instead
Since the PostgreSQL connection is failing, try using the REST API connection instead:

```python
conn = st.connection("supabase", type=SupabaseConnection)
# Use conn.query() method
```

### 2. Try a Different Connection String Format
- Remove `db.` prefix from the hostname
- Try using IP address directly if DNS resolution is working

### 3. Check Supabase Project Status
- Login to Supabase dashboard
- Ensure your project is not paused
- Verify the connection string from project settings
""")

# Show current settings
st.subheader("Current Connection Settings")
if hasattr(st, 'secrets') and 'connections' in st.secrets and 'supabase_sql' in st.secrets.connections:
    url = st.secrets.connections.supabase_sql.get("url", "")
    masked_url = url.replace(":721AFFTNZmnQ3An7@", ":****@")
    st.code(f"Connection URL: {masked_url}") 