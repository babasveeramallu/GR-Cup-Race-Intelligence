import streamlit as st
import json
import pandas as pd
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="GR Cup Race Intelligence",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, clean UI
st.markdown("""
    <style>
    * {
        margin: 0;
        padding: 0;
    }
    
    body {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .main {
        padding: 2rem 1.5rem;
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    [data-testid="stMainBlockContainer"] {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    /* Header styling */
    .header-main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
    }
    
    .header-main h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .header-main p {
        font-size: 1.1rem;
        opacity: 0.95;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.8rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0.8rem 0;
        letter-spacing: 1px;
    }
    
    .metric-label {
        font-size: 0.95rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: white;
        margin: 2rem 0 1.5rem 0;
        padding-bottom: 1rem;
        border-bottom: 3px solid #667eea;
    }
    
    /* Race header */
    .race-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 2rem 0 1.5rem 0;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
    }
    
    .race-header h2 {
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Insight boxes */
    .insight-box {
        padding: 1.2rem;
        margin: 0.8rem 0;
        border-radius: 8px;
        border-left: 5px solid;
        backdrop-filter: blur(10px);
        background-color: rgba(255, 255, 255, 0.05);
    }
    
    .insight-critical {
        border-left-color: #ff6b6b;
        background-color: rgba(255, 107, 107, 0.1);
    }
    
    .insight-high {
        border-left-color: #ffa94d;
        background-color: rgba(255, 164, 77, 0.1);
    }
    
    .insight-medium {
        border-left-color: #4dabf7;
        background-color: rgba(77, 171, 247, 0.1);
    }
    
    .insight-low {
        border-left-color: #b197fc;
        background-color: rgba(177, 151, 252, 0.1);
    }
    
    .insight-text {
        color: white;
        font-weight: 500;
        font-size: 0.95rem;
    }
    
    /* Podium cards */
    .podium-card {
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        border: 2px solid;
        transition: all 0.3s ease;
    }
    
    .podium-card:hover {
        transform: translateY(-10px);
    }
    
    .podium-first {
        background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
        border-color: #ffd700;
    }
    
    .podium-second {
        background: linear-gradient(135deg, #e8e8e8 0%, #808080 100%);
        border-color: #c0c0c0;
    }
    
    .podium-third {
        background: linear-gradient(135deg, #d4a574 0%, #8b4513 100%);
        border-color: #cd7f32;
    }
    
    .podium-medal {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .podium-car {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .podium-lap {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Data tables */
    [data-testid="dataframe"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    .sidebar-header {
        color: #667eea;
        font-weight: 700;
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }
    
    /* Dividers */
    hr {
        border: 0;
        height: 1px;
        background: linear-gradient(to right, transparent, #667eea, transparent);
        margin: 2rem 0;
    }
    
    /* Selectbox styling */
    [data-testid="stSelectbox"] label {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_race_data():
    with open('all_tracks_results.json', 'r') as f:
        return json.load(f)

try:
    race_data = load_race_data()
except FileNotFoundError:
    st.error("Error: all_tracks_results.json not found. Please run process_all_tracks.py first.")
    st.stop()

# Main header
st.markdown("""
    <div class='header-main'>
        <h1>🏁 GR Cup Race Intelligence</h1>
        <p>Real-Time Analytics & Strategy Engine</p>
    </div>
""", unsafe_allow_html=True)

# Summary metrics - improved layout
st.markdown("<h2 class='section-header'>📊 Overall Summary</h2>", unsafe_allow_html=True)
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4, gap="medium")

with metric_col1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Tracks</div>
        <div class='metric-value'>{race_data['summary']['total_tracks']}</div>
    </div>
    """, unsafe_allow_html=True)

with metric_col2:
    st.markdown(f"""
    <div class='metric-card' style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);'>
        <div class='metric-label'>Races</div>
        <div class='metric-value'>{race_data['summary']['total_races']}</div>
    </div>
    """, unsafe_allow_html=True)

with metric_col3:
    st.markdown(f"""
    <div class='metric-card' style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);'>
        <div class='metric-label'>Drivers</div>
        <div class='metric-value'>{race_data['summary']['total_cars']}</div>
    </div>
    """, unsafe_allow_html=True)

with metric_col4:
    st.markdown(f"""
    <div class='metric-card' style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);'>
        <div class='metric-label'>Insights</div>
        <div class='metric-value'>{race_data['summary']['total_insights']}</div>
    </div>
    """, unsafe_allow_html=True)

# Sidebar - Race selector
st.sidebar.markdown("<h3 class='sidebar-header'>🏎️ Select Race</h3>", unsafe_allow_html=True)
all_races = race_data['tracks']
race_names = [f"{t['track']} - Race {t['race']}" for t in all_races]
selected_race_idx = st.sidebar.selectbox("Choose a race:", range(len(all_races)), format_func=lambda x: race_names[x])
selected_race = all_races[selected_race_idx]

# Race header
st.markdown(f"""
    <div class='race-header'>
        <h2>{selected_race['track']} - Race {selected_race['race']}</h2>
    </div>
""", unsafe_allow_html=True)

# Race key metrics
race_metric_col1, race_metric_col2, race_metric_col3 = st.columns(3, gap="medium")

with race_metric_col1:
    st.metric("📍 Current Lap", selected_race['current_lap'], delta=None)

with race_metric_col2:
    st.metric("👥 Total Drivers", len(selected_race['cars']), delta=None)

with race_metric_col3:
    st.metric("⚡ Key Insights", len(selected_race['insights']), delta=None)

st.markdown("---")

# Podium section
st.markdown("<h2 class='section-header'>🏆 Podium - Top 3 Performers</h2>", unsafe_allow_html=True)

top_performers = selected_race['top_performers'][:3]
podium_col1, podium_col2, podium_col3 = st.columns(3, gap="large")

medals = ["🥇", "🥈", "🥉"]
colors = ["podium-first", "podium-second", "podium-third"]

podium_cols = [podium_col1, podium_col2, podium_col3]
for col, perf, medal, color in zip(podium_cols, top_performers, medals, colors):
    with col:
        st.markdown(f"""
        <div class='podium-card {color}'>
            <div class='podium-medal'>{medal}</div>
            <div class='podium-car'>Car #{perf['car_id']}</div>
            <div class='podium-lap'>Best Lap: {perf['best_lap']:.3f}s</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Tabs for better organization
tab1, tab2, tab3, tab4 = st.tabs(["🏁 Race Standings", "💡 Insights", "🔧 Pit Strategy", "🌤️ Conditions"])

# Tab 1: Race Standings
with tab1:
    st.markdown("<h3 style='color: white; margin-bottom: 1rem;'>Full Race Standings</h3>", unsafe_allow_html=True)
    
    cars_data = []
    for car in selected_race['cars']:
        cars_data.append({
            '🏁': car['position'],
            'Car': car['car_id'],
            'Laps': car['total_laps'],
            'Best (s)': f"{car['best_lap_time']:.3f}",
            'Avg (s)': f"{car['avg_lap_time']:.3f}",
            'Consistency': f"{car['consistency_score']:.0f}%",
            'Status': car['status']
        })
    
    cars_df = pd.DataFrame(cars_data)
    st.dataframe(cars_df, width='stretch', hide_index=True)

# Tab 2: Strategic Insights
with tab2:
    st.markdown("<h3 style='color: white; margin-bottom: 1rem;'>Strategic Insights & Alerts</h3>", unsafe_allow_html=True)
    
    if len(selected_race['insights']) > 0:
        for insight in selected_race['insights']:
            priority = insight.get('priority', 'info').lower()
            message = insight.get('message', 'No message')
            
            priority_label = {
                'critical': '🔴 CRITICAL',
                'high': '🟠 HIGH',
                'medium': '🔵 MEDIUM',
                'low': '🟣 LOW'
            }.get(priority, '📌 INFO')
            
            st.markdown(f"""
            <div class='insight-box insight-{priority}'>
                <div class='insight-text'><strong>{priority_label}</strong> {message}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("✅ No critical alerts for this race")

# Tab 3: Pit Strategy
with tab3:
    st.markdown("<h3 style='color: white; margin-bottom: 1rem;'>Pit Strategy - Top 10 Cars</h3>", unsafe_allow_html=True)
    
    pit_data = []
    for car in selected_race['cars'][:10]:
        pit_rec = car['pit_recommendation']
        pit_data.append({
            'Car': car['car_id'],
            'Fuel': f"{pit_rec['fuel_remaining_pct']:.0f}%",
            'Tire': f"{pit_rec['tire_condition_pct']:.0f}%",
            'Critical': pit_rec['critical_factor'],
            'Pit Lap': pit_rec['optimal_pit_lap'],
            'Urgency': pit_rec['urgency']
        })
    
    pit_df = pd.DataFrame(pit_data)
    st.dataframe(pit_df, width='stretch', hide_index=True)

# Tab 4: Track Conditions
with tab4:
    st.markdown("<h3 style='color: white; margin-bottom: 1rem;'>Track Conditions</h3>", unsafe_allow_html=True)
    
    cond_col1, cond_col2 = st.columns(2)
    
    with cond_col1:
        if selected_race['weather'] and selected_race['weather'].get('temperature'):
            temp = selected_race['weather'].get('temperature')
            st.metric("🌡️ Temperature", f"{temp:.1f}°C")
        else:
            st.metric("🌡️ Temperature", "N/A")
    
    with cond_col2:
        if selected_race['weather']:
            conditions = selected_race['weather'].get('conditions', 'Unknown')
            st.metric("☁️ Conditions", conditions)
        else:
            st.metric("☁️ Conditions", "No data")

st.markdown("---")

# Footer
st.markdown(f"""
    <div style='text-align: center; color: #999; padding: 2rem 0; font-size: 0.9rem;'>
        <p><strong>GR Cup Race Intelligence Dashboard</strong></p>
        <p>Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>Engine v1.0 | Analyzing {race_data['summary']['total_tracks']} tracks</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar - About
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 class='sidebar-header'>ℹ️ About</h3>", unsafe_allow_html=True)
st.sidebar.markdown("""
This dashboard provides real-time race analytics with:

✓ Live lap time analysis  
✓ Pit strategy predictions  
✓ Performance consistency scoring  
✓ Weather integration  
✓ Multi-track comparison  

**Data Coverage:**
- Barber: 2 races
- Indianapolis: 2 races
- Others: Partial data
""")

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 class='sidebar-header'>📈 Data Stats</h3>", unsafe_allow_html=True)
st.sidebar.metric("Total Races", race_data['summary']['total_races'])
st.sidebar.metric("Total Drivers", race_data['summary']['total_cars'])
st.sidebar.metric("Total Insights", race_data['summary']['total_insights'])
