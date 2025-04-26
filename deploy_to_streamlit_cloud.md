# Deploying to Streamlit Cloud

This guide will walk you through deploying your Clover Dashboard application to Streamlit Cloud.

## Prerequisites

1. A GitHub account
2. Your Clover Dashboard code in a GitHub repository
3. A Streamlit Cloud account (sign up at https://streamlit.io/cloud)
4. Your Supabase database is set up and contains your data

## Step 1: Prepare Your Code

1. Ensure your app is using the cloud-ready version:
   - Use `app_supabase.py` as your main app file
   - Rename it to `app.py` before deploying

2. Make sure your `requirements.txt` file includes all necessary dependencies:
   ```
   streamlit==1.32.0
   pandas==1.5.3
   requests==2.31.0
   toml==0.10.2
   python-dateutil==2.8.2
   plotly==5.18.0
   pydeck==0.8.0
   altair==5.2.0
   ```

3. Create a `.gitignore` file to exclude local files:
   ```
   .streamlit/secrets.toml
   *.db
   __pycache__/
   *.py[cod]
   *$py.class
   .env
   venv/
   ```

## Step 2: Push to GitHub

1. Initialize a Git repository (if not already done):
   ```bash
   git init
   ```

2. Add your files:
   ```bash
   git add .
   git add -f .streamlit/config.toml  # Add config but not secrets
   ```

3. Commit your changes:
   ```bash
   git commit -m "Prepare for Streamlit Cloud deployment"
   ```

4. Create a new repository on GitHub and follow the instructions to push your code:
   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
   git branch -M main
   git push -u origin main
   ```

## Step 3: Deploy on Streamlit Cloud

1. Log in to Streamlit Cloud: https://share.streamlit.io/

2. Click "New app"

3. Connect to your GitHub repository:
   - Select your repository
   - Select the branch (usually `main`)
   - Set the main file path to `app.py`

4. Configure advanced settings:
   - Set Python version to 3.10
   - You can leave other settings at their defaults

5. Click "Deploy!"

## Step 4: Configure Secrets in Streamlit Cloud

1. Once your app is deployed, click on the "Manage app" menu (three dots)

2. Select "Settings" → "Secrets"

3. Enter the same secrets as in your local `.streamlit/secrets.toml` file:
   ```toml
   [connections.supabase]
   project_url = "https://your-project-id.supabase.co"
   api_key = "your_anon_key"
   
   [connections.supabase_admin]
   project_url = "https://your-project-id.supabase.co"
   api_key = "your_service_role_key"
   
   [store_1]
   name = "Your Store Name"
   merchant_id = "YOUR_MERCHANT_ID"
   access_token = "YOUR_ACCESS_TOKEN"
   
   # Add other stores as needed
   ```

4. Click "Save"

5. Restart your app (three dots → "Reboot app")

## Step 5: Verify Your Deployment

1. Test your application features:
   - Verify database connection
   - Check that data is displayed correctly
   - Test syncing new data (if applicable)

2. Debug common issues:
   - Check app logs from the "Manage app" menu
   - Verify secrets are correctly configured
   - Ensure Supabase permissions allow access from Streamlit Cloud

## Troubleshooting

### App crashes on startup
- Check the logs for error messages
- Make sure all required packages are in `requirements.txt`
- Verify secrets are correctly configured

### Can't connect to Supabase
- Ensure your API key is correct
- Verify network permissions in Supabase (allow all origins)
- Check if your Supabase instance is online

### Data is not displaying
- Verify your tables exist in Supabase
- Check that data was properly migrated
- Test queries directly in Supabase SQL editor

## Need More Help?

- Streamlit Cloud docs: https://docs.streamlit.io/streamlit-cloud
- Supabase docs: https://supabase.com/docs 