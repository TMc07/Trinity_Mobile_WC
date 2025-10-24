import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from io import StringIO

# Page config
st.set_page_config(page_title="Medical Records Dashboard", layout="wide", page_icon="🏥")

GITHUB_CSV_URL = "https://raw.githubusercontent.com/TMc07/Trinity_Mobile_WC/refs/heads/Trinity_demo/csv_folder/master_set.csv"

# Caching data load
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data_from_github(url):
    """Load CSV from GitHub raw URL"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        return df
    except Exception as e:
        st.error(f"Error loading data from GitHub: {str(e)}")
        return None

def categorize_billing_status(status):
    """Categorize billing status into main groups"""
    if pd.isna(status):
        return 'Not Billable'
    
    status = str(status).strip()
    
    if status == 'Billing Submitted':
        return 'Billed'
    elif status in ['Note Not Signed', 'Note Incomplete', 'Note Incomplete', 'No Note on File', 'Note Not Signed by NP']:
        return 'Pending'
    elif status in ['Amendment Required', 'Note Revisions Requested', 'Note Corrected but not Billed']:
        return 'Amendment Required'
    elif status in ['Not_Processed_Yet']:
        return 'Processing'
    else:
        return 'Not Billable'

def calculate_billed_amount(row):
    """Sum all numeric columns for billed amount"""
    numeric_cols = [
        'numeric_mkng945v', 'numeric_mkng1ekp', 'numeric_mkngdap1',
        'numeric_mkngbb06', 'numeric_mknghpcs', 'numeric_mkng9d2s',
        'numeric_mkng6bmr', 'numeric_mkqnk160', 'numeric_mkqn9t3r'
    ]
    
    total = 0
    for col in numeric_cols:
        if col in row.index:
            val = pd.to_numeric(row[col], errors='coerce')
            if not pd.isna(val):
                total += val
    return total

def get_treatment_type(row):
    """Identify treatment type from various columns"""
    treatments = []
    
    # Aerobella
    if 'color_mkng6xh7' in row.index and str(row['color_mkng6xh7']) == '97610':
        treatments.append('Aerobella')
    
    # Moleculight
    if 'color_mkngdesv' in row.index and pd.notna(row['color_mkngdesv']) and str(row['color_mkngdesv']).strip() != '':
        treatments.append('Moleculight')
    
    # Caregiver Education
    if 'color_mkngmf4f' in row.index:
        val = str(row['color_mkngmf4f']).strip()
        if pd.notna(row['color_mkngmf4f']) and val != '' and val != 'Not Billed':
            treatments.append('Caregiver Ed')
    
    # Skin Graft
    is_skin_graft = False
    if 'dropdown_mkngd0vh' in row.index and pd.notna(row['dropdown_mkngd0vh']):
        if 'graft' in str(row['dropdown_mkngd0vh']).lower():
            is_skin_graft = True
    if 'numeric_mkqn9t3r' in row.index:
        val = pd.to_numeric(row['numeric_mkqn9t3r'], errors='coerce')
        if pd.notna(val) and val > 0:
            is_skin_graft = True
    if is_skin_graft:
        treatments.append('Skin Graft')
    
    return ', '.join(treatments) if treatments else 'Other'

def process_data(df):
    """Process and enrich the dataframe"""
    # Add calculated columns
    df['billing_category'] = df['color_mkngbtn2'].apply(categorize_billing_status)
    df['billed_amount'] = df.apply(calculate_billed_amount, axis=1)
    df['treatment_type'] = df.apply(get_treatment_type, axis=1)
    
    # Rename key columns for easier access
    df['service_date'] = pd.to_datetime(df['date4_y'], errors='coerce')
    df['last_worked'] = pd.to_datetime(df['date_mkwhxsab'], errors='coerce')
    df['note_complete'] = pd.to_datetime(df['date_mkrwcv4w'], errors='coerce')
    df['provider'] = df['dropdown_mkngnttn']
    df['market'] = df['color_mkv5zem0']
    df['patient_name'] = df['Patient_Name']
    df['patient_status'] = df['dropdown_mkrxh1cs']
    
    return df

# Main app
def main():
    st.title("🏥 Medical Records Dashboard")
    
    # Sidebar for refresh and info
    with st.sidebar:
        st.header("📊 Dashboard Controls")
        
        # GitHub URL input (can be updated by user)
        github_url = st.text_input(
            "GitHub CSV URL",
            value=GITHUB_CSV_URL,
            help="Enter the raw GitHub URL for your master_set.csv file"
        )
        
        if st.button("🔄 Refresh Data", type="primary"):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        st.caption("Click 'Refresh Data' to load the latest data from GitHub")
    
    # Load data
    with st.spinner("Loading data from GitHub..."):
        df = load_data_from_github(github_url)
    
    if df is None:
        st.error("Failed to load data. Please check your GitHub URL.")
        st.info("Make sure you're using the 'raw' GitHub URL, not the regular page URL.")
        st.code("Example: https://raw.githubusercontent.com/username/repo/main/master_set.csv")
        return
    
    # Process data
    df = process_data(df)
    
    # Show last updated time
    st.success(f"✅ Data loaded successfully! Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption(f"Total records: {len(df)}")
    
    # Filters
    st.header("🔍 Filters")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    with col3:
        markets = ['All'] + sorted(df['market'].dropna().unique().tolist())
        selected_market = st.selectbox("Market", markets)
    
    with col4:
        providers = ['All'] + sorted(df['provider'].dropna().unique().tolist())
        selected_provider = st.selectbox("Provider", providers)
    
    # Apply filters
    filtered_df = df.copy()
    filtered_df = filtered_df[
        (filtered_df['service_date'] >= pd.to_datetime(start_date)) &
        (filtered_df['service_date'] <= pd.to_datetime(end_date))
    ]
    
    if selected_market != 'All':
        filtered_df = filtered_df[filtered_df['market'] == selected_market]
    
    if selected_provider != 'All':
        filtered_df = filtered_df[filtered_df['provider'] == selected_provider]
    
    # Key Metrics
    st.header("📈 Key Metrics")
    
    billed_df = filtered_df[filtered_df['billing_category'] == 'Billed']
    pending_df = filtered_df[filtered_df['billing_category'] == 'Pending']
    amendment_df = filtered_df[filtered_df['billing_category'] == 'Amendment Required']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "💰 BILLED",
            f"{len(billed_df)} visits",
            f"${billed_df['billed_amount'].sum():,.2f}"
        )
    
    with col2:
        st.metric(
            "⏳ PENDING",
            f"{len(pending_df)} visits",
            f"${pending_df['billed_amount'].sum():,.2f}"
        )
    
    with col3:
        st.metric(
            "⚠️ AMENDMENT REQUIRED",
            f"{len(amendment_df)} visits",
            f"${amendment_df['billed_amount'].sum():,.2f}"
        )
    
    # Market Breakdown
    st.header("🌎 Visits by Market")
    market_stats = filtered_df.groupby(['market', 'billing_category']).size().unstack(fill_value=0)
    
    if not market_stats.empty:
        st.dataframe(
            market_stats.style.background_gradient(cmap='RdYlGn', axis=1),
            use_container_width=True
        )
    
    # Provider Performance
    st.header("👨‍⚕️ Provider Status - NEEDS ATTENTION")
    
    provider_stats = filtered_df.groupby(['provider', 'billing_category']).size().unstack(fill_value=0)
    
    if 'Pending' in provider_stats.columns:
        provider_stats = provider_stats.sort_values('Pending', ascending=False)
        
        # Highlight providers with high pending
        def highlight_pending(row):
            if 'Pending' in row.index and row['Pending'] > 10:
                return ['background-color: #ffcccc'] * len(row)
            return [''] * len(row)
        
        styled_providers = provider_stats.style.apply(highlight_pending, axis=1)
        st.dataframe(styled_providers, use_container_width=True)
        
        # Alert for high pending
        high_pending = provider_stats[provider_stats.get('Pending', 0) > 10]
        if not high_pending.empty:
            st.error(f"🔴 {len(high_pending)} provider(s) have >10 pending visits - CALL THEM!")
            for provider in high_pending.index:
                st.warning(f"📞 {provider}: {high_pending.loc[provider, 'Pending']} pending visits")
    
    # Treatment Types
    st.header("💉 Treatment Types")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Regular Treatments")
        treatment_counts = {}
        for treatment in ['Aerobella', 'Moleculight', 'Caregiver Ed']:
            count = filtered_df['treatment_type'].str.contains(treatment, na=False).sum()
            treatment_counts[treatment] = count
        
        for treatment, count in treatment_counts.items():
            st.metric(treatment, count)
    
    with col2:
        st.subheader("Skin Grafts (Separate)")
        skin_graft_count = filtered_df['treatment_type'].str.contains('Skin Graft', na=False).sum()
        st.metric("Performed", skin_graft_count)
    
    # Detailed Records
    st.header("📋 Action Required Records")
    
    # Amendment Required
    with st.expander(f"🔴 AMENDMENT REQUIRED ({len(amendment_df)})", expanded=True):
        if not amendment_df.empty:
            display_cols = ['service_date', 'patient_name', 'provider', 'market', 'treatment_type', 'billed_amount']
            st.dataframe(
                amendment_df[display_cols].sort_values('service_date', ascending=False),
                use_container_width=True
            )
        else:
            st.success("No amendments required!")
    
    # Pending (grouped by provider)
    with st.expander(f"⏳ PENDING ({len(pending_df)})", expanded=True):
        if not pending_df.empty:
            for provider in pending_df['provider'].unique():
                provider_pending = pending_df[pending_df['provider'] == provider]
                
                alert = " - 🔴 CALL THEM" if len(provider_pending) > 10 else ""
                st.subheader(f"► {provider} ({len(provider_pending)} pending){alert}")
                
                display_cols = ['service_date', 'patient_name', 'market', 'treatment_type', 'billed_amount']
                st.dataframe(
                    provider_pending[display_cols].sort_values('service_date', ascending=False),
                    use_container_width=True
                )
        else:
            st.success("No pending visits!")
    
    # Billed (collapsed by default)
    with st.expander(f"✅ BILLED ({len(billed_df)})", expanded=False):
        if not billed_df.empty:
            display_cols = ['service_date', 'patient_name', 'provider', 'market', 'treatment_type', 'billed_amount']
            st.dataframe(
                billed_df[display_cols].sort_values('service_date', ascending=False),
                use_container_width=True
            )
    
    # Export functionality
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Export Filtered Data"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"medical_records_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()