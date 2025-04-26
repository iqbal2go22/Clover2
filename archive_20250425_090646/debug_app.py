import sys
import os
import platform
import traceback

# Write debug info to a file that we can access
with open('/tmp/streamlit_debug.log', 'w') as f:
    f.write(f"Python version: {sys.version}\n")
    f.write(f"Platform: {platform.platform()}\n")
    f.write(f"Working directory: {os.getcwd()}\n")
    f.write(f"Files in directory: {os.listdir()}\n")
    f.write("\nAttempting to import streamlit...\n")
    
    try:
        import streamlit as st
        f.write("Streamlit imported successfully\n")
        f.write(f"Streamlit version: {st.__version__}\n")
        
        # Try to use streamlit
        f.write("Attempting to use streamlit...\n")
        try:
            st.write("Debug app is running")
            f.write("Successfully used st.write()\n")
        except Exception as e:
            f.write(f"Error using st.write(): {str(e)}\n")
            f.write(traceback.format_exc())
    except Exception as e:
        f.write(f"Error importing streamlit: {str(e)}\n")
        f.write(traceback.format_exc())

# Now try to run the actual app
try:
    import streamlit as st
    st.write("Debug App")
    st.write("If you can see this, the app is working!")
    
    # Show system info
    st.subheader("System Information")
    st.code(f"""
    Python version: {sys.version}
    Platform: {platform.platform()}
    Streamlit version: {st.__version__}
    Working directory: {os.getcwd()}
    """)
    
    # Create a simple counter to test functionality
    if 'count' not in st.session_state:
        st.session_state.count = 0
        
    if st.button('Increment'):
        st.session_state.count += 1
        
    st.write(f'Count: {st.session_state.count}')
    
except Exception as e:
    # If we get here, we can't even start Streamlit
    # Write error to a file as a last resort
    with open('/tmp/streamlit_error.log', 'w') as f:
        f.write(f"Fatal error: {str(e)}\n")
        f.write(traceback.format_exc()) 