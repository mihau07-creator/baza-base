import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Order, Item
from datetime import datetime
import plotly.express as px

# Constants
DB_URL = "sqlite:///./sales.db"

# Setup Database Connection
@st.cache_resource
def get_engine():
    return create_engine(DB_URL, connect_args={"check_same_thread": False})

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Helper functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@st.cache_data
def load_data():
    """Load all sales data into a dataframe"""
    with next(get_db()) as db:
        # We need to join Order and Item to get full details similar to previous view
        # SQLAlchemy Query to properly join and select fields
        query = db.query(
            Order.id.label('order_id'),
            Order.date,
            Order.source,
            Order.client_name.label('client_login'),
            Order.total.label('amount_total'),
            Order.currency,
            Order.email,
            Order.phone,
            Order.nip,
            Order.company,
            Order.invoice_number,
            Order.receipt_number,
            Item.name.label('product_name'),
            Item.quantity,
            Item.price.label('item_price')
        ).join(Item, Order.id == Item.order_id)
        
        # Use pandas read_sql with the statement
        df = pd.read_sql(query.statement, query.session.bind)
    return df

# Page Config
st.set_page_config(
    page_title="Sales Archive",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #0e1117;
    }
    .metric-label {
        font-size: 14px;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# Main Application
def main():
    st.title("📦 Archiwum Sprzedaży")

    # Load Data
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Błąd ładowania bazy danych: {e}")
        st.code(str(e)) # Show error details for debugging
        return

    # convert dates
    if not df.empty and 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    # Sidebar - Filters
    st.sidebar.header("Filtry")
    
    # 1. Date Range
    if not df.empty:
        # Handle cases where date might be null
        valid_dates = df['date'].dropna()
        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            
            date_range = st.sidebar.date_input(
                "Zakres dat",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            start_date, end_date = date_range if len(date_range) == 2 else (min_date, max_date)
        else:
             start_date, end_date = datetime.now().date(), datetime.now().date()
    else:
        start_date, end_date = datetime.now().date(), datetime.now().date()

    # 2. Text Search
    search_query = st.sidebar.text_input("Szukaj (Klient, NIP, Produkt, Email)", "")

    # 3. Source Filter
    if not df.empty and 'source' in df.columns:
        sources = ["Wszystkie"] + sorted(df['source'].dropna().unique().tolist())
        selected_source = st.sidebar.selectbox("Źródło zamówienia", sources)
    else:
        selected_source = "Wszystkie"

    # Filter Logic
    filtered_df = df.copy()

    # Apply Date Filter
    if not filtered_df.empty and 'date' in filtered_df.columns:
        mask = (filtered_df['date'].dt.date >= start_date) & (filtered_df['date'].dt.date <= end_date)
        filtered_df = filtered_df.loc[mask]

    # Apply Source Filter
    if selected_source != "Wszystkie":
        filtered_df = filtered_df[filtered_df['source'] == selected_source]

    # Apply Text Search
    if search_query:
        query = search_query.lower()
        cols_to_search = ['client_login', 'email', 'company', 'nip', 'phone', 'product_name', 'order_id']
        search_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
        
        for col in cols_to_search:
            if col in filtered_df.columns:
                search_mask |= filtered_df[col].astype(str).str.lower().str.contains(query, na=False)
        
        filtered_df = filtered_df[search_mask]

    # --- Dashboard View ---
    
    # KPIs
    col1, col2, col3 = st.columns(3)
    
    # Calculate unique orders for revenue (each row is an item, so summing amount_total directly would duplicate order totals)
    # We should take unique orders
    if not filtered_df.empty:
        unique_orders = filtered_df.drop_duplicates(subset=['order_id'])
        total_revenue = unique_orders['amount_total'].sum()
        total_orders = len(unique_orders)
        avg_order = total_revenue / total_orders if total_orders > 0 else 0
    else:
        total_revenue = 0
        total_orders = 0
        avg_order = 0
    
    col1.metric("Całkowita Sprzedaż", f"{total_revenue:,.2f} PLN")
    col2.metric("Liczba Zamówień", f"{total_orders}")
    col3.metric("Średnia Wartość", f"{avg_order:,.2f} PLN")

    st.markdown("---")

    # Tabs for different views
    tab1, tab2 = st.tabs(["📋 Lista Zamówień", "📊 Statystyki"])

    with tab1:
        if not filtered_df.empty:
            # Select columns to display
            display_cols = [
                'order_id', 'date', 'source', 'client_login', 
                'amount_total', 'currency', 'product_name', 'quantity'
            ]
            
            # Map columns to nicer names
            column_config = {
                'order_id': 'ID Zamówienia',
                'date': 'Data',
                'source': 'Źródło',
                'client_login': 'Klient',
                'amount_total': st.column_config.NumberColumn('Kwota', format="%.2f PLN"),
                'currency': 'Waluta',
                'product_name': 'Produkt',
                'quantity': 'Ilość'
            }
            
            # Additional logic to handle potential missing columns
            actual_cols = [c for c in display_cols if c in filtered_df.columns]

            st.dataframe(
                filtered_df[actual_cols].sort_values(by='date', ascending=False),
                column_config=column_config,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Brak wyników dla podanych filtrów.")

    with tab2:
        if not filtered_df.empty:
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.subheader("Sprzedaż w czasie")
                # Use unique orders for sales over time
                unique_orders_time = filtered_df.drop_duplicates(subset=['order_id'])
                sales_over_time = unique_orders_time.groupby(unique_orders_time['date'].dt.date)['amount_total'].sum().reset_index()
                sales_over_time.columns = ['Data', 'Sprzedaż']
                fig_time = px.line(sales_over_time, x='Data', y='Sprzedaż', markers=True)
                st.plotly_chart(fig_time, use_container_width=True)

            with col_chart2:
                st.subheader("Top 10 Produktów")
                # Group by product
                top_products = filtered_df.groupby('product_name')['quantity'].sum().reset_index().sort_values('quantity', ascending=False).head(10)
                fig_prod = px.bar(top_products, x='quantity', y='product_name', orientation='h', title="Najczęściej kupowane")
                st.plotly_chart(fig_prod, use_container_width=True)
                
            col_chart3, col_chart4 = st.columns(2)
            
            with col_chart3:
                st.subheader("Źródła zamówień")
                unique_orders_source = filtered_df.drop_duplicates(subset=['order_id'])
                source_counts = unique_orders_source['source'].value_counts().reset_index()
                source_counts.columns = ['Źródło', 'Liczba']
                fig_source = px.pie(source_counts, values='Liczba', names='Źródło', hole=0.4)
                st.plotly_chart(fig_source, use_container_width=True)
            
        else:
            st.info("Brak danych do wyświetlenia statystyk.")

if __name__ == "__main__":
    main()
