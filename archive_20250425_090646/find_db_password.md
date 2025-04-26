# How to Find Your Supabase Database Password

Follow these steps to locate your database password in Supabase:

1. **Log in to Supabase Dashboard** and open your project

2. **Navigate to Project Settings**
   - Click on the gear icon ⚙️ in the sidebar 
   - Select "Project Settings"

3. **Go to Database Settings**
   - In the Project Settings menu, select "Database"

4. **Find Connection Info**
   - Scroll down to the "Connection Info" or "Connection Pooling" section
   - Look for a field labeled "Password" or "Database Password"

   ![Database Password Location](https://supabase.com/_next/image?url=%2Fimages%2Freference%2Fself-hosting%2Fdashboard%2Fdb-password.jpg&w=1920&q=75)

5. **Copy the Password**
   - It may be hidden behind dots or a "Show" button
   - Copy this password and paste it in your `.streamlit/secrets.toml` file
   - Replace `YOUR_ACTUAL_DB_PASSWORD` with the password you copied

6. **Save Your Changes**
   - Make sure to save the `secrets.toml` file after updating the password

Now run the script again with:
```
py setup_supabase_direct.py
```

## Troubleshooting

If you can't find the password:
- Check the "Connection Pooling" section instead of "Connection Info"
- Try looking for "Connection String" which might contain the password in the format `postgresql://postgres:[PASSWORD]@...`
- If you recently created the project, make sure you saved the initial password shown during setup 