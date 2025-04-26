import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import requests
import json
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Clover Executive Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title and description
st.title("📊 Clover Executive Dashboard")
st.write("Cloud version with Supabase database")

# Use cloud database utilities (REST API based)
import cloud_db_utils as db_utils

# Session state management
if "current_store" not in st.session_state:
    st.session_state.current_store = None
if "date_range" not in st.session_state:
    st.session_state.date_range = "Last 7 Days"
if "show_expense_form" not in st.session_state:
    st.session_state.show_expense_form = False
if "edit_expense_id" not in st.session_state:
    st.session_state.edit_expense_id = None

# Date range selection
def get_date_range(range_name):
    today = datetime.now().replace(hour=23, minute=59, second=59)
    
    if range_name == "Today":
        start_date = today.replace(hour=0, minute=0, second=0)
        end_date = today
    elif range_name == "Yesterday":
        yesterday = today - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59)
    elif range_name == "Last 7 Days":
        start_date = (today - timedelta(days=6)).replace(hour=0, minute=0, second=0)
        end_date = today
    elif range_name == "Last 30 Days":
        start_date = (today - timedelta(days=29)).replace(hour=0, minute=0, second=0)
        end_date = today
    elif range_name == "This Month":
        start_date = today.replace(day=1, hour=0, minute=0, second=0)
        end_date = today
    elif range_name == "Last Month":
        last_month = today.replace(day=1) - timedelta(days=1)
        start_date = last_month.replace(day=1, hour=0, minute=0, second=0)
        end_date = today.replace(day=1) - timedelta(seconds=1)
    elif range_name == "This Year":
        start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0)
        end_date = today
    else:  # All Time
        start_date = datetime(2020, 1, 1)  # Far in the past
        end_date = today
        
    return start_date, end_date

# Helper function to format currency
def format_currency(value):
    return f"${value:,.2f}"

# Function to open expense form
def open_expense_form(store_id=None, expense_id=None):
    st.session_state.current_store = store_id
    st.session_state.show_expense_form = True
    st.session_state.edit_expense_id = expense_id

# Function to close expense form
def close_expense_form():
    st.session_state.show_expense_form = False
    st.session_state.edit_expense_id = None

# MAIN APP LAYOUT

# Sidebar
with st.sidebar:
    st.header("Settings")
    
    # Get all stores
    try:
        stores_df = db_utils.get_all_stores()
        
        # If no stores in database, check if we have store configs in secrets
        if stores_df.empty and hasattr(st, 'secrets'):
            store_records = []
            
            for key in st.secrets:
                if key.startswith('store_') or 'store' in key:
                    store_config = st.secrets[key]
                    if isinstance(store_config, dict) and 'merchant_id' in store_config and 'name' in store_config:
                        store_records.append({
                            'merchant_id': store_config['merchant_id'],
                            'name': store_config['name']
                        })
            
            if store_records:
                stores_df = pd.DataFrame(store_records)
                st.info("Loaded store configurations from secrets (not yet in database)")
    except Exception as e:
        st.error(f"Error loading stores: {str(e)}")
        stores_df = pd.DataFrame()
    
    if not stores_df.empty:
        # Store selection
        store_options = stores_df['name'].tolist()
        selected_store_name = st.selectbox("Select Store", options=store_options)
        
        # Get the selected store's data
        selected_store = stores_df[stores_df['name'] == selected_store_name].iloc[0]
        store_id = selected_store['merchant_id']
        
        # Date range selection
        date_ranges = ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "This Month", "Last Month", "This Year", "All Time"]
        selected_range = st.selectbox("Date Range", options=date_ranges, index=date_ranges.index(st.session_state.date_range))
        st.session_state.date_range = selected_range
        
        # Force sync option
        if st.button("Force Full Resync", type="primary"):
            st.info("Starting full data resync... This may take a minute.")
            
            # Code to perform full resync
            try:
                start_date = datetime(2024, 1, 1)  # Start from Jan 1, 2024
                end_date = datetime.now()
                
                # Add a spinner to show progress
                with st.spinner("Syncing data from Clover API..."):
                    # Call the sync function
                    sync_result = db_utils.sync_clover_data(store_id, start_date, end_date)
                    
                if sync_result["success"]:
                    st.success(f"✅ {sync_result['message']}")
                    
                    # Add more detailed results if available
                    if "results" in sync_result:
                        with st.expander("Sync Details"):
                            st.write(f"Total stores processed: {sync_result['results']['total_stores']}")
                            st.write(f"Successful stores: {sync_result['results']['successful_stores']}")
                            st.write(f"Failed stores: {sync_result['results']['failed_stores']}")
                            st.write(f"Total payments synced: {sync_result['results']['total_payments']}")
                            st.write(f"Total order items synced: {sync_result['results']['total_order_items']}")
                else:
                    st.error(f"❌ {sync_result['message']}")
            except Exception as e:
                st.error(f"❌ Error during sync: {str(e)}")
                st.write("Check connection to Supabase and Clover API credentials")
    else:
        st.warning("No stores found in database. Please set up your stores in the Streamlit secrets.")
        store_id = None

# MAIN CONTENT
if 'store_id' in locals() and store_id:
    # Get date range based on selection
    start_date, end_date = get_date_range(st.session_state.date_range)
    
    # Create two columns for the header section
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header(f"{selected_store_name} Dashboard")
        st.write(f"Data for: {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}")
    
    with col2:
        last_sync = db_utils.get_last_sync()
        if last_sync:
            sync_time = datetime.fromisoformat(last_sync['sync_time']) if isinstance(last_sync['sync_time'], str) else last_sync['sync_time']
            st.write(f"Last synced: {sync_time.strftime('%b %d, %Y %I:%M %p')}")
    
    # Load data for the selected store and date range
    try:
        payments_df = db_utils.get_payments_by_merchant(store_id, start_date, end_date)
        
        if not payments_df.empty:
            # Calculate metrics
            order_count = len(payments_df)
            total_sales = payments_df['amount'].sum() / 100  # Convert cents to dollars
            avg_order_value = total_sales / order_count if order_count > 0 else 0
            
            # METRICS SECTION
            st.subheader("Key Metrics")
            
            # Create metric cards
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                st.metric("Total Sales", format_currency(total_sales))
            
            with metric_col2:
                st.metric("Order Count", f"{order_count}")
            
            with metric_col3:
                st.metric("Average Order Value", format_currency(avg_order_value))
                
            # SALES OVER TIME SECTION
            st.subheader("Sales Over Time")
            
            # Prepare data for time-based analysis
            payments_df['created_at'] = pd.to_datetime(payments_df['created_at'])
            
            # Determine appropriate time grouping based on date range
            days_diff = (end_date - start_date).days
            
            if days_diff <= 1:  # Today or Yesterday
                # Group by hour
                payments_df['time_period'] = payments_df['created_at'].dt.strftime('%I %p')  # Hour with AM/PM
                period_label = 'Hour'
            elif days_diff <= 31:  # Last 7/30 days or This/Last Month
                # Group by day
                payments_df['time_period'] = payments_df['created_at'].dt.strftime('%b %d')  # Jan 01 format
                period_label = 'Day'
            else:  # This Year or All Time
                # Group by month
                payments_df['time_period'] = payments_df['created_at'].dt.strftime('%b %Y')  # Jan 2023 format
                period_label = 'Month'
            
            # Create time-based aggregations
            sales_over_time = payments_df.groupby('time_period').agg(
                Total_Sales=('amount', lambda x: sum(x) / 100),
                Order_Count=('id', 'count')
            ).reset_index()
            
            # Create sales over time chart
            fig = go.Figure()
            
            # Add bar chart for sales
            fig.add_trace(go.Bar(
                x=sales_over_time['time_period'],
                y=sales_over_time['Total_Sales'],
                name='Sales',
                marker_color='#1E88E5'
            ))
            
            # Add line chart for order count
            fig.add_trace(go.Scatter(
                x=sales_over_time['time_period'],
                y=sales_over_time['Order_Count'],
                name='Orders',
                marker_color='#FFC107',
                mode='lines+markers',
                yaxis='y2'
            ))
            
            # Update layout for dual Y-axis
            fig.update_layout(
                title=f'Sales and Orders by {period_label}',
                xaxis=dict(title=period_label),
                yaxis=dict(title='Sales ($)', titlefont=dict(color='#1E88E5'), tickfont=dict(color='#1E88E5')),
                yaxis2=dict(title='Order Count', titlefont=dict(color='#FFC107'), tickfont=dict(color='#FFC107'),
                            overlaying='y', side='right'),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                height=400,
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # EXPENSE MANAGEMENT SECTION
            st.subheader("Expense Management")
            
            # Add expense button
            expense_col1, expense_col2 = st.columns([3, 1])
            
            with expense_col1:
                # Get expense data
                expenses_df = db_utils.get_expenses_by_store(store_id, start_date, end_date)
                
                if not expenses_df.empty:
                    # Calculate total expenses
                    total_expenses = expenses_df['amount'].sum()
                    st.metric("Total Expenses", format_currency(total_expenses))
                else:
                    st.metric("Total Expenses", "$0.00")
            
            with expense_col2:
                # Button to add a new expense
                st.button("📝 Add Expense", on_click=open_expense_form, args=(store_id, None))
            
            # Expense table
            if not expenses_df.empty:
                # Process expenses for display
                expenses_df['date'] = pd.to_datetime(expenses_df['date']).dt.strftime('%Y-%m-%d')
                expenses_df['amount'] = expenses_df['amount'].apply(lambda x: format_currency(x))
                
                # Create an HTML table with edit/delete buttons
                html_table = """
                <style>
                .expenses-container {
                    max-width: 750px;
                    margin: 0 auto;
                    background-color: #f9f9fb;
                    border-radius: 10px;
                    padding: 15px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .expense-table-container {
                    max-width: 750px;
                    overflow-x: auto;
                    margin-top: 10px;
                }
                .expense-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 0.9rem;
                }
                .expense-table th {
                    background-color: #f1f1f1;
                    padding: 10px 12px;
                    text-align: left;
                    font-weight: 600;
                    color: #333;
                    font-size: 0.85rem;
                }
                .expense-table td {
                    padding: 10px 12px;
                    border-bottom: 1px solid #eee;
                    font-size: 0.9rem;
                }
                .table-row:hover {
                    background-color: #f5f5f5;
                }
                .category-tag {
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 0.75rem;
                    background-color: #e8eaf6;
                    color: #3f51b5;
                    display: inline-block;
                }
                .actions {
                    display: flex;
                    gap: 6px;
                }
                .action-btn {
                    background: none;
                    border: none;
                    cursor: pointer;
                    padding: 4px;
                    border-radius: 4px;
                    min-width: 28px;
                    min-height: 28px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                }
                .action-btn:hover {
                    background-color: #f0f0f0;
                }
                .edit-btn {
                    color: #2196F3;
                }
                .delete-btn {
                    color: #F44336;
                }
                </style>
                
                <div class="expenses-container">
                <div class="expense-table-container">
                <table class="expense-table">
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
                """
                
                # Add rows for each expense
                for _, expense in expenses_df.iterrows():
                    html_table += f"""
                    <tr class="table-row">
                        <td>{expense['date']}</td>
                        <td>{expense['amount']}</td>
                        <td><span class="category-tag">{expense['category']}</span></td>
                        <td>{expense['description']}</td>
                        <td class="actions">
                            <button class="action-btn edit-btn" onclick="editExpense({expense['id']})">✏️</button>
                            <button class="action-btn delete-btn" onclick="deleteExpense({expense['id']})">🗑️</button>
                        </td>
                    </tr>
                    """
                
                html_table += """
                </tbody>
                </table>
                </div>
                </div>
                
                <script>
                function editExpense(id) {
                    // Use Streamlit's communication mechanism to send a message to Python
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: {'action': 'edit', 'id': id},
                        dataType: 'json'
                    }, '*');
                }
                
                function deleteExpense(id) {
                    if (confirm('Are you sure you want to delete this expense?')) {
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            value: {'action': 'delete', 'id': id},
                            dataType: 'json'
                        }, '*');
                    }
                }
                </script>
                """
                
                # Display the HTML table
                st.components.v1.html(html_table, height=400, scrolling=True)
                
                # Handle edit/delete actions with a hidden Streamlit component
                action_placeholder = st.empty()
                action_data = action_placeholder.text_input("Action", value="", key="expense_action", label_visibility="collapsed")
                
                if action_data:
                    try:
                        action = json.loads(action_data)
                        if action['action'] == 'edit':
                            # Open the expense form for editing
                            open_expense_form(store_id, action['id'])
                            # Clear the action
                            action_placeholder.text_input("Action", value="", key="expense_action_clear", label_visibility="collapsed")
                        elif action['action'] == 'delete':
                            # Delete the expense
                            success = db_utils.delete_expense(action['id'])
                            if success:
                                st.success("Expense deleted successfully!")
                                st.rerun()  # Reload the app to show updated data
                            else:
                                st.error("Failed to delete expense.")
                            # Clear the action
                            action_placeholder.text_input("Action", value="", key="expense_action_clear2", label_visibility="collapsed")
                    except Exception as e:
                        st.error(f"Error processing action: {str(e)}")
            else:
                st.info("No expenses recorded for the selected period.")
            
            # EXPENSE FORM
            if st.session_state.show_expense_form:
                st.divider()
                st.subheader("Expense Form")
                
                # Initialize values
                date_value = datetime.now()
                amount_value = ""
                category_value = ""
                description_value = ""
                
                # If editing, load the expense data
                if st.session_state.edit_expense_id is not None:
                    # Here you would fetch the expense data from the database
                    expense_data = expenses_df[expenses_df['id'] == st.session_state.edit_expense_id]
                    if not expense_data.empty:
                        expense = expense_data.iloc[0]
                        date_value = pd.to_datetime(expense['date'])
                        # Remove $ and commas from amount
                        amount_value = float(expense['amount'].replace('$', '').replace(',', ''))
                        category_value = expense['category']
                        description_value = expense['description']
                
                # Create a form for expense entry
                with st.form(key="expense_form"):
                    form_col1, form_col2 = st.columns(2)
                    
                    with form_col1:
                        date = st.date_input("Date", value=date_value)
                        amount = st.number_input("Amount ($)", value=amount_value, step=1.0, format="%.2f")
                    
                    with form_col2:
                        category_options = db_utils.get_expense_categories()
                        category = st.selectbox("Category", options=category_options, index=category_options.index(category_value) if category_value in category_options else 0)
                        description = st.text_area("Description", value=description_value)
                    
                    # Form actions
                    submit_col, cancel_col = st.columns([1, 3])
                    
                    with submit_col:
                        submit_button = st.form_submit_button("Save Expense")
                    
                    with cancel_col:
                        cancel_button = st.form_submit_button("Cancel")
                
                # Handle form submission
                if submit_button:
                    try:
                        if st.session_state.edit_expense_id is not None:
                            # Update existing expense
                            data = {
                                "date": date.strftime("%Y-%m-%d"),
                                "amount": float(amount),
                                "category": category,
                                "description": description
                            }
                            success = db_utils.update_expense(st.session_state.edit_expense_id, data)
                            message = "Expense updated successfully!" if success else "Failed to update expense."
                        else:
                            # Add new expense
                            success = db_utils.add_expense(store_id, date, amount, category, description)
                            message = "Expense added successfully!" if success else "Failed to add expense."
                        
                        if success:
                            st.success(message)
                            close_expense_form()
                            st.rerun()  # Reload the app to show updated data
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"Error saving expense: {str(e)}")
                
                if cancel_button:
                    close_expense_form()
                    st.rerun()
        else:
            st.warning("No data available for the selected date range.")
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.write("Please check that you have properly set up your Supabase connection and migrated your data.")
else:
    # Show helpful information if no stores are available
    st.info("👋 Welcome to the Clover Executive Dashboard!")
    st.markdown("""
    ### Getting Started:
    
    1. Make sure your Supabase database is set up correctly
    2. Add your store configurations in the Streamlit secrets
    3. Migrate your data from SQLite if you haven't already
    
    If you need help, refer to the README or deployment guide.
    """)

# Footer
st.markdown("---")
st.markdown("© 2024 Clover Executive Dashboard | Cloud Version") 