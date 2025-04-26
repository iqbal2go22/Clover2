# Streamlit Cloud Migration Plan

This document outlines the **exact** steps needed to move the Clover Dashboard from SQLite to Supabase and deploy it on Streamlit Cloud.

## Step 1: Prepare the Deployment Files

1. Keep only the essential files:
   - `app_deployed.py` (rename to `app.py`)
   - `cloud_db_utils.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `.gitignore`
   - `README.md`

2. Delete or move unnecessary files to an archive folder:
   - `direct_migrate.py`
   - `migrate_rest_api.py`
   - `fix_schema.sql`
   - `inspect_schema.py`
   - `fix_migration.py`
   - `app_cloud.py`
   - `setup_supabase_rest.py`
   - All test scripts

## Step 2: Rename and Final Check

1. Rename the main application file:
   ```bash
   mv app_deployed.py app.py
   ```

2. Check that `app.py` correctly imports `cloud_db_utils.py`

3. Verify `.streamlit/config.toml` exists with proper settings:
   ```toml
   [server]
   headless = true

   [browser]
   gatherUsageStats = false
   ```

## Step 3: Prepare Your GitHub Repository

1. Create a new GitHub repository

2. Initialize your local git repository:
   ```bash
   git init
   ```

3. Add only the essential files:
   ```bash
   git add app.py
   git add cloud_db_utils.py
   git add requirements.txt
   git add .gitignore
   git add README.md
   git add -f .streamlit/config.toml
   ```

4. Commit and push to GitHub:
   ```bash
   git commit -m "Initial deployment version"
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
   git branch -M main
   git push -u origin main
   ```

## Step 4: Deploy on Streamlit Cloud

1. Go to [Streamlit Cloud](https://share.streamlit.io/)

2. Click "New app"

3. Connect to your GitHub repository:
   - Select your repository
   - Branch: `main`
   - Main file path: `app.py`

4. Configure secrets - add exactly as shown:
   ```toml
   [connections.supabase]
   project_url = "https://yegrbbtxlsfbrlyavmbg.supabase.co"
   api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ3JiYnR4bHNmYnJseWF2bWJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODI1NDg3NDgsImV4cCI6MTk5ODEyNDc0OH0.oYtqAj4HbVjiRB-bjJ-xPTJQYcpioU3hbLBYm0-QxTU"
   pooling_url = "postgresql://postgres.yegrbbtxlsfbrlyavmbg:721AFFTNZmnQ3An7@yegrbbtxlsfbrlyavmbg.supabase.co:6543/postgres"
   
   [connections.supabase_admin]
   project_url = "https://yegrbbtxlsfbrlyavmbg.supabase.co"
   api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InllZ3JiYnR4bHNmYnJseWF2bWJnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY4MjU0ODc0OCwiZXhwIjoxOTk4MTI0NzQ4fQ.8XF8KhYfgWR7wcOkDbMuRD0L8HVtE-QKgKjbHzqbprM"
   
   [store_1]
   name = "Laurel"
   merchant_id = "4VZSM7038BKQ1"
   access_token = "b9f678d7-9b27-e971-d9e4-feab8b227c96"
   
   [store_2]
   name = "Algiers"
   merchant_id = "K25SHP45Z91H1"
   access_token = "fb51be17-f0c4-c58c-0e08-44bcd4bbc5ab"
   
   [store_3]
   name = "Hattiesburg"
   merchant_id = "J3N08YKN8TSD1"
   access_token = "5608c683-801e-d4cf-092d-abfc907eafcc"
   ```

5. Click "Deploy"

## Step 5: Verify Your Deployment

1. Check the app logs from the "Manage app" menu for any errors

2. Test the app to make sure it connects to Supabase correctly

3. Verify all data is displayed as expected

## Troubleshooting

If you encounter issues:

1. **Database connection error**:
   - Check that Supabase credentials are correct
   - Make sure Supabase tables exist and have been properly created

2. **Missing data**:
   - Verify data was migrated to Supabase correctly
   - Check for any column name mismatches

3. **Visual issues**:
   - Ensure all dependencies are in requirements.txt 