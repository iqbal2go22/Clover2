import streamlit as st

st.title("Minimal Test App")
st.write("If you can see this, the deployment is working!")

# Super simple counter example
count = 0
if 'count' in st.session_state:
    count = st.session_state.count

if st.button("Click me"):
    count += 1
    st.session_state.count = count

st.write(f"Button has been clicked {count} times") 