import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import base64
from io import BytesIO
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Bihar Cold Wave Dashboard",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="auto", # Can be 'expanded' or 'collapsed'
)

# Function to load and encode image to base64
def get_image_base64(path):
    try:
        img = Image.open(path)
        buffered = BytesIO()
        img_format = path.split('.')[-1].upper()
        if img_format == "PNG":
            img.save(buffered, format="PNG")
            mime_type = "image/png"
        elif img_format == "WEBP":
            img.save(buffered, format="WEBP")
            mime_type = "image/webp"
        elif img_format in ["JPG", "JPEG"]:
            img.save(buffered, format="JPEG")
            mime_type = "image/jpeg"
        else:
            img.save(buffered, format="PNG")
            mime_type = "image/png"
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:{mime_type};base64,{img_str}"
    except FileNotFoundError:
        st.warning(f"Title image '{path}' not found. Displaying title without image.")
        return None
    except Exception as e:
        print(f"Error encoding image {path}: {e}")
        return None

# ======================================================================
# === DATABASE-CONNECTED DATA LOADING FUNCTION (SQL JOIN METHOD) ===
# ======================================================================
@st.cache_data(ttl=600) # Cache data for 10 minutes
def load_data():
    """
    Connects to the SQL Server DB and uses a single JOIN query to fetch all data.
    This requires a properly indexed/performant database.
    """
    try:
        # Step 1: Define the SQL query that joins the tables
        sql_query = """
        SELECT
            CD.RecordDate,
            CD.FYearID,
            D.DistrictName,
            B.BlockName,
            CD.AffectedPeople,
            CD.DeadPeople,
            CD.TotalNightShelter,
            PA.AllotedAmount,
            CD.AmountSpent,
            CD.BlanketDistribution,
            CD.TotalPeopleNightShelter,
            CD.WoodWt,
            CD.BonfirePlace
        FROM
            dbo.ColdWaveDetails AS CD
        LEFT JOIN
            dbo.ColdWavepaymentAllotment AS PA ON CD.ID = PA.ID
        LEFT JOIN
            dbo.mst_Districts AS D ON CD.DistrictCode = D.DistrictCode
        LEFT JOIN
            dbo.mst_Blocks AS B ON CD.BlockCode = B.BlockCode;
        """

        # Step 2: Connect to the database using Streamlit's connection manager
        conn = st.connection("sql_server", type="sql")
        df_loaded = conn.query(sql_query)
        
        # The success message has been commented out as requested.
        # st.success("Database connection successful and data loaded!")

        # Step 3: Define the mapping from database columns to dashboard column names
        column_mapping = {
            'RecordDate': 'date',
            'FYearID': 'financial_year',
            'DistrictName': 'district',
            'BlockName': 'block',
            'AffectedPeople': 'affected_population_lac',
            'DeadPeople': 'death',
            'TotalNightShelter': 'rain_basera',
            'AllotedAmount': 'alloted_amount_lac',
            'AmountSpent': 'expenditure_amount_lac',
            'BlanketDistribution': 'blanket_distributed',
            'TotalPeopleNightShelter': 'people_in_rain_basera',
            'WoodWt': 'wood_burn_kg',
            'BonfirePlace': 'bonfire_places'
        }
        
        # Step 4: Rename the columns
        df_loaded.rename(columns=column_mapping, inplace=True)

        # Step 5: As requested, create the 'affected_forms_filled' column and set it to 0
        df_loaded['affected_forms_filled'] = 0
        
        # --- The rest of your data processing ---
        df_loaded['date'] = pd.to_datetime(df_loaded['date'])
        numeric_cols = [
            'affected_forms_filled', 'affected_population_lac', 'death', 'rain_basera',
            'alloted_amount_lac', 'expenditure_amount_lac', 'blanket_distributed',
            'people_in_rain_basera', 'wood_burn_kg', 'bonfire_places'
        ]
        for col in numeric_cols:
            df_loaded[col] = pd.to_numeric(df_loaded[col], errors='coerce').fillna(0)
        
        df_loaded = df_loaded.fillna(0)
        
        if 'district' in df_loaded.columns:
            df_loaded['district'] = df_loaded['district'].astype(str).str.strip().str.title()
        if 'block' in df_loaded.columns:
            df_loaded['block'] = df_loaded['block'].astype(str).str.strip().str.title()
            
        return df_loaded

    except Exception as e:
        st.error(f"An error occurred while connecting to the database or loading data: {e}")
        st.error("Please check your database connection, secrets file, and SQL query.")
        return pd.DataFrame()

# The rest of your dashboard code
df_main = load_data()

# ======================= SIDEBAR FILTERS =======================
# All filter controls moved to the sidebar for a clean main layout
with st.sidebar:
    st.header("⚙️ Configure Filters")

    if 'district' in df_main.columns and not df_main['district'].empty:
        unique_districts = sorted(list(df_main['district'].unique()))
    else:
        unique_districts = []
    selected_district_filter = st.selectbox(
        "District", 
        options=unique_districts, 
        key="sb_dist_filter",
        placeholder="Select District",
        index=None
    )

    if 'block' in df_main.columns:
        if selected_district_filter:
            unique_blocks_for_district = df_main[df_main['district'] == selected_district_filter]['block'].unique()
            block_options = sorted(list(unique_blocks_for_district))
        else:
            block_options = sorted(list(df_main['block'].unique()))
    else:
        block_options = []
    selected_block_filter = st.selectbox(
        "Block", 
        options=block_options, 
        key="sb_block_filter", 
        placeholder="Select Block",
        index=None
    )

    if 'date' in df_main.columns and not df_main['date'].empty:
        min_date_data = df_main['date'].min().date()
        max_date_data = df_main['date'].max().date()
        default_start_date = pd.to_datetime('2022-12-14').date()
        default_end_date = pd.to_datetime('2025-01-03').date()

        date_input_value = st.date_input(
            "Select Date Range",
            value=[default_start_date, default_end_date],
            min_value=min_date_data,
            max_value=max_date_data,
            key="di_date"
        )
    else:
        date_input_value = st.date_input("Select Date Range:", [], key="di_date", help="No date data available")

    if len(date_input_value) == 2:
        date_range = date_input_value
    else:
        date_range = [pd.to_datetime('2022-12-14').date(), pd.to_datetime('2025-01-03').date()]


# Title icon and text separated for individual styling
icon = "❄️"
title_text = "Bihar Cold Wave Dashboard"

st.markdown(
    f"""
    <div class="title-container">
        <div class="title-box">
            <span class="title-icon">{icon}</span>
            <h1 class="title-text">{title_text}</h1>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# MODIFICATION: CSS updated for smooth sidebar transition
st.markdown("""
<style>
@keyframes fadeIn {
    0% { opacity: 0; transform: translateY(10px); }
    100% { opacity: 1; transform: translateY(0); }
}
section.main {
    transition: margin-left 0.3s ease-out !important;
}
body, .stApp { font-family: "IBM Plex Sans", sans-serif !important; font-size: 0.95rem; background-color: #F4F4F4; }
h1, h3, h6 { font-family: "IBM Plex Sans", sans-serif; }
h3 { font-size: 1.1em !important; margin-bottom: 5px !important; margin-top: 10px !important; font-weight: 600; color: #161616; }
h6 { font-size: 0.85em !important; color: #525252; text-align: left; font-weight: 600; margin-bottom: 5px; }
hr { margin: 15px 0px !important; }
.title-container {
    display: flex;
    justify-content: center;
    padding: 12px;
    margin-bottom: 10px;
}
.title-box {
    background-color: #E6F7FF;
    border: 1px solid #0F62FE;
    border-radius: 8px;
    padding: 8px 15px;
    display: inline-flex;
    align-items: center;
}
.title-icon {
    font-size: 1.5em;
    margin-right: 10px;
}
.title-text {
    font-size: 1.3em !important;
    font-weight: normal !important;
    text-decoration: underline;
    text-decoration-color: black;
    text-underline-offset: 4px;
    color: #161616;
}
.kpi-card-single {
    background-color: #FFFFFF; border: 1px solid #E8E8E8; border-left: 3px solid #0F62FE; padding: 6px 8px; border-radius: 3px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05); transition: all 0.35s ease-out; max-width: 95%; margin-left: auto; margin-right: auto;
    margin-bottom: 10px; opacity: 0; animation: fadeIn 0.5s ease-out forwards; position: relative;
    display: flex; flex-direction: column; height: 85px;
}
.kpi-card-single:hover {
    background-color: #FFFFFF; transform: translateY(-8px) scale(1.05); border-left: 5px solid #0043CE !important;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15), 0 0 20px 4px rgba(15, 98, 254, 0.45) !important;
}
.kpi-card-single .kpi-title {
    font-size: 0.55em; color: #393939; text-transform: uppercase; letter-spacing: 0.3px; font-weight: 600;
    margin-bottom: 4px; padding-bottom: 2px; border-bottom: 1px solid #F0F0F0; text-align: left;
    white-space: normal; height: 2.6em; line-height: 1.3;
}
.kpi-card-single .kpi-values-container { display: flex; justify-content: space-around; align-items: center; width: 100%; flex-grow: 1; margin-top: 2px; }
.kpi-card-single .kpi-value-block { text-align: center; padding: 0 2px; }
.kpi-card-single .kpi-sublabel { font-size: 0.55em; color: #787878; margin-bottom: 0px; display: block; font-weight: 400; }
.kpi-card-single .kpi-value-main { font-size: 1.05em; font-weight: 600; color: #0F62FE; line-height: 1.1; display: block; }
.kpi-card-merged {
    height: 170px;
}
.kpi-card-merged .merged-kpi-row {
    flex-grow: 1;
}
.kpi-card-merged .kpi-title {
    height: auto;
}
.merged-kpi-row .kpi-title {
    border-bottom: none; font-size: 0.65em; text-align: center; margin-bottom: 0; padding-bottom: 0; }
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div, 
div[data-testid="stDateInput"] > div > div {
    transition: all 0.2s ease-in-out;
    border: 1px solid transparent;
    border-radius: 4px;
}
div[data-testid="stSelectbox"]:hover div[data-baseweb="select"] > div, 
div[data-testid="stDateInput"]:hover > div > div {
    border: 1px solid #0F62FE;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

if df_main.empty:
    st.error("Dashboard cannot be displayed because no data could be loaded.")
    st.stop()

# Apply filters to the data
base_filtered_df = df_main.copy()
if 'date' in base_filtered_df.columns and date_range:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    if start_date > end_date:
        st.error("Error: Start date cannot be after end date."); st.stop()
    base_filtered_df = base_filtered_df[(base_filtered_df['date'] >= start_date) & (base_filtered_df['date'] <= end_date)]

# Update filter logic to check for None (placeholder) instead of "All"
today = end_date
kpi_ts_df = base_filtered_df.copy()
if selected_district_filter and 'district' in kpi_ts_df.columns:
    kpi_ts_df = kpi_ts_df[kpi_ts_df['district'] == selected_district_filter]
    if selected_block_filter and 'block' in kpi_ts_df.columns:
        kpi_ts_df = kpi_ts_df[kpi_ts_df['block'] == selected_block_filter]

if kpi_ts_df.empty:
    today_df = pd.DataFrame(columns=df_main.columns)
    tillnow_df_for_kpis = pd.DataFrame(columns=df_main.columns)
    ts_df = pd.DataFrame(columns=['date', 'affected_forms_filled', 'affected_population_lac', 'death', 'rain_basera', 'alloted_amount_lac', 'expenditure_amount_lac', 'blanket_distributed', 'people_in_rain_basera'])
    ts_df['date'] = pd.to_datetime(ts_df['date'])
else:
    today_df = kpi_ts_df[kpi_ts_df['date'] == today]
    tillnow_df_for_kpis = kpi_ts_df.copy()
    ts_df = kpi_ts_df.groupby('date', as_index=False).agg({'affected_forms_filled': 'sum', 'affected_population_lac': 'sum', 'death': 'sum', 'rain_basera': 'sum','alloted_amount_lac': 'sum', 'expenditure_amount_lac': 'sum', 'blanket_distributed': 'sum', 'people_in_rain_basera': 'sum'})

plotly_template="plotly_white"; primary_color="#0F62FE"; secondary_color="#525252"; death_color="#DA1E28"; blanket_color="#24A148"; exp_color="#A8A8A8"; fill_opacity=0.1; text_color="#161616"; grid_color="#E0E0E0"; axis_color="#C6C6C6"; font_family="IBM Plex Sans, sans-serif"; theme_secondary_bg_color="#FFFFFF"
# Reduced default chart height for a more compact view
def style_chart(fig, chart_height=190, is_pie_or_donut=False):
    fig.update_layout(template=plotly_template, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(showgrid=False, linecolor=axis_color, tickfont=dict(color=text_color, size=9), showline=True, zeroline=False),
                            yaxis=dict(showgrid=True, gridcolor=grid_color, linecolor=axis_color, tickfont=dict(color=text_color, size=9), showline=True, zeroline=False),
                            hoverlabel=dict(bgcolor="#FFFFFF", font_size=11, font_family=font_family, bordercolor=axis_color, font_color=text_color),
                            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(color=text_color, size=9), bgcolor='rgba(0,0,0,0)'),
                            margin=dict(l=30, r=10, t=10, b=20), title_text='', title_x=0.5, font_color=text_color, font_family=font_family, height=chart_height) # Reduced margins
    if not is_pie_or_donut:
        fig.update_layout(hovermode='x unified'); fig.update_xaxes(title_text=None, hoverformat='%a, %d %b %Y'); fig.update_yaxes(title_text=None)
    else:
        fig.update_layout(hovermode='closest'); fig.update_layout(xaxis=dict(visible=False, showgrid=False), yaxis=dict(visible=False, showgrid=False))
    return fig

if kpi_ts_df.empty and not df_main.empty :
    st.warning("No data available for KPIs and Time Series charts for the selected filter combination. Please adjust filters.")

def create_single_kpi_card(title, today_val, till_now_val, key_suffix, is_lac=False):
    today_str = f"{today_val:,.2f}" if is_lac else f"{int(today_val):,}"
    till_now_str = f"{till_now_val:,.2f}" if is_lac else f"{int(till_now_val):,}"
    st.markdown(f"""<div class="kpi-card-single" id="kpi-{key_suffix}"><div class="kpi-title">{title}</div><div class="kpi-values-container"><div class="kpi-value-block"><span class="kpi-sublabel">Today</span><span class="kpi-value-main">{today_str}</span></div><div class="kpi-value-block"><span class="kpi-sublabel">Till Now</span><span class="kpi-value-main">{till_now_str}</span></div></div></div>""", unsafe_allow_html=True)

def create_merged_financial_card(allot_today, allot_till, exp_today, exp_till):
    allot_today_str = f"{allot_today:,.2f}"
    allot_till_str = f"{allot_till:,.2f}"
    exp_today_str = f"{exp_today:,.2f}"
    exp_till_str = f"{exp_till:,.2f}"
    st.markdown(f"""<div class="kpi-card-single kpi-card-merged" id="kpi-financial"><div class="merged-kpi-row" style="flex-grow: 1; border-bottom: 1px solid #F0F0F0; margin-bottom: 5px; padding-bottom: 5px;"><div class="kpi-title">ALLOTED AMOUNT (LAC)</div><div class="kpi-values-container"><div class="kpi-value-block"><span class="kpi-sublabel">Today</span><span class="kpi-value-main">{allot_today_str}</span></div><div class="kpi-value-block"><span class="kpi-sublabel">Till Now</span><span class="kpi-value-main">{allot_till_str}</span></div></div></div><div class="merged-kpi-row" style="flex-grow: 1;"><div class="kpi-title">EXPENDITURE AMOUNT (LAC)</div><div class="kpi-values-container"><div class="kpi-value-block"><span class="kpi-sublabel">Today</span><span class="kpi-value-main">{exp_today_str}</span></div><div class="kpi-value-block"><span class="kpi-sublabel">Till Now</span><span class="kpi-value-main">{exp_till_str}</span></div></div></div></div>""", unsafe_allow_html=True)

# Changed column ratios to make the treemap wider.
st.markdown("---")
main_col1, main_col2 = st.columns([0.55, 0.45], gap="large")

with main_col1:
    st.markdown("### Graphical Analysis")
    chart_row1_col1, chart_row1_col2 = st.columns(2, gap="medium")
    with chart_row1_col1:
        st.markdown("###### Affected Population (lac)")
        if not ts_df.empty and 'affected_population_lac' in ts_df.columns:
            fig = px.line(ts_df, x='date', y='affected_population_lac', color_discrete_sequence=[primary_color])
            fig.update_traces(mode='lines', line_shape='linear', line=dict(width=1.5), fill='tozeroy', fillcolor=f'rgba(15, 98, 254, {fill_opacity})', name='Population', hovertemplate='%{y:,.2f} lac<extra></extra>')
            st.plotly_chart(style_chart(fig), use_container_width=True)
        else: st.caption("No data for Population.")

    with chart_row1_col2:
        st.markdown("###### Deaths Reported")
        if not ts_df.empty and 'death' in ts_df.columns:
            fig = px.bar(ts_df, x='date', y='death', color_discrete_sequence=[death_color])
            fig.update_traces(name='Deaths', hovertemplate='%{y:,}<extra></extra>', marker_line_width=0)
            fig.update_layout(bargap=0.6)
            st.plotly_chart(style_chart(fig), use_container_width=True)
        else: st.caption("No data for Deaths.")

    chart_row2_col1, chart_row2_col2 = st.columns(2, gap="medium")
    with chart_row2_col1:
        st.markdown("###### Shelter & Blankets")
        if not ts_df.empty and 'people_in_rain_basera' in ts_df.columns and 'blanket_distributed' in ts_df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ts_df['date'], y=ts_df['people_in_rain_basera'], name='People Sheltered', mode='lines', line=dict(color=secondary_color, width=1.5), fill='tozeroy', fillcolor=f'rgba(82, 82, 82, {fill_opacity})', hovertemplate='Sheltered: %{y:,}<extra></extra>'))
            fig.add_trace(go.Scatter(x=ts_df['date'], y=ts_df['blanket_distributed'], name='Blankets Distributed', mode='lines', line=dict(color=blanket_color, width=1.5, dash='dot'), yaxis='y2', hovertemplate='Blankets: %{y:,}<extra></extra>'))
            fig = style_chart(fig)
            fig.update_layout(yaxis=dict(tickfont=dict(color=secondary_color)), yaxis2=dict(title=None, overlaying='y', side='right', showgrid=False, showline=True, linecolor=axis_color, tickfont=dict(color=blanket_color)), legend=dict(y=1.15))
            st.plotly_chart(fig, use_container_width=True)
        else: st.caption("No data for Shelter & Blankets.")

    with chart_row2_col2:
        st.markdown("###### Financial Overview (Lac)")
        if not ts_df.empty and 'alloted_amount_lac' in ts_df.columns and 'expenditure_amount_lac' in ts_df.columns:
            fig = px.line(ts_df, x='date', y=['alloted_amount_lac', 'expenditure_amount_lac'], color_discrete_sequence=[primary_color, exp_color])
            fig.update_traces(mode='lines', line_shape='linear', line=dict(width=1.5), hovertemplate='%{y:,.2f} lac<extra></extra>')
            fig.update_layout(hovermode='x', legend_title_text=None)
            if len(fig.data) >= 1: fig.data[0].name = 'Alloted'
            if len(fig.data) >= 2: fig.data[1].name = 'Expenditure'
            st.plotly_chart(style_chart(fig), use_container_width=True)
        else: st.caption("No data for Financial Overview.")

with main_col2:
    st.markdown("### Geographical Overview")
    st.markdown("###### District/Block Overview")
    treemap_input_data = base_filtered_df.copy()
    if selected_district_filter:
        treemap_input_data = treemap_input_data[treemap_input_data['district'] == selected_district_filter]
        if selected_block_filter:
            treemap_input_data = treemap_input_data[treemap_input_data['block'] == selected_block_filter]
    
    if not treemap_input_data.empty and 'district' in treemap_input_data.columns and 'block' in treemap_input_data.columns:
        block_level_data = treemap_input_data.groupby(['district', 'block'], as_index=False)['affected_population_lac'].sum()
        block_level_data = block_level_data[block_level_data['affected_population_lac'] > 0.001]
        if not block_level_data.empty:
            
            # REVERTED: The flawed log transformation has been removed to ensure data integrity.
            treemap_path = [px.Constant("Filtered Overview"), 'district', 'block']
            fig_treemap = px.treemap(
                block_level_data, # Using original data
                path=treemap_path, 
                values='affected_population_lac', 
                color='affected_population_lac',
                custom_data=['affected_population_lac'],
                color_continuous_scale='Blues', 
                title=None
            )
            
            fig_treemap.update_layout(
                height=500, 
                margin=dict(t=10, l=10, r=10, b=10), 
                font_family=font_family, 
                hoverlabel=dict(bgcolor="#FFFFFF", font_size=11, font_family=font_family, bordercolor=axis_color, font_color=text_color), 
                coloraxis_colorbar=dict(title="Pop. (Lac)")
            )

            # Using original values for display now
            fig_treemap.update_traces(
                texttemplate="<b>%{label}</b><br>%{value:,.2f}",
                hovertemplate='<b>%{label}</b><br>Population (Lac): %{value:,.2f} L<extra></extra>',
                textposition='middle center', 
                textfont_size=11, 
                marker=dict(cornerradius=0, line=dict(color='#B0B0B0', width=0.5), pad=dict(t=2,l=2,r=2,b=2))
            )
            fig_treemap.update_traces(maxdepth=2)
            st.plotly_chart(fig_treemap, use_container_width=True)
        else: st.caption("No data for Treemap.")
    else: st.caption("No data for Treemap.")

# KPI section moved to the bottom.
kpi_data = {
    "forms": {"title": "Affected/ Form Filled Blocks & Nagar Nikaay", "today": today_df['affected_forms_filled'].sum(), "till_now": tillnow_df_for_kpis['affected_forms_filled'].sum(), "is_lac": False},
    "population": {"title": "AFFECTED POPULATION (LAC)", "today": today_df['affected_population_lac'].sum(), "till_now": tillnow_df_for_kpis['affected_population_lac'].sum(), "is_lac": True},
    "basera": {"title": "NO. OF RAIN BASERA", "today": today_df['rain_basera'].sum(), "till_now": tillnow_df_for_kpis['rain_basera'].sum(), "is_lac": False},
    "deaths": {"title": "NO OF DEATHS", "today": today_df['death'].sum(), "till_now": tillnow_df_for_kpis['death'].sum(), "is_lac": False},
    "people_basera": {"title": "NO. OF PEOPLE IN RAIN BASERA", "today": today_df['people_in_rain_basera'].sum(), "till_now": tillnow_df_for_kpis['people_in_rain_basera'].sum(), "is_lac": False},
    "blankets": {"title": "BLANKETS DISTRIBUTED", "today": today_df['blanket_distributed'].sum(), "till_now": tillnow_df_for_kpis['blanket_distributed'].sum(), "is_lac": False},
    "wood": {"title": "TOTAL WOOD BURN (IN KG)", "today": today_df['wood_burn_kg'].sum(), "till_now": tillnow_df_for_kpis['wood_burn_kg'].sum(), "is_lac": False},
    "bonfires": {"title": "NO. OF BONFIRE PLACES", "today": today_df['bonfire_places'].sum(), "till_now": tillnow_df_for_kpis['bonfire_places'].sum(), "is_lac": False},
    "allotment": {"today": today_df['alloted_amount_lac'].sum(), "till_now": tillnow_df_for_kpis['alloted_amount_lac'].sum()},
    "expenditure": {"today": today_df['expenditure_amount_lac'].sum(), "till_now": tillnow_df_for_kpis['expenditure_amount_lac'].sum()},
}

st.markdown("---") 
st.markdown("### Key Performance Indicators")
kpi_order = ["forms", "population", "basera", "financial", "deaths", "people_basera", "blankets", "wood", "bonfires"]
cols = st.columns(3)
col_idx = 0
for key in kpi_order:
    current_col = cols[col_idx]
    with current_col:
        if key == "financial":
            create_merged_financial_card(allot_today=kpi_data["allotment"]["today"], allot_till=kpi_data["allotment"]["till_now"], exp_today=kpi_data["expenditure"]["today"], exp_till=kpi_data["expenditure"]["till_now"])
        else:
            c = kpi_data[key]
            create_single_kpi_card(c["title"], c["today"], c["till_now"], key, c["is_lac"])
    # MODIFICATION: This line was causing the error. It is now corrected.
    col_idx = (col_idx + 1) %3