import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import base64
from io import BytesIO
from datetime import datetime, timedelta
import time
try:
    from streamlit_plotly_events import plotly_events
    PLOTLY_EVENTS_AVAILABLE = True
except ImportError:
    PLOTLY_EVENTS_AVAILABLE = False

st.set_page_config(
    page_title="EOC Incident Dashboard - Bihar",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(15px) scale(0.98); }
        100% { opacity: 1; transform: translateY(0) scale(1); }
    }
    body, .stApp {
        font-family: "IBM Plex Sans", sans-serif !important;
        font-size: 0.95rem;
        background-color: #F4F4F4;
    }

    .title-container {
        width: 100%; /* Take full width of its parent */
        text-align: center; /* Center the inline-block title element */
        margin-bottom: 25px !important;
        position: relative; /* For the HR line */
    }

    .main-header-content {
        font-size: 1.9em !important;
        padding: 10px 25px !important; /* Padding inside the box */
        color: #161616; /* Original text color */
        font-family: "IBM Plex Sans", sans-serif;

        background-color: #E6F0FF; /* Light blue background for the box */
        border: 1px solid #0F62FE; /* Blue border for the box */
        border-radius: 12px; /* Curved edges */
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); /* Subtle shadow for depth */
        display: inline-block;
        position: relative; /* Needed for pseudo-element positioning */
        padding-bottom: 15px !important; /* Original space for the underline below the text */
    }

    .main-header-content::after {
        content: '';
        position: absolute;
        left: 50%; /* Start from center */
        transform: translateX(-50%); /* Adjust to truly center the line */
        bottom: 5px; /* Original position under the text */
        width: 80%; /* Width of the underline relative to the content box */
        height: 3px; /* Thickness of the underline */
        background-color: #0F62FE; /* Original underline color (blue) */
        border-radius: 2px; /* Slightly rounded corners for the underline */
    }

    /* New HR style for the line below the dashboard title */
    .dashboard-divider {
        border: none;
        height: 2px; /* Increased thickness to 2px */
        background-color: #0F62FE; /* Blue color for the line */
        margin-top: 15px; /* Reduced space above the line */
        margin-bottom: 25px; /* Reduced space below the line */
        width: 100%; /* Made the line complete (100% width) */
        margin-left: auto;
        margin-right: auto;
        border-radius: 1px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
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
        margin-bottom: 5px; /* Slightly reduced margin */
        margin-top: 5px;  /* Slightly reduced margin */
    }
    .stButton>button {
        border-radius: 4px;
        padding: 8px 15px; /* Standard button padding */
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

    .gauge-overall-container {
        background-color: #FFFFFF;
        padding: 8px; /* Slightly reduced padding */
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 15px; /* Reduced space below this whole section */
        display: flex;
        align-items: stretch;
    }

    .gauge-container {
        background-color: #FFFFFF;
        padding: 3px; /* Slightly reduced padding */
        border-radius: 8px;
        box_shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 10px; /* Reduced margin */
        animation: fadeIn 0.8s ease-out forwards;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out, opacity 0.8s ease-out;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        width: 100%;
        box-sizing: border-box;
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
        height: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .gauge-value {
        font-size: 1.4em; /* Slightly smaller font for value */
        font-weight: 700;
        color: #161616;
        margin-top: 5px; /* Reduced margin */
        text-align: center;
        width: 100%;
    }

    .st-emotion-cache-1l269bu {
        background-color: #FFFFFF;
        border-right: 1px solid #E0E0E0;
        box-shadow: 2px 0 5px rgba(0,0,0,0.05);
        padding-top: 1.5rem; /* Reduced padding */
        padding-left: 0.8rem; /* Reduced padding */
        padding-right: 0.8rem; /* Reduced padding */
    }
    .st-emotion-cache-1l269bu .stSelectbox, .st-emotion-cache-1l269bu .stDateInput {
        margin-bottom: 10px; /* Reduced margin */
    }
    .sidebar-title {
        font-size: 1.2em; /* Slightly smaller sidebar title */
        font-weight: 600;
        color: #0F62FE;
        margin-bottom: 15px; /* Reduced margin */
        text-align: center;
    }
    button[data-baseweb="tab"] {
        font-size: 0.9em !important; /* Slightly smaller font for tabs */
        padding: 8px 15px !important; /* Reduced padding for tabs */
        font-family: "IBM Plex Sans", sans-serif !important;
        font-weight: 500 !important;
    }
    [data-baseweb="tab-list"] {
        background-color: #F4F4F4 !important;
        padding-bottom: 0px !important;
        margin-bottom: 10px; /* Reduced margin */
    }

    .gauge-overall-container > div[data-testid="stHorizontalBlock"] {
        margin: 0 !important;
        padding: 0 !important;
        gap: 0px !important;
    }

    .gauge-overall-container div[data-testid="stColumn"] {
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        margin: 0 !important;
        border-right: 1px solid #E0E0E0;
        box-sizing: border-box;
    }
    .gauge-overall-container div[data-testid="stColumn"]:last-child {
        border-right: none;
    }

    .gauge-overall-container div[data-testid="stColumn"] > div {
        padding: 0 ;
        margin: 0 ;
    }

    /* Incident Death Summary specific styles - Compact layout */
    .incident-summary-wrapper-container div[data-testid="stHorizontalBlock"] {
        max-width: 350px;
        padding: 0px ;
        margin: 0px ;
        gap: 2px ; /* Very minimal gap between columns */
        width: 100% ;
    }

    .incident-summary-wrapper-container div[data-testid="stColumn"] {
        padding: 0px 1px ; /* Even more minimal padding between columns */
        margin: 0px ;
        display: flex;
        flex-direction: column; /* Stack cards vertically */
        align-items: center; /* Center cards within their column */
        justify-content: flex-start; /* Align cards to the top of the column */
        flex-grow: 1; /* Allow columns to grow, but content is limited */
    }

    .incident-death-card {
        background-color: #6777EF; /* Light blue (cyan) default color */
        color: white;
        padding: 1px 6px;
        border-radius: 5px;
        text-align: center;
        margin: 2px 1px;
        font-weight: 500;
        height: 22px;
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        align-items: center;
        border: 1px solid transparent; /* Transparent border by default */
        transition: background-color 0.3s ease, border-color 0.3s ease, box-shadow 0.15s, transform 0.12s;
        box-shadow: 0 1px 4px rgba(103,119,239,0.10);
        width: 100%;
        max-width: 140px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        box-sizing: border-box;
        font-size: 0.85em;
    }
    .incident-death-card:hover {
        background-color: #3B5BDB; /* Change to darker blue on hover */
        border: 1px solid #000000; /* Thinner black border on hover */
        box-shadow: 0 4px 12px rgba(0,0,0,0.25); /* Enhanced shadow on hover */
        transform: translateY(-2px) scale(1.03);
    }

    .incident-death-card.total-deaths-card {
        background-color: #FC403B; /* Light red default color */
        border: 1px solid transparent; /* Transparent border by default */
        transition: background-color 0.3s ease, border-color 0.3s ease, box-shadow 0.15s, transform 0.12s;
        box-shadow: 0 1px 4px rgba(252,84,75,0.10);
    }
    .incident-death-card.total-deaths-card:hover {
        background-color: #DA1E28; /* Darker red on hover */
        border: 1px solid #000000; /* Black border on hover */
        box-shadow: 0 4px 12px rgba(0,0,0,0.25); /* Enhanced shadow on hover */
        transform: translateY(-2px) scale(1.03);
    }

    .incident-death-card .incident-label {
        font-size: 0.8em;
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        flex-shrink: 1;
        margin-right: 3px;
        line-height: 1;
    }

    .incident-death-card .incident-value {
        font-size: 0.9em;
        font-weight: 700;
        flex-shrink: 0;
        white-space: nowrap;
        line-height: 1;
    }

    .st-emotion-cache-1f8u01d { /* This is the main container for the incident cards (the grey box) */
        background-color: #F8FAFF;
        border-radius: 12px;
        border: 1.5px solid #E0E6F0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        padding: 15px 8px 10px 8px;
        margin-bottom: 18px;
        display: flex;
        flex-wrap: wrap;
        justify-content: flex-start;
        align-items: flex-start;
        align-content: flex-start;
        gap: 0px;
        height: auto;
        max-height: 320px;
        overflow-y: auto;
        width: 320px; /* Reduced width for more compact container */
        max-width: 320px; /* Set maximum width */
        margin-left: 0;
        margin-right: 0;
    }
    .incident-summary-wrapper-container > div {
        padding: 0 !important;
    }
    .incident-summary-wrapper-container .st-emotion-cache-1f8u01d {
        width: 100%;
    }

    /* Target the actual container class from browser inspector */
    .st-emotion-cache-1d8vwwt.e1lln2w84 {
        background-color: #F8FAFF;
        border-radius: 12px;
        border: 1.5px solid #E0E6F0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        padding: 15px 8px 10px 8px;
        margin-bottom: 18px;
        display: flex;
        flex-wrap: wrap;
        justify-content: flex-start;
        align-items: flex-start;
        align-content: flex-start;
        gap: 0px;
        height: auto;
        max-height: 320px;
        overflow-y: auto;
        width: 320px !important; /* Reduced width for more compact container */
        max-width: 320px !important; /* Set maximum width */
        margin-left: 0;
        margin-right: 0;
    }

    /* Target the heading container class from browser inspector */
    .stElementContainer.element-container.st-emotion-cache-17lr0tt.e1lln2w81 {
        width: 320px !important; /* Match the incident boxes container width */
        max-width: 320px !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }

    /* Alternative selector for the heading container */
    div.st-emotion-cache-17lr0tt.e1lln2w81 {
        width: 320px !important;
        max-width: 320px !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }



    .stPlotlyChart {
        background-color: transparent !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
        margin-top: 0px !important;
        margin-bottom: 0px !important;
    }

    /* Align all three graph columns at the top for professional look */
    div[data-testid="column"] {
        vertical-align: top !important;
        align-items: flex-start !important;
    }

    /* Ensure consistent top alignment for all graph sections */
    div[data-testid="column"] > div {
        vertical-align: top !important;
        align-items: flex-start !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
    }

    /* Specific alignment for plotly charts */
    .js-plotly-plot {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* Align headings consistently across all columns */
    div[data-testid="column"] h6,
    div[data-testid="column"] h3 {
        margin-top: 0 !important;
        padding-top: 0 !important;
        margin-bottom: 10px !important;
    }

    /* Ensure all column content starts from the same vertical position */
    div[data-testid="column"] .stMarkdown,
    div[data-testid="column"] .stContainer {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

</style>
""", unsafe_allow_html=True)

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

# --- Data Loading ---
@st.cache_data(ttl=600) # Cache data for 10 minutes to reduce DB load
def load_data_from_db():
    try:
        conn = st.connection("sql_server", type="sql")

        sql_query = """
        SELECT
            CAST(HR.IncidentDate AS DATE) AS date,
            TRIM(MD.DistrictName) AS district,
            TRIM(MB.BlockName) AS block,
            H.Name AS incident_type,
            COALESCE(SUM(CASE WHEN HLR.HLCode = 2 THEN 1 ELSE 0 END), 0) AS deaths, -- Corrected: HLCode = 2 for Deaths
            COALESCE(SUM(CASE WHEN HLR.HLCode = 1 THEN 1 ELSE 0 END), 0) AS injured, -- Corrected: HLCode = 1 for Injured
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
        WHERE
            HR.IncidentDate >= '1970-01-01'
        GROUP BY
            CAST(HR.IncidentDate AS DATE),
            TRIM(MD.DistrictName),
            TRIM(MB.BlockName),
            H.Name,
            HR.IsFinal
        ORDER BY
            CAST(HR.IncidentDate AS DATE);
        """

        df = conn.query(sql_query)

        df['date'] = pd.to_datetime(df['date'])
        for col in ['district', 'block', 'incident_type', 'entry_type']:
            if col in df.columns and df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip().str.title()
        for col in ['deaths', 'injured']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        return df

    except Exception as e:
        st.error(f"An error occurred while loading data: {e}. Please ensure:")
        st.error("- Your `.streamlit/secrets.toml` file includes the correct server and database (e.g., `mssql+pyodbc://@YOUR_SERVER/YOUR_DATABASE?...`).")
        st.error("- The database server is accessible and the ODBC Driver 17 for SQL Server is installed.")
        return pd.DataFrame()

df_main = load_data_from_db()
if df_main.empty: st.stop()

st.markdown('<div class="title-container"><div class="main-header-content">Incident Dashboard</div></div>', unsafe_allow_html=True)
st.markdown('<hr class="dashboard-divider">', unsafe_allow_html=True) # Add the horizontal line below the main title

with st.sidebar:
    st.markdown('<div class="sidebar-title">Incident Filters</div>', unsafe_allow_html=True)

    min_date_data = df_main['date'].min().date()
    max_date_data = df_main['date'].max().date()

    default_start_date_filter = datetime(2021, 1, 1).date()
    default_end_date_filter = datetime(2025, 6, 30).date()

    if default_start_date_filter < min_date_data:
        default_start_date_filter = min_date_data
    if default_end_date_filter > max_date_data:
        default_end_date_filter = max_date_data

    date_range_tuple_filter = st.date_input(
        "Select Date Range",
        value=(default_start_date_filter, default_end_date_filter),
        min_value=min_date_data,
        max_value=max_date_data,
        key="date_range_filter_sidebar"
    )

    if len(date_range_tuple_filter) == 2:
        start_date, end_date = pd.to_datetime(date_range_tuple_filter[0]), pd.to_datetime(date_range_tuple_filter[1])
    else:
        start_date, end_date = pd.to_datetime(default_start_date_filter), pd.to_datetime(default_end_date_filter)
        st.warning("Please select a valid date range (start and end date).")

    if start_date > end_date:
        st.error("Error: Start date cannot be after end date. Please adjust the date range.")
        st.stop()

    selected_district = st.selectbox(
        "Select District",
        ['All'] + sorted(list(df_main['district'].unique())),
        key="district_filter_sidebar"
    )
    selected_entry_type = st.selectbox(
        "Select Entry Type",
        ['All'] + sorted(list(df_main['entry_type'].unique())),
        key="entry_type_filter_sidebar"
    )
    selected_incident_type = st.selectbox(
        "Select Incident Type",
        ['All'] + sorted(list(df_main['incident_type'].unique())),
        key="incident_type_filter_sidebar"
    )

df_filtered = df_main[(df_main['date'] >= start_date) & (df_main['date'] <= end_date)].copy()
if selected_district != 'All': df_filtered = df_filtered[df_filtered['district'] == selected_district]
if selected_entry_type != 'All': df_filtered = df_filtered[df_filtered['entry_type'] == selected_entry_type]
if selected_incident_type != 'All': df_filtered = df_filtered[df_filtered['incident_type'] == selected_incident_type]

# --- RENAME 'Strong Wind (Andhi Toofan)' to 'Strong Wind' ---
if 'incident_type' in df_filtered.columns:
    df_filtered['incident_type'] = df_filtered['incident_type'].replace('Strong Wind (Andhi Toofan)', 'Strong Wind')

total_incidents = len(df_filtered)
total_deaths = df_filtered['deaths'].sum() if 'deaths' in df_filtered else 0
total_injured = df_filtered['injured'].sum() if 'injured' in df_filtered else 0

def create_plotly_gauge_figure(value, title_text, color, max_value, animated=True):
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=value,
        number={
            'font': {'size': 24, 'family': CHART_FONT, 'color': color},
            'valueformat': ',d',
        },
        title={
            'text': f'<span style="font-size:14px; color:{color}; text-decoration:underline; text-decoration-color:{color}; text-decoration-thickness:1px;">{title_text}</span>',
            'font': {'size': 14, 'family': CHART_FONT, 'color': color}
        },
        gauge={
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
    if animated:
        frames = []
        steps = 20
        for i in range(steps + 1):
            frame_value = (value * i) / steps
            frames.append(go.Frame(
                data=[go.Indicator(
                    mode="gauge+number",
                    value=frame_value,
                    number={
                        'font': {'size': 24, 'family': CHART_FONT, 'color': color},
                        'valueformat': ',d',
                    },
                    title={
                        'text': f'<span style=\"font-size:14px; color:{color}; text-decoration:underline; text-decoration-color:{color}; text-decoration-thickness:1px;\">{title_text}</span>',
                        'font': {'size': 14, 'family': CHART_FONT, 'color': color}
                    },
                    gauge={
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
                )],
                name=str(i)
            ))
        fig.frames = frames
        fig.update_layout(
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'visible': True,
                'buttons': [{
                    'label': 'Play',
                    'method': 'animate',
                    'args': [None, {
                        'frame': {'duration': 50, 'redraw': True},
                        'fromcurrent': True,
                        'transition': {'duration': 0, 'easing': 'linear'}
                    }]
                }]
            }]
        )
    fig.update_layout(
        height=140,
        margin=dict(l=5, r=5, t=50, b=5),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family=CHART_FONT,
        font_color=TEXT_COLOR,
    )
    return fig

INCIDENTS_GAUGE_MAX = max(10, total_incidents + int(total_incidents*0.25)) if total_incidents > 0 else 10
DEATHS_GAUGE_MAX = max(10, total_deaths + int(total_deaths*0.5) + 5) if total_deaths > 0 else 10
INJURED_GAUGE_MAX = max(10, total_injured + int(total_injured*0.5) + 5) if total_injured > 0 else 10

gauge_key_base = f"{total_incidents}_{total_deaths}_{total_injured}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{selected_district}_{selected_entry_type}_{selected_incident_type}"

with st.markdown('<div class="gauge-overall-container">', unsafe_allow_html=True):
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

    with kpi_col1:
        fig_incidents = create_plotly_gauge_figure(total_incidents, "Incidents", INCIDENT_COLOR, INCIDENTS_GAUGE_MAX, animated=True)
        st.plotly_chart(fig_incidents, use_container_width=True, config={'displayModeBar': False}, key=f"incidents_chart_{gauge_key_base}")
    with kpi_col2:
        fig_deaths = create_plotly_gauge_figure(total_deaths, "Deaths", DEATH_COLOR, DEATHS_GAUGE_MAX, animated=True)
        st.plotly_chart(fig_deaths, use_container_width=True, config={'displayModeBar': False}, key=f"deaths_chart_{gauge_key_base}")
    with kpi_col3:
        fig_injured = create_plotly_gauge_figure(total_injured, "Injured", INJURED_COLOR, INJURED_GAUGE_MAX, animated=True)
        st.plotly_chart(fig_injured, use_container_width=True, config={'displayModeBar': False}, key=f"injured_chart_{gauge_key_base}")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<hr class="dashboard-divider">', unsafe_allow_html=True) # Horizontal line below gauge charts

def style_plotly_chart(fig, chart_height=280, is_pie_or_donut=False, legend_orientation="h"):
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
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
        margin=dict(l=20, r=10, t=30, b=30),
        title_text='',
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
            margin=dict(l=5, r=5, t=25, b=5)
        )
    if fig.layout.title.text:
        fig.update_layout(title_x=0.5)
    return fig

graph_col1, graph_col2, graph_col3 = st.columns([1.0, 0.8, 0.8])

with graph_col1:
    st.markdown("### Incident Death Summary")
    if not df_filtered.empty and 'deaths' in df_filtered.columns and 'incident_type' in df_filtered.columns:
        incident_deaths_summary = df_filtered[df_filtered['deaths'] > 0].groupby('incident_type')['deaths'].sum().sort_values(ascending=False).reset_index()

        st.markdown('<div class="incident-summary-wrapper-container">', unsafe_allow_html=True)
        incident_cards_container = st.container(border=True)
        st.markdown('</div>', unsafe_allow_html=True)


        with incident_cards_container:
            if not incident_deaths_summary.empty:

                all_death_summary_items = incident_deaths_summary.to_dict('records')
                all_death_summary_items.append({"incident_type": "Total Deaths", "deaths": total_deaths, "is_total": True})

                # Create two columns with minimal gap
                cols = st.columns([1, 1])

                # Distribute cards manually to left and right column
                left_column_items = [item for i, item in enumerate(all_death_summary_items) if i % 2 == 0]
                right_column_items = [item for i, item in enumerate(all_death_summary_items) if i % 2 != 0]

                with cols[0]:
                    for item in left_column_items:
                        card_class = "incident-death-card"
                        if item.get("is_total"):
                            card_class += " total-deaths-card"
                        st.markdown(f"""
                            <div class="{card_class}">
                                <span class="incident-label">{item["incident_type"]} :</span>
                                <span class="incident-value">{item["deaths"]:,}</span>
                            </div>
                        """, unsafe_allow_html=True)
                with cols[1]:
                    for item in right_column_items:
                        card_class = "incident-death-card"
                        if item.get("is_total"):
                            card_class += " total-deaths-card"
                        st.markdown(f"""
                            <div class="{card_class}">
                                <span class="incident-label">{item["incident_type"]} :</span>
                                <span class="incident-value">{item["deaths"]:,}</span>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                incident_cards_container.markdown('<p style="text-align: center; color: #525252; padding-top: 50px;">No deaths by incident type for selected filters.</p>', unsafe_allow_html=True)
    else:
        st.info("Required columns for 'Incident Death Summary' (deaths, incident_type) are not available or no data in filtered set.")

with graph_col2:
    st.markdown("###### Deaths by Incident Type")
    try:
        if not df_filtered.empty and 'deaths' in df_filtered.columns and 'incident_type' in df_filtered.columns and df_filtered['deaths'].sum() > 0:
            sunburst_data_df = df_filtered[df_filtered['deaths'] > 0].groupby('incident_type')['deaths'].sum().reset_index()
            sunburst_data_df = sunburst_data_df.sort_values(by='deaths', ascending=False)

            if not sunburst_data_df.empty:
                fig_sunburst = px.sunburst(
                    sunburst_data_df,
                    path=[px.Constant("Total Deaths"), 'incident_type'],
                    values='deaths',
                    color='incident_type',
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    custom_data=['deaths']
                )
                fig_sunburst.update_traces(
                    textinfo='label+percent root',
                    hovertemplate='<b>%{label}</b><br>Deaths: %{customdata[0]:,}<br>(%{percentRoot:.1%})<extra></extra>',
                    insidetextorientation='radial',
                    leaf_opacity=0.9,
                    marker_line_width=0.5, marker_line_color='rgba(0,0,0,0.4)'
                )
                st.plotly_chart(style_plotly_chart(fig_sunburst, chart_height=300, is_pie_or_donut=True), use_container_width=True, key=f"sunburst_chart_{total_deaths}_{start_date}_{end_date}")
            else: st.caption("No death data by incident type to display for the selected filters.")
        elif not ('deaths' in df_filtered.columns and 'incident_type' in df_filtered.columns):
            st.caption("Required columns ('deaths', 'incident_type') missing for sunburst chart.")
        else: st.caption("No deaths recorded in the selected period to display by incident type.")
    except Exception as e:
        st.error(f"Could not render 'Deaths by Incident Type' chart: {e}")

with graph_col3:
    st.markdown("###### Deaths in Last 7 Months")
    try:
        if not df_filtered.empty and 'deaths' in df_filtered.columns and 'date' in df_filtered.columns:
            last_7_months_end_date = end_date
            last_7_months_start_date = (last_7_months_end_date - pd.DateOffset(months=6)).replace(day=1)

            df_7_months = df_filtered[
                (df_filtered['date'] >= last_7_months_start_date) &
                (df_filtered['date'] <= last_7_months_end_date)
            ].copy()

            if not df_7_months.empty:
                df_7_months['year_month'] = df_7_months['date'].dt.to_period('M')
                monthly_summary_7_months = df_7_months.groupby('year_month')['deaths'].sum().reset_index()
                monthly_summary_7_months['month_label'] = monthly_summary_7_months['year_month'].dt.strftime('%b %Y')
                monthly_summary_7_months = monthly_summary_7_months.sort_values('year_month')

                if not monthly_summary_7_months.empty and monthly_summary_7_months['deaths'].sum() > 0:
                    fig_7_months = px.bar(
                        monthly_summary_7_months,
                        x='month_label',
                        y='deaths',
                        labels={'month_label': 'Month', 'deaths': 'Total Deaths'},
                        color_discrete_sequence=[DEATH_COLOR],
                        title=f"Total Deaths from {monthly_summary_7_months['month_label'].iloc[0]} to {monthly_summary_7_months['month_label'].iloc[-1]}" if not monthly_summary_7_months.empty else "Deaths in Last 7 Months",
                        text_auto=True
                    )

                    fig_7_months.update_traces(
                        hovertemplate='Month: %{x}<br>Deaths: %{y}<extra></extra>',
                        textposition='outside'
                    )

                    fig_7_months = style_plotly_chart(fig_7_months, chart_height=250)
                    st.plotly_chart(fig_7_months, use_container_width=True, config={'displayModeBar': False}, key=f"deaths_7_months_chart_{gauge_key_base}")
                else:
                    st.caption("No deaths recorded in the last 7 months for the selected filters.")
            else:
                st.caption("No data available for the last 7 months.")
        elif not ('deaths' in df_filtered.columns and 'date' in df_filtered.columns):
            st.caption("Required columns ('date', 'deaths') missing for last 7 months death report.")
        else:
            st.caption("No data available in df_filtered to display last 7 months report.")
    except Exception as e:
        st.error(f"Could not render 'Deaths in Last 7 Months' chart: {e}")

st.markdown("### District and Block wise Incident Distribution")
treemap_col = st.container()

with treemap_col:
    if not df_filtered.empty and 'district' in df_filtered.columns and 'incident_type' in df_filtered.columns:
        df_treemap = df_filtered.groupby(['district', 'incident_type']).size().reset_index(name='incident_count')
        df_treemap = df_treemap[df_treemap['incident_count'] > 0]

        if not df_treemap.empty:
            try:
                fig_treemap = px.treemap(
                    df_treemap,
                    path=[px.Constant("All Incidents"), 'district', 'incident_type'],
                    values='incident_count',
                    color='district',
                    hover_name='incident_type',
                    custom_data=['district'],
                    color_discrete_sequence=px.colors.qualitative.Pastel1
                )

                fig_treemap.update_traces(
                    textinfo="label+value+percent parent",
                    marker=dict(cornerradius=5),
                    hovertemplate='<b>%{label}</b><br>District: %{customdata[0]}<br>Incidents: %{value}<br>Percentage of Parent: %{percentParent:.1%}<extra></extra>'
                )
                fig_treemap.data[0].textfont.size = 10

                fig_treemap.update_layout(
                    title_text='Incident Distribution by District & Type',
                    margin=dict(t=40, l=5, r=5, b=5)
                )

                st.plotly_chart(style_plotly_chart(fig_treemap, chart_height=380, is_pie_or_donut=True), use_container_width=True, key=f"treemap_chart_{total_incidents}_{start_date}_{end_date}")

            except Exception as e:
                st.error(f"Could not render Treemap: {e}")
        else:
            st.info("No data available to display in the Treemap for the current filter selection.")
    else:
        st.info("Required columns ('district', 'incident_type') not available or no data in filtered set for Treemap.")

st.markdown("---")
st.caption(f"Data displayed for the period: {start_date.strftime('%d %b, %Y')} to {end_date.strftime('%d %b, %Y')}")
st.caption(f"Last data refresh from database: {df_main['date'].max().strftime('%d %b, %Y %H:%M') if not df_main.empty and 'date' in df_main else 'N/A'}")