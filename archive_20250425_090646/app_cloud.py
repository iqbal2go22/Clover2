import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
# Change SQLite imports to cloud database imports
import cloud_db_utils as db_utils  # Using cloud_db_utils instead of db_utils
# Remove SQLite-specific imports
import clover_data_fetcher

# Add the import for our new incremental sync
import incremental_sync

# Page configuration
st.set_page_config(
    page_title="Clover Executive Dashboard",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Add custom CSS for styling
st.markdown("""
<style>
    /* Modern Dashboard Styling */
    .main {
        background-color: #fafafa;
    }
    .block-container {
        max-width: 1080px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stColumn {
        padding-left: 5px !important;
        padding-right: 5px !important;
    }
    h1, h2, h3 {
        font-size: 1.8rem !important;
    }
    .metric-card {
        padding: 15px;
        border-radius: 8px;
        background-color: white;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .card-title {
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 5px;
        color: #555;
    }
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        line-height: 1.2;
    }
    .metric-icon {
        float: right;
        font-size: 28px;
        opacity: 0.7;
        margin-top: -32px;
    }
    .sales-value {
        color: #0284c7;
    }
    .profit-value {
        color: #059669;
    }
    .expense-value {
        color: #dc2626;
    }
    .tax-value {
        color: #7e22ce;
    }
    .count-value {
        color: #2563eb;
    }
    .debug-info {
        color: #666;
        font-size: 0.8rem;
        font-family: monospace;
        padding: 10px;
        background-color: #f0f0f0;
        border-radius: 5px;
        margin-top: 20px;
    }
    
    /* Store card metric colors */
    .sales-figure {
        color: #0284c7;
        font-weight: 600;
    }
    .expense-figure {
        color: #dc2626;
        font-weight: 600;
    }
    .profit-figure {
        color: #059669;
        font-weight: 600;
    }
    .orders-figure {
        color: #2563eb;
        font-weight: 600;
    }
    .avg-figure {
        color: #7e22ce;
        font-weight: 600;
    }
    
    /* Date Selector Styling */
    div[data-testid="stHorizontalBlock"] {
        background-color: white;
        padding: 5px 10px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    /* Button Styling */
    .stButton > button {
        background-color: transparent;
        color: #666;
        border: none;
        font-weight: 500;
        transition: all 0.2s;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        position: relative;
    }
    .stButton > button:hover {
        background-color: #f0f0f0;
        color: #2563eb;
    }
    
    /* Button active style classes */
    .button-active {
        color: #2563eb !important;
        font-weight: 600 !important;
    }
    .button-active::after {
        content: '';
        position: absolute;
        bottom: -5px;
        left: 0;
        width: 100%;
        height: 3px;
        background-color: #2563eb;
        border-radius: 2px;
    }
    
    /* Streamlit Overrides */
    .stMetric {
        background-color: white !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
        padding: 15px !important;
    }
    .stMetric:hover {
        box-shadow: 0 5px 15px rgba(0,0,0,0.1) !important;
    }
    
    /* Hide unnecessary elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Expense form styling */
    .form-container {
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        padding: 30px;
        margin: 20px auto;
        max-width: 600px;
    }
    
    .form-header {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 25px;
        color: #1e3a8a;
        text-align: center;
        border-bottom: 2px solid #f3f4f6;
        padding-bottom: 15px;
    }
    
    .form-label {
        font-weight: 600;
        color: #374151;
        margin-bottom: 10px;
        font-size: 1rem;
    }
    
    .form-help-text {
        color: #6b7280;
        font-size: 0.8rem;
        margin-top: 5px;
    }
    
    .expense-form-button {
        background-color: #2563eb !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 12px 20px !important;
        border-radius: 8px !important;
        transition: all 0.3s !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2) !important;
    }
    
    .expense-form-button:hover {
        background-color: #1d4ed8 !important;
        box-shadow: 0 6px 10px rgba(37, 99, 235, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    
    .cancel-button {
        background-color: #f3f4f6 !important;
        color: #4b5563 !important;
        font-weight: 600 !important;
        padding: 12px 20px !important;
        border-radius: 8px !important;
        transition: all 0.3s !important;
        border: none !important;
    }
    
    .cancel-button:hover {
        background-color: #e5e7eb !important;
        color: #1f2937 !important;
    }
    
    /* Store card action button styling */
    .add-expense-button {
        background-color: #2563eb !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 10px 15px !important;
        border-radius: 8px !important;
        transition: all 0.3s !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2) !important;
        width: 100% !important;
    }
    
    .add-expense-button:hover {
        background-color: #1d4ed8 !important;
        box-shadow: 0 6px 10px rgba(37, 99, 235, 0.3) !important;
        transform: translateY(-2px) !important;
    }

    /* Expense management page styling */
    .expense-wrapper {
        max-width: 750px;
        margin: 0 auto;
        background-color: #f9fafb;
        padding: 16px;
        border-radius: 8px;
    }
    
    .expense-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 14px;
        color: #374151;
    }
    
    .expense-container {
        background-color: white;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .total-row {
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 12px;
        margin-top: 8px;
        color: #1f2937;
    }
    
    .expense-divider {
        height: 1px;
        background-color: #f3f4f6;
        margin: 6px 0;
    }
    
    .expense-date {
        font-size: 0.8rem;
        color: #6b7280;
        margin-bottom: 4px;
    }
    
    .expense-amount {
        font-weight: 600;
        font-size: 0.95rem;
        color: #1f2937;
        margin-bottom: 4px;
    }
    
    .expense-description {
        font-size: 0.85rem;
        color: #4b5563;
        margin-bottom: 4px;
    }
    
    .category-tag {
        display: inline-block;
        font-size: 0.7rem;
        padding: 3px 8px;
        border-radius: 12px;
        background-color: #e5e7eb;
        color: #4b5563;
        margin-top: 4px;
    }
    
    /* Expenses table container */
    .expense-table-container {
        max-width: 750px;
        margin: 0 auto;
        background-color: white;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Expenses table */
    .expense-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
    }
    
    .expense-table th {
        text-align: left;
        padding: 8px 12px;
        color: #4b5563;
        font-size: 0.8rem;
        font-weight: 600;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .expense-table td {
        padding: 8px 12px;
        border-bottom: 1px solid #f3f4f6;
        font-size: 0.85rem;
    }

    /* Expense management custom styles */
    .main {
        padding: 1rem;
    }
    .expense-wrapper {
        max-width: 750px;
        margin: 0 auto;
        background-color: #fafafa;
        padding: 15px;
        border-radius: 15px;
    }
    .expense-header {
        font-weight: 600;
        color: #1E1E1E;
        margin-bottom: 0;
        font-size: 0.8rem;
        padding: 0;
    }
    .total-row {
        font-weight: 600;
        background-color: #f0f2f6;
        padding: 8px 12px;
        border-radius: 5px;
        margin-top: 8px;
        margin-bottom: 12px;
        font-size: 0.9rem;
    }
    .category-tag {
        padding: 1px 6px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 500;
        display: inline-block;
    }
    .rent-tag {
        background-color: #dbeafe;
        color: #1e40af;
    }
    .salary-tag {
        background-color: #f3e8ff;
        color: #7e22ce;
    }
    .purchases-tag {
        background-color: #dcfce7;
        color: #166534;
    }
    .other-tag {
        background-color: #f1f5f9;
        color: #475569;
    }
    .expense-form {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .expense-container {
        background-color: white;
        padding: 10px 15px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 8px;
    }
    .expense-divider {
        margin: 2px 0;
        border: none;
        border-top: 1px solid #eaecef;
    }
    .expense-date {
        color: #6b7280;
        font-size: 0.8rem;
        margin: 0;
        padding: 0;
    }
    .expense-amount {
        font-weight: 600;
        color: #1f2937;
        font-size: 0.8rem;
        margin: 0;
        padding: 0;
    }
    .expense-description {
        color: #4b5563;
        font-size: 0.8rem;
        margin: 0;
        padding: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .expense-table-container {
        max-width: 750px;
        margin: 0 auto;
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        padding: 10px 12px 6px;
    }
    .stButton>button {
        padding: 2px 6px !important;
        font-size: 0.8rem !important;
        height: auto !important;
        min-height: 0 !important;
    }
    /* Reduce the height of Streamlit elements */
    div[data-testid="stVerticalBlock"] > div {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    .stMarkdown p {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Row styling */
    .expense-divider {
        margin: 3px 0;
        opacity: 0.2;
    }
    .expense-date {
        color: #505050;
        font-size: 0.75rem;
    }
    .expense-amount {
        font-weight: 500;
        color: #202020;
        font-size: 0.75rem;
    }
    .expense-description {
        color: #505050;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
</style>
""", unsafe_allow_html=True)

# For cloud version, we don't need to check for SQLite database
# Instead check if we have a Supabase connection
# Updated to use modern Streamlit caching API
@st.cache_data
def check_supabase_connection():
    try:
        # Simply test if we can connect
        conn = db_utils.get_db_connection()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return False

# Rest of the app goes here - all the functionality from app.py
# but using cloud_db_utils instead

# Main app header
st.title("📊 Clover Executive Dashboard")
st.subheader("Cloud Version")

# Page layout and content would be identical to app.py but using cloud database

# Let the user know this is the cloud version
st.info("This version uses a Supabase cloud database and can be deployed to Streamlit Cloud.")

# Check if the connection is working
if check_supabase_connection():
    st.success("✅ Connected to Supabase database")
else:
    st.error("❌ Failed to connect to Supabase database")
    st.stop()

# Now let's port all the main functionality from app_deployed.py
# Since it's a longer file, start by implementing the basics here 