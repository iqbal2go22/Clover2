#!/usr/bin/env python
"""
Cleanup script for Clover Dashboard project.
This script organizes project files for deployment by moving non-essential files to an archive folder.
"""

import os
import shutil
import datetime

def cleanup_project():
    """
    Cleanup the project directory by:
    1. Creating an archive folder with timestamp
    2. Moving non-essential files to the archive folder
    3. Keeping only essential files for deployment
    4. Renaming app_deployed.py to app.py if it exists
    """
    # Create archive folder with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_folder = f"archive_{timestamp}"
    
    if not os.path.exists(archive_folder):
        os.makedirs(archive_folder)
        print(f"Created archive folder: {archive_folder}")
    
    # Essential files to keep (not to be moved)
    essential_files = [
        "app.py",
        "cloud_db_utils.py",
        "requirements.txt",
        "README.md",
        "deploy_to_streamlit_cloud.md",
        ".streamlit",
        ".gitignore",
        ".git"
    ]
    
    # Rename app_deployed.py to app.py if it exists
    if os.path.exists("app_deployed.py"):
        if os.path.exists("app.py"):
            # Move existing app.py to archive
            shutil.move("app.py", os.path.join(archive_folder, "app.py"))
            print("Moved existing app.py to archive")
        
        # Rename app_deployed.py to app.py
        os.rename("app_deployed.py", "app.py")
        print("Renamed app_deployed.py to app.py")
    
    # Move non-essential files to archive
    moved_count = 0
    
    for item in os.listdir("."):
        # Skip current script, essential files, and the archive folder itself
        if (item == os.path.basename(__file__) or 
            item in essential_files or 
            item == archive_folder or
            item.startswith(".")):
            continue
        
        try:
            shutil.move(item, os.path.join(archive_folder, item))
            moved_count += 1
            print(f"Moved {item} to archive")
        except Exception as e:
            print(f"Error moving {item}: {e}")
    
    print(f"\nCleanup complete! Moved {moved_count} files to {archive_folder}")
    print("Project is now ready for deployment to Streamlit Cloud")
    print("For deployment instructions, see deploy_to_streamlit_cloud.md")

if __name__ == "__main__":
    print("Starting project cleanup for deployment...")
    cleanup_project() 