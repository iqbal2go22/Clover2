import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import cloud_db_utils as db_utils  # Use cloud_db_utils instead of db_utils
import clover_data_fetcher
import time
import incremental_sync

# Page configuration
st.set_page_config(
    page_title="Clover Executive Dashboard",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Database initialization
db_utils.create_database()

# Ensure data is synced on startup for the last 3 days
today = datetime.now().date()
start_date = today - timedelta(days=7)  # Sync the last 7 days to ensure we have all recent data
stores = db_utils.get_all_stores()

# Only run sync if we have at least one store
if not stores.empty:
    with st.spinner("Syncing latest data, please wait..."):
        for _, store in stores.iterrows():
            incremental_sync.sync_store_data(store['id'], store['merchant_id'], store['access_token'], start_date)
    st.success("Data sync completed!")

# App title and description
st.title("📊 Multi-Store Dashboard")

# Get stores from the database
stores = db_utils.get_all_stores()

# Function to get metrics for a given date range
def get_metrics(start_date, end_date):
    # Format end_date to include time (11:59:59 PM)
    end_date_time = datetime.combine(end_date, datetime.max.time())
    
    # Query to get total orders and sales
    conn = db_utils.get_db_connection()
    try:
        query = """
        WITH OrderData AS (
            SELECT 
                store_id,
                order_id,
                SUM(price * quantity) AS order_total
            FROM order_items
            WHERE created_time >= :start_date AND created_time <= :end_date
            GROUP BY store_id, order_id
        )
        SELECT 
            COUNT(DISTINCT order_id) AS total_orders,
            SUM(order_total) AS total_sales
        FROM OrderData
        """
        
        df = pd.read_sql(query, conn, params={
            'start_date': start_date,
            'end_date': end_date_time
        })
        
        total_orders = int(df['total_orders'].iloc[0]) if not df.empty and df['total_orders'].iloc[0] else 0
        total_sales = float(df['total_sales'].iloc[0]) if not df.empty and df['total_sales'].iloc[0] else 0
        
        return total_orders, total_sales
    finally:
        conn.close()

# Date range selection
col1, col2 = st.columns(2)
with col1:
    view = st.radio("View", ["Daily", "Monthly", "Yearly", "Year-to-Date", "Custom"])

with col2:
    if view == "Daily":
        selected_date = st.date_input("Select Date", datetime.now().date())
        start_date = selected_date
        end_date = selected_date
    elif view == "Monthly":
        today = datetime.now().date()
        first_day = datetime(today.year, today.month, 1).date()
        selected_month = st.date_input("Select Month", today, min_value=first_day, max_value=today)
        start_date = datetime(selected_month.year, selected_month.month, 1).date()
        if selected_month.month == 12:
            end_date = datetime(selected_month.year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(selected_month.year, selected_month.month + 1, 1).date() - timedelta(days=1)
    elif view == "Yearly":
        selected_year = st.selectbox("Select Year", range(2020, datetime.now().year + 1), index=datetime.now().year - 2020)
        start_date = datetime(selected_year, 1, 1).date()
        end_date = datetime(selected_year, 12, 31).date()
    elif view == "Year-to-Date":
        today = datetime.now().date()
        start_date = datetime(today.year, 1, 1).date()
        end_date = today
    elif view == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now().date() - timedelta(days=7))
        with col2:
            end_date = st.date_input("End Date", datetime.now().date())

# Get metrics for the selected date range
total_orders, total_sales = get_metrics(start_date, end_date)

# Display metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Sales", f"${total_sales:,.2f}")
with col2:
    st.metric("Total Orders", f"{total_orders}")
with col3:
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0
    st.metric("Average Order Value", f"${avg_order_value:.2f}")

# Store comparison
st.header("Store Comparison")

# Format end_date to include time (11:59:59 PM)
end_date_time = datetime.combine(end_date, datetime.max.time())
# Format start date as midnight
start_date_time = datetime.combine(start_date, datetime.min.time())

# This query matches the approach used in the metrics function
conn = db_utils.get_db_connection()
try:
    query = """
    WITH OrderData AS (
        SELECT 
            oi.store_id,
            s.name AS store_name,
            oi.order_id,
            SUM(oi.price * oi.quantity) AS order_total
        FROM order_items oi
        JOIN stores s ON oi.store_id = s.id
        WHERE oi.created_time >= :start_date AND oi.created_time <= :end_date
        GROUP BY oi.store_id, s.name, oi.order_id
    )
    SELECT 
        store_id,
        store_name,
        COUNT(DISTINCT order_id) AS order_count,
        SUM(order_total) AS total_sales
    FROM OrderData
    GROUP BY store_id, store_name
    ORDER BY total_sales DESC
    """
    
    store_comparison = pd.read_sql(query, conn, params={
        'start_date': start_date_time,
        'end_date': end_date_time
    })
finally:
    conn.close()

if not store_comparison.empty:
    # Store comparison bar chart
    fig = px.bar(
        store_comparison, 
        x='store_name', 
        y='total_sales',
        text_auto='.2s',
        title=f"Sales by Store ({start_date} to {end_date})",
        labels={'store_name': 'Store', 'total_sales': 'Total Sales ($)'},
        color='store_name',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_traces(texttemplate='$%{text}', textposition='outside')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Orders by store
    fig2 = px.bar(
        store_comparison, 
        x='store_name', 
        y='order_count',
        text='order_count',
        title=f"Orders by Store ({start_date} to {end_date})",
        labels={'store_name': 'Store', 'order_count': 'Number of Orders'},
        color='store_name',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig2.update_traces(textposition='outside')
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)
    
    # Store comparison table
    store_comparison['total_sales'] = store_comparison['total_sales'].map('${:,.2f}'.format)
    store_comparison.rename(columns={
        'store_name': 'Store',
        'order_count': 'Orders',
        'total_sales': 'Sales'
    }, inplace=True)
    st.dataframe(store_comparison[['Store', 'Orders', 'Sales']], hide_index=True)
else:
    st.info("No data available for the selected date range.")

# Debug information and resync button
st.header("Debug Information")

# Create tabs for debug info and admin options
debug_tab, admin_tab = st.tabs(["Debug Info", "Admin Options"])

with debug_tab:
    # Display debug information
    st.markdown(f"""
    - **Date Range**: {start_date} to {end_date}
    - **Query Time Range**: {start_date_time} to {end_date_time}
    - **Total Sales**: ${total_sales:,.2f}
    - **Total Orders**: {total_orders}
    """)
    
    # Get the latest sync time from the database
    conn = db_utils.get_db_connection()
    try:
        query = "SELECT MAX(sync_date) as last_sync FROM sync_log"
        last_sync_df = pd.read_sql(query, conn)
        last_sync = last_sync_df['last_sync'].iloc[0] if not last_sync_df.empty and last_sync_df['last_sync'].iloc[0] else "Never"
        st.markdown(f"- **Last Data Sync**: {last_sync}")
    finally:
        conn.close()

with admin_tab:
    if st.button("Force Full Resync"):
        # Wipe existing data and reload all historical data
        if st.warning("This will delete all existing data and reload from the beginning. This may take several minutes. Continue?"):
            with st.spinner("Resetting database and reloading all historical data..."):
                # Clear orders for all stores
                for _, store in stores.iterrows():
                    db_utils.clear_orders_for_store(store['id'])
                
                # Load all historical data from Jan 1
                start_date = datetime(2024, 1, 1).date()
                for _, store in stores.iterrows():
                    incremental_sync.sync_store_data(store['id'], store['merchant_id'], store['access_token'], start_date)
                
                st.success("Full data resync completed!")
                st.rerun()

# Add expense management functionality
st.header("Expense Management")

# Get all stores again to ensure we have the latest data
stores_df = db_utils.get_all_stores()
stores_dict = {row['id']: row['name'] for idx, row in stores_df.iterrows()}

# Store selection for expenses
selected_store_id = st.selectbox("Select Store for Expenses", 
                                options=list(stores_dict.keys()),
                                format_func=lambda x: stores_dict.get(x, "Unknown Store"))

# Custom CSS for the expense management section
st.markdown("""
<style>
.expense-wrapper {
    max-width: 750px;
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 20px;
}
.expense-header {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 12px;
}
.total-row {
    font-size: 1rem;
    font-weight: 600;
    margin-top: 15px;
    margin-bottom: 15px;
}
.category-tag {
    display: inline-block;
    padding: 2px 8px;
    font-size: 0.75rem;
    border-radius: 12px;
    background: #e1e5f2;
    margin-right: 5px;
}
.expense-container {
    padding: 10px 0;
    margin: 5px 0;
    border-bottom: 1px solid #eaecef;
}
.expense-divider {
    margin: 5px 0;
    border-top: 1px solid #eaecef;
}
.expense-date {
    font-size: 0.85rem;
    color: #6c757d;
    padding-bottom: 4px;
}
.expense-amount {
    font-size: 0.9rem;
    font-weight: 600;
}
.expense-description {
    font-size: 0.85rem;
    color: #495057;
}
.expense-table-container {
    box-shadow: 0 0 5px rgba(0,0,0,0.05);
    border-radius: 5px;
    padding: 10px;
    margin-top: 15px;
    max-width: 750px;
}
.expenses-container {
    max-width: 750px;
}
.expense-table {
    width: 100%;
    border-collapse: collapse;
}
.expense-table th {
    background-color: #f8f9fa;
    padding: 6px;
    font-size: 0.75rem;
    text-align: left;
    color: #495057;
    font-weight: 600;
}
.expense-table td {
    padding: 5px;
    font-size: 0.9rem;
    border-bottom: 1px solid #eaecef;
}
.table-row:hover {
    background-color: #f8f9fa;
}
.action-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
    min-width: 28px;
    min-height: 28px;
    font-size: 0.8rem;
    border-radius: 4px;
}
.action-btn:hover {
    background-color: #f0f0f0;
}
.edit-btn {
    color: #2c7be5;
}
.delete-btn {
    color: #e63757;
}
</style>
""", unsafe_allow_html=True)

def get_store_expenses(store_id):
    """Get expenses for a specific store."""
    conn = db_utils.get_db_connection()
    try:
        query = """
        SELECT id, date, amount, category, description
        FROM expenses
        WHERE store_id = :store_id
        ORDER BY date DESC
        """
        expenses = pd.read_sql(query, conn, params={'store_id': store_id})
        return expenses
    finally:
        conn.close()

def delete_expense(expense_id):
    """Delete an expense from the database."""
    conn = db_utils.get_db_connection()
    try:
        conn.execute("DELETE FROM expenses WHERE id = :id", {'id': expense_id})
        conn.commit()
    finally:
        conn.close()

def expense_management_page(store_id, store_name):
    """Show the expense management page for a store."""
    
    # Get expenses for this store
    expenses = get_store_expenses(store_id)
    
    # Calculate total expenses
    total_expenses = expenses['amount'].sum() if not expenses.empty else 0
    
    # Display empty state if no expenses
    if expenses.empty:
        st.info(f"No expenses found for {store_name}.")
    else:
        # Display total expenses
        st.markdown(f"<div class='total-row'>Total Expenses: ${total_expenses:,.2f}</div>", unsafe_allow_html=True)
        
        # Display expenses in a table format
        st.markdown("<div class='expense-table-container'>", unsafe_allow_html=True)
        st.markdown(f"""
        <table class='expense-table'>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Amount</th>
                    <th>Category</th>
                    <th>Description</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
        """, unsafe_allow_html=True)
        
        for _, expense in expenses.iterrows():
            st.markdown(f"""
            <tr class='table-row'>
                <td>{expense['date']}</td>
                <td>${expense['amount']:,.2f}</td>
                <td><div class='category-tag'>{expense['category']}</div></td>
                <td>{expense['description']}</td>
                <td>
                    <button class='action-btn edit-btn' onclick="window.open('?edit_expense={expense['id']}', '_self')">✏️</button>
                    <button class='action-btn delete-btn' onclick="window.open('?delete_expense={expense['id']}', '_self')">🗑️</button>
                </td>
            </tr>
            """, unsafe_allow_html=True)
        
        st.markdown("</tbody></table>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Add expense button
    st.button(f"📝 Add Expense for {store_name}", on_click=open_expense_form, args=(store_id, None))
    
    # Expense deletion logic
    query_params = st.experimental_get_query_params()
    if 'delete_expense' in query_params:
        expense_id = query_params['delete_expense'][0]
        if st.warning(f"Are you sure you want to delete this expense?", button_text="Confirm Delete"):
            delete_expense(expense_id)
            st.success("Expense deleted successfully!")
            st.experimental_set_query_params()
            st.rerun()
    
    # Expense editing logic
    if 'edit_expense' in query_params:
        expense_id = query_params['edit_expense'][0]
        try:
            expense_id = int(expense_id)
            expense_row = expenses[expenses['id'] == expense_id].iloc[0]
            open_expense_form(store_id, expense_row)
        except:
            st.error("Invalid expense ID")
            st.experimental_set_query_params()

def open_expense_form(store_id, expense=None):
    """Open the expense form for adding or editing an expense."""
    
    st.markdown("""
    <style>
    .expense-form-container {
        max-width: 600px;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
    }
    .form-header {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 15px;
        color: #333;
    }
    .form-group {
        margin-bottom: 15px;
    }
    .form-label {
        font-weight: 500;
        display: block;
        margin-bottom: 5px;
        color: #495057;
    }
    .help-text {
        font-size: 0.8rem;
        color: #6c757d;
        margin-top: 4px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a container for the form
    st.markdown("<div class='expense-form-container'>", unsafe_allow_html=True)
    
    # Form header based on whether we're adding or editing
    if expense is None:
        st.markdown("<div class='form-header'>Add New Expense</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='form-header'>Edit Expense</div>", unsafe_allow_html=True)
    
    # Form fields
    with st.form(key='expense_form'):
        # Date field
        expense_date = st.date_input(
            "Date",
            value=expense['date'] if expense is not None else datetime.now().date()
        )
        
        # Amount field
        amount = st.number_input(
            "Amount ($)",
            min_value=0.01, 
            step=1.0,
            value=float(expense['amount']) if expense is not None else 0.0,
            format="%.2f"
        )
        
        # Category selection
        categories = db_utils.get_expense_categories()
        selected_category = st.selectbox(
            "Category",
            options=categories,
            index=categories.index(expense['category']) if expense is not None and expense['category'] in categories else 0
        )
        
        # Description field
        description = st.text_area(
            "Description",
            value=expense['description'] if expense is not None else "",
            max_chars=200,
            help="Briefly describe this expense"
        )
        
        # Submit button
        if expense is None:
            submit_label = "Add Expense"
        else:
            submit_label = "Update Expense"
        
        submit = st.form_submit_button(submit_label)
        
        if submit:
            # Validate inputs
            if amount <= 0:
                st.error("Amount must be greater than 0")
            elif description.strip() == "":
                st.error("Description is required")
            else:
                try:
                    if expense is None:
                        # Add new expense
                        db_utils.save_expense(
                            store_id,
                            amount,
                            selected_category,
                            description,
                            expense_date
                        )
                        st.success("Expense added successfully!")
                    else:
                        # Update existing expense
                        conn = db_utils.get_db_connection()
                        try:
                            query = """
                            UPDATE expenses
                            SET date = :date, amount = :amount, category = :category, description = :description
                            WHERE id = :id
                            """
                            conn.execute(query, {
                                'date': expense_date,
                                'amount': amount,
                                'category': selected_category,
                                'description': description,
                                'id': expense['id']
                            })
                            conn.commit()
                            st.success("Expense updated successfully!")
                        finally:
                            conn.close()
                    
                    # Clear query params and rerun the app
                    st.experimental_set_query_params()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving expense: {e}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Cancel button
    if st.button("Cancel"):
        st.experimental_set_query_params()
        st.rerun()

# Check if we're in the expense form mode
query_params = st.experimental_get_query_params()
if 'edit_expense' in query_params or 'delete_expense' in query_params:
    pass  # These are handled in the expense_management_page function
else:
    # Show the expense management page
    store_name = stores_dict.get(selected_store_id, "Unknown Store")
    expense_management_page(selected_store_id, store_name)

# Footer
st.markdown("---")
st.markdown("© 2024 Clover Executive Dashboard | Version 3.0")

# Force resync button
if st.button("Force Sync Data (Last 7 Days)"):
    today = datetime.now().date()
    start_date = today - timedelta(days=7)
    
    with st.spinner("Syncing data..."):
        for _, store in stores.iterrows():
            incremental_sync.sync_store_data(store['id'], store['merchant_id'], store['access_token'], start_date)
        
        st.success("Data sync completed!")
        st.rerun() 