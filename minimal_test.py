import streamlit as st

st.set_page_config(page_title="Minimal Test", layout="wide")
st.title("Minimal Test App")
st.write("This is a minimal test app with no external connections.")

if st.button("Click Me"):
    st.success("Button clicked!")

st.write(f"Streamlit version: {st.__version__}") 