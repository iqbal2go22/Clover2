import streamlit as st
import pandas as pd
import datetime
import requests
import json
import plotly.express as px
import cloud_db_utils as db

# Page config
st.set_page_config(
    page_title="Clover Executive Dashboard",
    page_icon="📊",
    layout="wide",
)

# Initialize session state variables
if "current_store" not in st.session_state:
    st.session_state.current_store = None
if "date_range" not in st.session_state:
    st.session_state.date_range = "This Month"
if "show_expense_form" not in st.session_state:
    st.session_state.show_expense_form = False
if "editing_expense" not in st.session_state:
    st.session_state.editing_expense = None

def get_date_range(range_name):
    today = datetime.datetime.now().date()
    if range_name == "Today":
        start_date = today
        end_date = today
    elif range_name == "Yesterday":
        start_date = today - datetime.timedelta(days=1)
        end_date = today - datetime.timedelta(days=1)
    elif range_name == "Last 7 Days":
        start_date = today - datetime.timedelta(days=6)
        end_date = today
    elif range_name == "This Month":
        start_date = datetime.date(today.year, today.month, 1)
        end_date = today
    elif range_name == "Last Month":
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year if today.month > 1 else today.year - 1
        last_day = 31  # This is simplified and might not be accurate for all months
        if last_month in [4, 6, 9, 11]:
            last_day = 30
        elif last_month == 2:
            if (last_month_year % 4 == 0 and last_month_year % 100 != 0) or (last_month_year % 400 == 0):
                last_day = 29
            else:
                last_day = 28
        start_date = datetime.date(last_month_year, last_month, 1)
        end_date = datetime.date(last_month_year, last_month, last_day)
    elif range_name == "This Year":
        start_date = datetime.date(today.year, 1, 1)
        end_date = today
    else:
        start_date = today - datetime.timedelta(days=30)
        end_date = today
    
    return start_date, end_date

def format_currency(value):
    return f"${value:,.2f}"

# Helper functions for expense form
def open_expense_form():
    st.session_state.show_expense_form = True
    st.session_state.editing_expense = None

def close_expense_form():
    st.session_state.show_expense_form = False
    st.session_state.editing_expense = None

# Header and sidebar
with st.sidebar:
    st.title("Settings")
    
    # Check connection
    try:
        # Attempt to connect to Supabase
        db.check_connection()
        st.success("Connected to Supabase successfully!")
    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")
    
    # Load stores
    try:
        stores_data = db.get_stores()
        if not stores_data:
            st.warning("No stores found in the database. Please add stores first.")
        else:
            stores = {store['id']: store['name'] for store in stores_data}
            selected_store = st.selectbox(
                "Select Store",
                options=list(stores.keys()),
                format_func=lambda x: stores.get(x, "Unknown"),
                key="store_selector"
            )
            st.session_state.current_store = selected_store
    except Exception as e:
        st.error(f"Error loading stores: {str(e)}")
        stores = {}
    
    # Date range selection
    date_range_options = ["Today", "Yesterday", "Last 7 Days", "This Month", "Last Month", "This Year"]
    selected_range = st.selectbox("Select Date Range", options=date_range_options, index=3)
    st.session_state.date_range = selected_range
    
    # Force sync button
    if st.button("Force Full Data Resync"):
        try:
            db.add_sync_log_entry(force_sync=True)
            st.success("Sync flag set. Data will be refreshed on next sync.")
        except Exception as e:
            st.error(f"Error setting sync flag: {str(e)}")

# Main content
st.title("Clover Executive Dashboard")

if st.session_state.current_store:
    # Get date range
    start_date, end_date = get_date_range(st.session_state.date_range)
    
    # Format dates for display
    formatted_start = start_date.strftime("%b %d, %Y")
    formatted_end = end_date.strftime("%b %d, %Y")
    
    st.subheader(f"Sales Data: {formatted_start} to {formatted_end}")
    
    # Load payment data
    try:
        payments = db.get_payments_by_date_range(
            st.session_state.current_store, 
            start_date.isoformat(), 
            end_date.isoformat()
        )
        
        if not payments:
            st.info("No payment data found for the selected date range.")
        else:
            # Calculate metrics
            total_sales = sum(payment.get('amount', 0) for payment in payments)
            order_count = len(payments)
            avg_order = total_sales / order_count if order_count > 0 else 0
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Sales", format_currency(total_sales))
            with col2:
                st.metric("Order Count", f"{order_count:,}")
            with col3:
                st.metric("Average Order", format_currency(avg_order))
            
            # Prepare data for visualization
            df_payments = pd.DataFrame(payments)
            if not df_payments.empty:
                # Convert timestamp to datetime
                df_payments['date'] = pd.to_datetime(df_payments['timestamp']).dt.date
                
                # Group by date
                daily_sales = df_payments.groupby('date')['amount'].sum().reset_index()
                
                # Create chart
                fig = px.line(
                    daily_sales, 
                    x='date', 
                    y='amount',
                    title='Sales Over Time',
                    labels={'date': 'Date', 'amount': 'Sales Amount ($)'}
                )
                fig.update_layout(
                    xaxis_title='Date',
                    yaxis_title='Sales Amount ($)',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading payment data: {str(e)}")
    
    # Expense Management Section
    st.subheader("Expense Management")
    
    try:
        # Load expenses
        expenses = db.get_expenses_by_store_and_date_range(
            st.session_state.current_store,
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        # Calculate total expenses
        total_expenses = sum(expense.get('amount', 0) for expense in expenses)
        
        # Display total expenses
        st.metric("Total Expenses", format_currency(total_expenses))
        
        # Button to add new expense
        st.button("Add Expense", on_click=open_expense_form, key="add_expense_button")
        
        # Display expenses table if there are expenses
        if expenses:
            # Create a DataFrame for display
            df_expenses = pd.DataFrame(expenses)
            
            # Convert date string to datetime for proper sorting
            df_expenses['date'] = pd.to_datetime(df_expenses['date'])
            
            # Sort by date (newest first)
            df_expenses = df_expenses.sort_values('date', ascending=False)
            
            # Format for display
            display_df = df_expenses.copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            display_df['amount'] = display_df['amount'].apply(lambda x: format_currency(x))
            
            # Add Edit and Delete buttons using HTML
            # This requires JavaScript for interactivity
            html_table = """
            <style>
                .expenses-table { width: 100%; border-collapse: collapse; }
                .expenses-table th, .expenses-table td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                .expenses-table th { background-color: #f2f2f2; }
                .action-button { cursor: pointer; margin-right: 5px; padding: 3px 8px; border-radius: 3px; }
                .edit-button { background-color: #4CAF50; color: white; border: none; }
                .delete-button { background-color: #f44336; color: white; border: none; }
            </style>
            <table class="expenses-table">
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
            
            for _, row in display_df.iterrows():
                html_table += f"""
                <tr>
                    <td>{row['date']}</td>
                    <td>{row['amount']}</td>
                    <td>{row['category']}</td>
                    <td>{row['description']}</td>
                    <td>
                        <button 
                            class="action-button edit-button" 
                            onclick="editExpense({row['id']}, '{row['date']}', {df_expenses.loc[display_df.index[_],'amount']}, '{row['category']}', '{row['description']}')">
                            Edit
                        </button>
                        <button 
                            class="action-button delete-button" 
                            onclick="deleteExpense({row['id']})">
                            Delete
                        </button>
                    </td>
                </tr>
                """
            
            html_table += """
                </tbody>
            </table>
            <script>
                function editExpense(id, date, amount, category, description) {
                    const data = {
                        id: id,
                        date: date,
                        amount: amount,
                        category: category,
                        description: description
                    };
                    window.parent.postMessage({type: 'editExpense', data: data}, '*');
                }
                
                function deleteExpense(id) {
                    if (confirm('Are you sure you want to delete this expense?')) {
                        window.parent.postMessage({type: 'deleteExpense', id: id}, '*');
                    }
                }
            </script>
            """
            
            # Use components.html to render the HTML table
            st.components.v1.html(html_table, height=400)
            
            # JavaScript message handler
            st.markdown("""
            <script>
                window.addEventListener('message', function(event) {
                    if (event.data.type === 'editExpense') {
                        const data = event.data.data;
                        // Send to Streamlit via session state
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            value: {
                                action: 'edit',
                                expense: data
                            }
                        }, '*');
                    } else if (event.data.type === 'deleteExpense') {
                        // Send to Streamlit via session state
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            value: {
                                action: 'delete',
                                id: event.data.id
                            }
                        }, '*');
                    }
                });
            </script>
            """, unsafe_allow_html=True)
        else:
            st.info("No expenses found for the selected date range.")
    
    except Exception as e:
        st.error(f"Error loading expenses: {str(e)}")
    
    # Expense Form
    if st.session_state.show_expense_form:
        st.subheader("Add/Edit Expense")
        
        with st.form("expense_form"):
            # If editing, pre-fill the form
            if st.session_state.editing_expense:
                expense = st.session_state.editing_expense
                expense_date = expense.get('date', datetime.date.today().isoformat())
                expense_amount = expense.get('amount', 0.0)
                expense_category = expense.get('category', '')
                expense_description = expense.get('description', '')
            else:
                expense_date = datetime.date.today().isoformat()
                expense_amount = 0.0
                expense_category = ''
                expense_description = ''
            
            # Form fields
            date_input = st.date_input("Date", value=pd.to_datetime(expense_date).date())
            amount_input = st.number_input("Amount", value=float(expense_amount), step=0.01, format="%.2f")
            
            # Categories dropdown
            categories = ["Rent", "Utilities", "Payroll", "Inventory", "Marketing", "Equipment", "Maintenance", "Insurance", "Other"]
            category_input = st.selectbox("Category", options=categories, index=categories.index(expense_category) if expense_category in categories else 0)
            
            description_input = st.text_area("Description", value=expense_description)
            
            # Submit and Cancel buttons
            col1, col2 = st.columns(2)
            with col1:
                submit_button = st.form_submit_button("Submit")
            with col2:
                cancel_button = st.form_submit_button("Cancel", on_click=close_expense_form)
            
            if submit_button:
                try:
                    # Prepare expense data
                    expense_data = {
                        'store_id': st.session_state.current_store,
                        'date': date_input.isoformat(),
                        'amount': amount_input,
                        'category': category_input,
                        'description': description_input
                    }
                    
                    # Add or update expense
                    if st.session_state.editing_expense:
                        expense_data['id'] = st.session_state.editing_expense.get('id')
                        db.update_expense(expense_data)
                        st.success("Expense updated successfully!")
                    else:
                        db.add_expense(expense_data)
                        st.success("Expense added successfully!")
                    
                    # Close form
                    close_expense_form()
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error saving expense: {str(e)}")
else:
    st.warning("Please select a store from the sidebar to view dashboard.") 