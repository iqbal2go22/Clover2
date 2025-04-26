"""
Create a secrets.toml file for Streamlit Cloud deployment
"""
import os
import toml

# Make sure .streamlit directory exists
if not os.path.exists('.streamlit'):
    os.makedirs('.streamlit')

# Create secrets.toml with cloud database credentials
secrets = {
    'supabase': {
        'url': "postgresql://postgres.yegrbbtxlsfbrlyavmbg:721AFFTNZmnQ3An7@yegrbbtxlsfbrlyavmbg.supabase.co:6543/postgres"
    },
    'clover': {
        # Add your Clover API credentials here - these should be moved from your code to secrets
        'merchant_id': "",  # Your merchant ID
        'api_key': "",      # Your API key
        'access_token': ""  # Your access token
    }
}

# Write the secrets to .streamlit/secrets.toml
with open('.streamlit/secrets.toml', 'w') as f:
    toml.dump(secrets, f)

print("✅ Created .streamlit/secrets.toml")
print("Add your Clover API credentials to the file before deploying.")
print("For Streamlit Cloud deployment, you'll need to copy the contents of this file")
print("to the secrets management section in your Streamlit Cloud dashboard.") 