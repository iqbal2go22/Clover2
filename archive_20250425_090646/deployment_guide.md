# Streamlit Cloud Deployment Guide

## Step 1: Push Your Code to GitHub

1. Create a GitHub repository (if you haven't already)
2. Initialize a git repository in your local project folder:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```
3. Connect to your GitHub repository:
   ```bash
   git remote add origin https://github.com/yourusername/your-repo-name.git
   git push -u origin main
   ```

## Step 2: Prepare Your Repository Files

Make sure your repository includes:

- `app.py` - Your Streamlit application
- `cloud_db_utils.py` - The database utilities for Supabase
- `requirements.txt` - List of required packages
- Other supporting Python modules

## Step 3: Set Up Streamlit Cloud

1. Go to https://streamlit.io/cloud and sign in with your GitHub account
2. Click "New app"
3. Select your repository, branch (main), and main file path (`app.py`)
4. Click "Advanced Settings" and go to the "Secrets" section

## Step 4: Configure Secrets

In the Secrets section of Streamlit Cloud, paste the contents of your `.streamlit/secrets.toml` file:

```toml
[supabase]
url = "postgresql://postgres.yegrbbtxlsfbrlyavmbg:721AFFTNZmnQ3An7@yegrbbtxlsfbrlyavmbg.supabase.co:6543/postgres"

[clover]
merchant_id = "YOUR_MERCHANT_ID"
api_key = "YOUR_API_KEY"
access_token = "YOUR_ACCESS_TOKEN"
```

Be sure to replace the Clover credentials with your actual API keys.

## Step 5: Deploy Your App

Click "Deploy" and wait for the deployment process to complete. This may take a few minutes as Streamlit Cloud installs the dependencies and starts your application.

## Step 6: Migrate Your Data

The first time you run your app on Streamlit Cloud, it will automatically create the necessary tables in your Supabase database.

However, you'll need to migrate your existing data from SQLite to Supabase. You have two options:

### Option A: Deploy with Empty Database

Start fresh with an empty database. Your app will rebuild the data over time as it syncs with Clover.

### Option B: Manually Run Migration on Streamlit Cloud

1. Add a migration page to your app (with password protection)
2. Trigger the migration from the app's interface when deployed

## Step 7: Check Database Connection

Once deployed, your app should automatically connect to Supabase using the connection pooling URL.

If you encounter any issues:
1. Check the Streamlit Cloud logs
2. Verify your database credentials are correct in the Streamlit Secrets
3. Ensure Supabase is properly configured to accept connections from Streamlit Cloud

## Important Notes

- **Data Persistence**: Unlike SQLite, your Supabase database will persist data between app restarts
- **Connection Pooling**: We're using connection pooling which is optimized for serverless deployments
- **Scaling**: If your app experiences heavy traffic, you may need to upgrade your Supabase plan
- **Backup**: Regularly backup your Supabase database using their export functionality

## Troubleshooting

- If you encounter "connection refused" errors, check if your IP is allowed in Supabase settings
- If you face timeout issues, the connection pooling might be at capacity; consider upgrading your plan
- For "authentication failed" errors, double-check your database credentials 