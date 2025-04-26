# Streamlit Cloud Deployment Checklist

Use this checklist to ensure your app is ready for deployment to Streamlit Cloud with Supabase.

## Pre-Deployment

- [ ] Set up Supabase database
  - [ ] Create Supabase account
  - [ ] Create new project
  - [ ] Get database credentials and REST API key

- [ ] Database Setup
  - [ ] Run `streamlit run setup_supabase_db.py` to create tables
  - [ ] Run `streamlit run migrate_data.py` to transfer existing data (if any)
  - [ ] Run `streamlit run test_connection.py` to verify connection works

- [ ] Code Changes
  - [ ] Ensure app.py imports from cloud_db_utils.py instead of db_utils.py
  - [ ] Update any SQLite-specific code to use Supabase
  - [ ] Remove any local file operations not needed in cloud deployment

- [ ] Test Locally
  - [ ] Verify app works with Supabase connection
  - [ ] Check all features (metrics, expenses, etc.)
  - [ ] Ensure data displays correctly

## Git Repository Setup

- [ ] Initialize git repository (if not already done)
  ```
  git init
  ```

- [ ] Add all files to repository
  ```
  git add .
  ```

- [ ] Create .gitignore file with:
  ```
  *.db
  *.sqlite
  __pycache__/
  .DS_Store
  ```

- [ ] Commit changes
  ```
  git commit -m "Prepare for Streamlit Cloud deployment"
  ```

- [ ] Create GitHub repository at github.com

- [ ] Link local repository to GitHub
  ```
  git remote add origin https://github.com/yourusername/your-repo-name.git
  ```

- [ ] Push code to GitHub
  ```
  git push -u origin main
  ```

## Streamlit Cloud Setup

- [ ] Go to https://streamlit.io/cloud
- [ ] Sign in with GitHub account
- [ ] Click "New app"
- [ ] Select your repository
- [ ] Select branch (usually "main")
- [ ] Set main file path to "app.py"

## Secrets Configuration

- [ ] In Streamlit Cloud app settings, add the following to secrets:
  ```toml
  [connections.supabase_sql]
  type = "postgresql"
  url = "postgresql://postgres:PASSWORD@db.PROJECTID.supabase.co:5432/postgres"
  
  [connections.supabase]
  project_url = "https://PROJECTID.supabase.co"
  api_key = "YOUR_SUPABASE_API_KEY"
  
  # Clover credentials
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

## Post-Deployment

- [ ] After deployment completes, test all functionality on Streamlit Cloud
- [ ] Check that the app can connect to Supabase
- [ ] Verify all data is displaying correctly
- [ ] Test adding expenses to ensure write operations work
- [ ] Ensure data syncing with Clover API works

## Troubleshooting

If you encounter issues:

1. Check Streamlit Cloud logs for errors
2. Verify secrets are configured correctly
3. Make sure Supabase database is accessible (not paused)
4. Check for any network restrictions or IP limiting on Supabase

## Resources

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-cloud)
- [Supabase Documentation](https://supabase.com/docs)
- [Detailed Connection Guide](README_SUPABASE.md) 