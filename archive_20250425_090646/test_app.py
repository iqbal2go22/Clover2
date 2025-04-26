import streamlit as st

st.title("Clover Dashboard - Test App")
st.write("If you can see this, the deployment is working!")

# Display the secrets (without exposing sensitive values)
st.subheader("Checking Configuration")

if hasattr(st, 'secrets'):
    if 'supabase' in st.secrets:
        st.success("✅ Supabase configuration found")
    else:
        st.error("❌ Supabase configuration missing")
        
    if 'store_1' in st.secrets:
        st.success(f"✅ Store configuration found: {st.secrets.store_1.name}")
    else:
        st.error("❌ Store configuration missing")
else:
    st.error("❌ No secrets configuration found")

st.write("This is a test app to verify the deployment works. Once confirmed, you can update the main app file.") 