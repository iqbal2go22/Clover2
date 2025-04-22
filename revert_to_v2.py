import os
import shutil
import sys
import subprocess

def revert_to_v2():
    """Revert the application to V2 snapshot"""
    # Check if V2 directory exists
    if not os.path.exists('V2'):
        print("Error: V2 directory not found. Cannot revert.")
        return False
    
    # List of core files to copy
    core_files = [
        'app.py',
        'clover_data_fetcher.py', 
        'db_utils.py',
        'incremental_sync.py',
        'get_store_stats.py',
        'check_store_data.py',
        'load_historical_data.py',
        'admin_tools.py',
        'clean_stores.py',
        'load_algiers_data.py'
    ]
    
    # Check if any Streamlit processes are running
    try:
        print("Checking for running Streamlit processes...")
        result = subprocess.run(['tasklist', '/fi', 'imagename eq streamlit.exe'], 
                               capture_output=True, text=True)
        if 'streamlit.exe' in result.stdout:
            confirm = input("Streamlit is currently running. Do you want to continue? (y/n): ")
            if confirm.lower() != 'y':
                print("Revert cancelled.")
                return False
    except Exception as e:
        print(f"Warning: Could not check running processes - {str(e)}")
    
    # Copy files from V2 directory
    print("\nReverting to V2...")
    copied_files = []
    for file in core_files:
        source = os.path.join('V2', file)
        if os.path.exists(source):
            try:
                shutil.copy2(source, file)
                copied_files.append(file)
                print(f"  ✓ Restored {file}")
            except Exception as e:
                print(f"  ✗ Failed to copy {file}: {str(e)}")
        else:
            print(f"  ! Warning: {file} not found in V2 directory")
    
    print(f"\nSuccessfully reverted {len(copied_files)}/{len(core_files)} files to V2.")
    print("\nTo restart the application, run: py -m streamlit run app.py")
    
    return True

if __name__ == "__main__":
    revert_to_v2() 