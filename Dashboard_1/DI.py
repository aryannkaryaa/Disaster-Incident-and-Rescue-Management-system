import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import base64
from io import BytesIO
from datetime import datetime, timedelta
# pyodbc is implicitly handled by st.connection("sql") for mssql

# --- Page Configuration ---
st.set_page_config(
    page_title="EOC Incident Dashboard - Bihar",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Function to load and encode image to base64 ---
def get_image_base64(path):
    try:
        # Use PIL.Image.open for broader image format support, then save to BytesIO as PNG
        img = Image.open(path)
        buffered = BytesIO()
        img.save(buffered, format="PNG") # Always save as PNG for consistency in data URI
        return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"
    except FileNotFoundError:
        st.warning(f"IMAGE FILE NOT FOUND AT: {path}")
        return None
    except Exception as e:
        st.error(f"Error encoding image {path}: {e}")
        return None

# --- Custom CSS ---
st.markdown("""
<style>
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    body, .stApp {
        font-family: "IBM Plex Sans", sans-serif !important;
        font-size: 0.95rem;
        background-color: #F4F4F4;
    }
    .main-header {
        font-size: 1.9em !important;
        padding-bottom: 0px !important;
        margin-bottom: 15px !important;
        color: #161616;
        font-family: "IBM Plex Sans", sans-serif;
        display: flex;
        align-items: center;
    }
    .logo-image {
        vertical-align: middle;
        margin-right: 15px;
        height: 50px;
    }
    h3 {
        font-size: 1.2em !important;
        margin-bottom: 10px !important;
        margin-top: 20px !important;
        font-weight: 600;
        color: #161616;
        border-bottom: 2px solid #0F62FE;
        padding-bottom: 5px;
    }
    .stTabs [data-baseweb="tab-panel"] h3 {
        margin-top: 10px !important;
    }
    h6 {
        font-size: 0.9em !important;
        color: #525252;
        text-align: center;
        font-weight: 600;
        margin-bottom: 8px;
        margin-top: 5px;
    }
    .stButton>button {
        border-radius: 4px;
        padding: 8px 15px;
        border: 1px solid #0F62FE;
        background-color: #FFFFFF;
        color: #0F62FE;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #0F62FE;
        color: #FFFFFF;
        border: 1px solid #0043CE;
    }
    .stButton>button:active {
        background-color: #0031A1 !important;
        color: #FFFFFF !important;
    }

    /* KPI Card Styling (for casualty types) */
    .casualty-kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-left: 4px solid #0F62FE;
        padding: 10px 15px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        text-align: center;
        animation: fadeIn 0.5s ease-out forwards;
        height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
    .casualty-kpi-card:hover {
        transform: scale(1.03);
        box-shadow: 0 5px 15px rgba(15, 98, 254, 0.3);
        cursor: pointer;
    }
    .casualty-kpi-card.death-total {
        border-left-color: #DA1E28;
    }
    .casualty-kpi-card.death-total .value {
        color: #DA1E28;
    }

    /* Styling for Plotly Gauge Chart Containers */
    .gauge-container {
        background-color: #FFFFFF;
        padding: 5px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        width: 100%;
    }
    .gauge-container:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 6px 12px rgba(15, 98, 254, 0.25);
        cursor: default;
    }
    .gauge-container .stPlotlyChart {
        padding: 0 !important;
        margin: 0 !important;
        width: 100%;
        display: flex;
        justify-content: center;
    }
    .gauge-value {
        font-size: 1.5em;
        font-weight: 700;
        color: #161616;
        margin-top: 10px;
        text-align: center;
        width: 100%;
    }

    /* Sidebar styling */
    .st-emotion-cache-1l269bu { /* This class targets the sidebar container. It might change in future Streamlit versions. */
        background-color: #FFFFFF;
        border-right: 1px solid #E0E0E0;
        box-shadow: 2px 0 5px rgba(0,0,0,0.05);
        padding-top: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .st-emotion-cache-1l269bu .stSelectbox, .st-emotion-cache-1l269bu .stDateInput {
        margin-bottom: 15px;
    }
    .sidebar-title {
        font-size: 1.3em;
        font-weight: 600;
        color: #0F62FE;
        margin-bottom: 20px;
        text-align: center;
    }
    /* Tab styling */
    button[data-baseweb="tab"] {
        font-size: 0.95em !important;
        padding: 10px 18px !important;
        font-family: "IBM Plex Sans", sans-serif !important;
        font-weight: 500 !important;
    }
    [data-baseweb="tab-list"] {
        background-color: #F4F4F4 !important;
        padding-bottom: 0px !important;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- Global Colors and Styles ---
PRIMARY_COLOR = "#0F62FE"
SECONDARY_COLOR = "#525252"
DEATH_COLOR = "#DA1E28"
INJURED_COLOR = "#FF8C00"
INCIDENT_COLOR = PRIMARY_COLOR
TEXT_COLOR = "#161616"
GRID_COLOR = "#E0E0E0"
AXIS_COLOR = "#C6C6C6"
PLOTLY_TEMPLATE = "plotly_white"
CHART_FONT = "IBM Plex Sans, sans-serif"

# --- Data Loading (UPDATED FOR st.connection TO MATCH YOUR WORKING DASHBOARD) ---
@st.cache_data(ttl=600) # Cache data for 10 minutes to reduce DB load
def load_data_from_db():
    try:
        # Use Streamlit's connection object with the name "sql_server"
        # This name MUST match [connections.sql_server] in your .streamlit/secrets.toml
        conn = st.connection("sql_server", type="sql")
        
        # SQL Query to fetch and join data based on your requirements
        # Ensure your table and column names here are exact as in your database
        sql_query = """
        SELECT
            CAST(HR.IncidentTable AS DATE) AS date,
            MD.DistrictName AS district,
            MB.BlockName AS block,
            H.Name AS incident_type,
            COALESCE(SUM(CASE WHEN HLR.HLCode = 1 THEN 1 ELSE 0 END), 0) AS deaths,
            COALESCE(SUM(CASE WHEN HLR.HLCode = 2 THEN 1 ELSE 0 END), 0) AS injured,
            CASE
                WHEN HR.IsFinal = 1 THEN 'Final'
                WHEN HR.IsFinal = 2 THEN 'Verified'
                ELSE 'Unknown'
            END AS entry_type
        FROM
            dbo.HazardReport AS HR
        LEFT JOIN
            dbo.Hazards AS H ON HR.HazardCode = H.ID
        LEFT JOIN
            dbo.mst_Districts AS MD ON HR.DistrictCode = MD.DistrictCode
        LEFT JOIN
            dbo.mst_Blocks AS MB ON HR.BlockCode = MB.BlockCode AND HR.DistrictCode = MB.DistrictCode
        LEFT JOIN
            dbo.HumanLossReport AS HLR ON HR.ID = HLR.HzdReptID
        GROUP BY
            CAST(HR.IncidentTable AS DATE),
            MD.DistrictName,
            MB.BlockName,
            H.Name,
            HR.IsFinal
        ORDER BY
            CAST(HR.IncidentTable AS DATE);
        """

        # Execute the query using the Streamlit connection object's query method
        df = conn.query(sql_query)
            
        # Post-processing to ensure data types and string formatting are consistent
        df['date'] = pd.to_datetime(df['date'])
        for col in ['district', 'block', 'incident_type', 'entry_type']:
            if col in df.columns and df[col].dtype == 'object': # Check if column exists and is object type
                df[col] = df[col].astype(str).str.strip().str.title()
        for col in ['deaths', 'injured']:
            if col in df.columns: # Check if column exists
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        return df

    except Exception as e:
        # A general error message for database connection issues, prompting the user
        # to check their secrets.toml and server accessibility.
        st.error(f"An error occurred while loading data: {e}. Please ensure:")
        st.error("- Your `.streamlit/secrets.toml` file is correctly configured.")
        st.error("- The database server is accessible from where this app is running.")
        st.error("- The `[connections.sql_server]` section in `secrets.toml` is correct.")
        st.error("- The 'ODBC Driver 17 for SQL Server' is installed on your system.")
        return pd.DataFrame()

# Call the updated data loading function
df_main = load_data_from_db()
if df_main.empty: st.stop() # Stop if data loading failed

# --- Dashboard Title ---
# Ensure 'bihar_sarkar_logo.png' is in the same directory as your script
logo_path = "bihar_sarkar_logo.png" 
base64_logo = get_image_base64(logo_path)
title_html_content = f'<img src="{base64_logo}" class="logo-image">' if base64_logo else ""
title_html_content += "Incident Dashboard"
st.markdown(f'<div class="main-header">{title_html_content}</div>', unsafe_allow_html=True)

# --- Filter Area (Moved to Sidebar) ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚙️ Incident Filters</div>', unsafe_allow_html=True)
    
    # Ensure min/max dates are derived from the newly loaded database data
    min_date_data = df_main['date'].min().date()
    max_date_data = df_main['date'].max().date()
    # Default start date for filter to show recent data (e.g., last 30 days)
    default_start_date_filter = max_date_data - timedelta(days=29) if (max_date_data - min_date_data).days > 29 else min_date_data
    
    date_range_tuple_filter = st.date_input(
        "Select Date Range",
        value=(default_start_date_filter, max_date_data),
        min_value=min_date_data,
        max_value=max_date_data,
        key="date_range_filter_sidebar"
    )
    
    if len(date_range_tuple_filter) == 2:
        start_date, end_date = pd.to_datetime(date_range_tuple_filter[0]), pd.to_datetime(date_range_tuple_filter[1])
    else:
        # Fallback if only one date is selected initially, or range is invalid
        start_date, end_date = pd.to_datetime(default_start_date_filter), pd.to_datetime(max_date_data)
        st.warning("Please select a valid date range (start and end date).")
    
    if start_date > end_date:
        st.error("Error: Start date cannot be after end date. Please adjust the date range.")
        st.stop()
    
    selected_district = st.selectbox(
        "Select District",
        ['All'] + sorted(list(df_main['district'].unique())), # Options are now names directly from DB
        key="district_filter_sidebar"
    )
    selected_entry_type = st.selectbox(
        "Select Entry Type",
        ['All'] + sorted(list(df_main['entry_type'].unique())), # Options are now 'Final', 'Verified', 'Unknown'
        key="entry_type_filter_sidebar"
    )
    selected_incident_type = st.selectbox(
        "Select Incident Type",
        ['All'] + sorted(list(df_main['incident_type'].unique())), # Options are now names directly from DB
        key="incident_type_filter_sidebar"
    )

# --- Filtering Data ---
df_filtered = df_main[(df_main['date'] >= start_date) & (df_main['date'] <= end_date)]
if selected_district != 'All': df_filtered = df_filtered[df_filtered['district'] == selected_district]
if selected_entry_type != 'All': df_filtered = df_filtered[df_filtered['entry_type'] == selected_entry_type]
if selected_incident_type != 'All': df_filtered = df_filtered[df_filtered['incident_type'] == selected_incident_type]

# --- Create Tabs ---
tab_overview = st.tabs(["📊 Dashboard Overview"])[0]

with tab_overview:
    st.markdown("### Overall Status")
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    total_incidents = len(df_filtered)
    total_deaths = df_filtered['deaths'].sum() if 'deaths' in df_filtered else 0
    total_injured = df_filtered['injured'].sum() if 'injured' in df_filtered else 0

    # Function to create a Plotly Gauge Figure
    def create_plotly_gauge_figure(value, title_text, color, max_value, chart_key):
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = value,
            number = {'font': {'size': 28, 'family': CHART_FONT, 'color': color}},
            title = {'text': title_text, 'font': {'size': 14, 'family': CHART_FONT, 'color': TEXT_COLOR}},
            gauge = {
                'axis': {'range': [None, max_value], 'tickwidth': 1, 'tickcolor': "darkgray"},
                'bar': {'color': color, 'thickness': 0.75},
                'bgcolor': "white",
                'borderwidth': 1,
                'bordercolor': "#E0E0E0",
                'steps': [
                    {'range': [0, max_value * 0.5], 'color': "#F0F0F0"},
                    {'range': [max_value * 0.5, max_value], 'color': "#E0E0E0"}
                ]
            }
        ))
        fig.update_layout(
            height=170,
            margin=dict(l=10, r=10, t=35, b=5),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_family=CHART_FONT,
            font_color=TEXT_COLOR
        )
        return fig

    # Dynamically set max values for gauges
    INCIDENTS_GAUGE_MAX = max(10, total_incidents + int(total_incidents*0.25)) if total_incidents > 0 else 10
    DEATHS_GAUGE_MAX = max(10, total_deaths + int(total_deaths*0.5) + 5) if total_deaths > 0 else 10
    INJURED_GAUGE_MAX = max(10, total_injured + int(total_injured*0.5) + 5) if total_injured > 0 else 10
    
    with kpi_col1:
        st.markdown('<div class="gauge-container">', unsafe_allow_html=True)
        fig_incidents = create_plotly_gauge_figure(total_incidents, "Incidents", INCIDENT_COLOR, INCIDENTS_GAUGE_MAX, "incidents_gauge")
        st.plotly_chart(fig_incidents, use_container_width=True, config={'displayModeBar': False}, key="incidents_chart_key")
        st.markdown(f'<div class="gauge-value">{total_incidents}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with kpi_col2:
        st.markdown('<div class="gauge-container">', unsafe_allow_html=True)
        fig_deaths = create_plotly_gauge_figure(total_deaths, "Deaths", DEATH_COLOR, DEATHS_GAUGE_MAX, "deaths_gauge")
        st.plotly_chart(fig_deaths, use_container_width=True, config={'displayModeBar': False}, key="deaths_chart_key")
        st.markdown(f'<div class="gauge-value">{total_deaths}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with kpi_col3:
        st.markdown('<div class="gauge-container">', unsafe_allow_html=True)
        fig_injured = create_plotly_gauge_figure(total_injured, "Injured", INJURED_COLOR, INJURED_GAUGE_MAX, "injured_gauge")
        st.plotly_chart(fig_injured, use_container_width=True, config={'displayModeBar': False}, key="injured_chart_key")
        st.markdown(f'<div class="gauge-value">{total_injured}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Casualties (Deaths) by Incident Type")
    if 'deaths' in df_filtered.columns and 'incident_type' in df_filtered.columns:
        deaths_by_type_cards_data = df_filtered[df_filtered['deaths'] > 0].groupby('incident_type')['deaths'].sum().sort_values(ascending=False)
        all_incident_types_for_casualty_display = sorted(list(df_main['incident_type'].unique())) # Use df_main to ensure all types are shown, even if 0 deaths

        casualty_cards_data_list = []
        for inc_type in all_incident_types_for_casualty_display:
            death_count = deaths_by_type_cards_data.get(inc_type, 0)
            casualty_cards_data_list.append({"title": inc_type, "value": death_count})
        
        casualty_cards_data_list.append({"title": "Total Deaths", "value": total_deaths, "is_total": True})
        
        cols_per_row_casualty = 4
        num_casualty_cards = len(casualty_cards_data_list)
        for i in range(0, num_casualty_cards, cols_per_row_casualty):
            cols = st.columns(cols_per_row_casualty)
            for j in range(cols_per_row_casualty):
                if i + j < num_casualty_cards:
                    card_data = casualty_cards_data_list[i+j]
                    card_class = "casualty-kpi-card"
                    value_color = TEXT_COLOR
                    if card_data.get("is_total", False):
                        card_class += " death-total"
                        value_color = DEATH_COLOR
                    with cols[j]:
                        st.markdown(f"""<div class="{card_class}"><div class="title">{card_data['title']}</div><div class="value" style="color:{value_color};">{card_data['value']:,}</div></div>""", unsafe_allow_html=True)
    else:
        st.info("Required columns for 'Casualties (Deaths) by Incident Type' (deaths, incident_type) are not available in the filtered data.")

    st.markdown("### Graphical Analysis")
    graph_col1, graph_col2 = st.columns(2)

    def style_plotly_chart(fig, chart_height=320, is_pie_or_donut=False, legend_orientation="h"):
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='#FFFFFF', # Set paper background for the chart area
            xaxis=dict(
                showgrid=False,
                linecolor=AXIS_COLOR,
                tickfont=dict(color=TEXT_COLOR, size=10),
                showline=True,
                zeroline=False
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=GRID_COLOR,
                linecolor=AXIS_COLOR,
                tickfont=dict(color=TEXT_COLOR, size=10),
                showline=False,
                zeroline=False,
                rangemode='tozero'
            ),
            hoverlabel=dict(bgcolor="#FFFFFF", font_size=11, font_family=CHART_FONT, bordercolor=AXIS_COLOR, font_color=TEXT_COLOR),
            legend=dict(orientation=legend_orientation, yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(family=CHART_FONT, color=TEXT_COLOR, size=10), bgcolor='rgba(0,0,0,0)'),
            margin=dict(l=40, r=20, t=35, b=40),
            title_text='', # Titles are handled by Streamlit markdown for better control
            title_font_family=CHART_FONT,
            title_font_color=TEXT_COLOR,
            font_color=TEXT_COLOR,
            font_family=CHART_FONT,
            height=chart_height
        )
        if not is_pie_or_donut: 
            fig.update_layout(hovermode='x unified')
            fig.update_xaxes(title_text=None)
            fig.update_yaxes(title_text=None)
        else: 
            fig.update_layout(hovermode='closest')
            fig.update_layout(
                xaxis=dict(visible=False, showgrid=False),
                yaxis=dict(visible=False, showgrid=False),
                margin=dict(l=10, r=10, t=30, b=10)
            )
        if fig.layout.title.text: # Center plotly title if it exists
            fig.update_layout(title_x=0.5)
        return fig

    with graph_col1:
        st.markdown("###### Deaths by Incident Type")
        try:
            if not df_filtered.empty and 'deaths' in df_filtered.columns and 'incident_type' in df_filtered.columns and df_filtered['deaths'].sum() > 0:
                sunburst_data_df = df_filtered[df_filtered['deaths'] > 0].groupby('incident_type', as_index=False)['deaths'].sum()
                sunburst_data_df = sunburst_data_df.sort_values(by='deaths', ascending=False)

                if not sunburst_data_df.empty:
                    fig_sunburst = px.sunburst(
                        sunburst_data_df,
                        path=[px.Constant("Total Deaths"), 'incident_type'],
                        values='deaths',
                        color='incident_type', # Color by incident type
                        color_discrete_sequence=px.colors.qualitative.Pastel,
                        custom_data=['deaths']
                    )
                    fig_sunburst.update_traces(
                        textinfo='label+percent root', # Show label and percentage of total deaths
                        hovertemplate='<b>%{label}</b><br>Deaths: %{customdata[0]:,}<br>(%{percentRoot:.1%})<extra></extra>',
                        insidetextorientation='radial',
                        leaf_opacity=0.9,
                        marker_line_width=0.5, marker_line_color='rgba(0,0,0,0.4)'
                    )
                    st.plotly_chart(style_plotly_chart(fig_sunburst, chart_height=340, is_pie_or_donut=True), use_container_width=True)
                else: st.caption("No death data by incident type to display for the selected filters.")
            elif not ('deaths' in df_filtered.columns and 'incident_type' in df_filtered.columns):
                st.caption("Required columns ('deaths', 'incident_type') missing for sunburst chart.")
            else: st.caption("No deaths recorded in the selected period to display by incident type.")
        except Exception as e:
            st.error(f"Could not render 'Deaths by Incident Type' chart: {e}")

    with graph_col2:
        st.markdown("###### Daily Death Report (Last 30 Days)")
        try:
            if not df_filtered.empty and 'deaths' in df_filtered.columns and 'date' in df_filtered.columns:
                daily_df = df_filtered.copy()

                current_end_date_for_daily = end_date
                last_30_days_start_date = current_end_date_for_daily - timedelta(days=29) # Inclusive of end_date, so 30 days total

                # Create a complete date range to fill missing days with zero
                all_dates_in_daily_range = pd.date_range(start=last_30_days_start_date, end=current_end_date_for_daily)
                
                if not all_dates_in_daily_range.empty:
                    daily_summary = daily_df.groupby(daily_df['date'].dt.date)['deaths'].sum().reindex(all_dates_in_daily_range.date, fill_value=0).reset_index()
                    
                    # Ensure column names are correct after reindex/reset_index
                    rename_cols = {'index': 'date'}
                    if 'deaths' not in daily_summary.columns and len(daily_summary.columns) > 1 and daily_summary.columns[1] not in ['date', 'index']:
                        rename_cols[daily_summary.columns[1]] = 'deaths'
                    daily_summary.rename(columns=rename_cols, inplace=True)
                    daily_summary['date'] = pd.to_datetime(daily_summary['date'])

                    if not daily_summary.empty and 'deaths' in daily_summary.columns:
                        fig_daily = px.line(daily_summary, x='date', y='deaths',
                                             labels={'date': '', 'deaths': 'Total Deaths'},
                                             color_discrete_sequence=[DEATH_COLOR],
                                             markers=True) # Add markers for individual days
                        fig_daily.update_traces(
                            hovertemplate='Date: %{x|%d %b %Y}<br>Deaths: %{y}<extra></extra>',
                            line=dict(width=2, shape='linear'), # Smooth line
                            marker=dict(size=5, symbol='circle')
                        )
                        fig_daily.update_xaxes(showticklabels=True, title_text=None, type='date', showgrid=False, tickformat='%d %b')
                        fig_daily.update_yaxes(showgrid=True, gridcolor=GRID_COLOR, zeroline=False, minallowed=0)
                        st.plotly_chart(style_plotly_chart(fig_daily, chart_height=340), use_container_width=True)
                    else: st.caption("No daily death data to summarize (or 'deaths' column missing after processing).")
                else: st.caption("Invalid date range for daily death report (e.g., max date older than 30 days prior to min date).")
            elif not ('deaths' in df_filtered.columns and 'date' in df_filtered.columns):
                st.caption("Required columns ('date', 'deaths') missing for daily death report.")
            else: st.caption("No data available in df_filtered to display day-wise report.")
        except Exception as e:
            st.error(f"Could not render 'Daily Death Report' chart: {e}")

    # --- Hierarchical Incident Breakdown (Treemap) ---
    st.markdown("### Hierarchical Incident Breakdown")
    if not df_filtered.empty and 'district' in df_filtered.columns and 'incident_type' in df_filtered.columns:
        df_treemap = df_filtered.groupby(['district', 'incident_type']).size().reset_index(name='incident_count')
        df_treemap = df_treemap[df_treemap['incident_count'] > 0] # Only show branches with incidents

        if not df_treemap.empty:
            try:
                fig_treemap = px.treemap(
                    df_treemap,
                    path=[px.Constant("All Incidents"), 'district', 'incident_type'],
                    values='incident_count',
                    color='district', # Color treemap squares by district
                    hover_name='incident_type',
                    custom_data=['district'],
                    color_discrete_sequence=px.colors.qualitative.Pastel1 # A nice palette
                )

                fig_treemap.update_traces(
                    textinfo="label+value+percent parent", # Show label, value, and percentage of parent
                    marker=dict(cornerradius=5), # Rounded corners for treemap cells
                    hovertemplate='<b>%{label}</b><br>District: %{customdata[0]}<br>Incidents: %{value}<br>Percentage of Parent: %{percentParent:.1%}<extra></extra>'
                )
                fig_treemap.data[0].textfont.size = 11 # Adjust font size within treemap cells

                fig_treemap.update_layout(
                    title_text='Incident Distribution: District & Type',
                    margin=dict(t=50, l=10, r=10, b=10)
                )

                st.plotly_chart(style_plotly_chart(fig_treemap, chart_height=450, is_pie_or_donut=True), use_container_width=True)

            except Exception as e:
                st.error(f"Could not render Treemap: {e}")
        else:
            st.info("No data available to display in the Treemap for the current filter selection.")
    else:
        st.info("Required columns ('district', 'incident_type') not available or no data in filtered set for Treemap.")

st.markdown("---")
st.caption(f"Data displayed for the period: {start_date.strftime('%d %b, %Y')} to {end_date.strftime('%d %b, %Y')}")
st.caption(f"Last data refresh from database: {df_main['date'].max().strftime('%d %b, %Y %H:%M') if not df_main.empty and 'date' in df_main else 'N/A'}")