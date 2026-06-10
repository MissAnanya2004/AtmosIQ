import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import math

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AtmosIQ",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# WEATHER CODE → CONDITION MAPPING (Open-Meteo)
# ─────────────────────────────────────────────
WMO_CODES = {
    0: ("Clear Sky", "sunny"),
    1: ("Mainly Clear", "sunny"),
    2: ("Partly Cloudy", "cloudy"),
    3: ("Overcast", "cloudy"),
    45: ("Foggy", "foggy"),
    48: ("Icy Fog", "foggy"),
    51: ("Light Drizzle", "rainy"),
    53: ("Drizzle", "rainy"),
    55: ("Heavy Drizzle", "rainy"),
    61: ("Slight Rain", "rainy"),
    63: ("Rain", "rainy"),
    65: ("Heavy Rain", "rainy"),
    71: ("Slight Snow", "snowy"),
    73: ("Snow", "snowy"),
    75: ("Heavy Snow", "snowy"),
    77: ("Snow Grains", "snowy"),
    80: ("Slight Showers", "rainy"),
    81: ("Showers", "rainy"),
    82: ("Violent Showers", "stormy"),
    85: ("Snow Showers", "snowy"),
    86: ("Heavy Snow Showers", "snowy"),
    95: ("Thunderstorm", "stormy"),
    96: ("Thunderstorm w/ Hail", "stormy"),
    99: ("Thunderstorm w/ Heavy Hail", "stormy"),
}

# ─────────────────────────────────────────────
# THEME PALETTES PER WEATHER CONDITION
# ─────────────────────────────────────────────
THEMES = {
    "sunny": {
        "bg_gradient": "linear-gradient(135deg, #FF8C00 0%, #FFD700 40%, #FFF4CC 100%)",
        "card_bg": "rgba(255,200,50,0.18)",
        "card_border": "#FFB300",
        "accent": "#FF6F00",
        "text_primary": "#3E2000",
        "text_secondary": "#7A4500",
        "badge_bg": "#FF8C00",
        "badge_text": "#fff",
        "icon": "☀️",
        "plotly_color": "#FFB300",
        "plotly_bg": "#FFF8E1",
    },
    "cloudy": {
        "bg_gradient": "linear-gradient(135deg, #546E7A 0%, #90A4AE 50%, #CFD8DC 100%)",
        "card_bg": "rgba(144,164,174,0.22)",
        "card_border": "#78909C",
        "accent": "#37474F",
        "text_primary": "#1C2B32",
        "text_secondary": "#455A64",
        "badge_bg": "#607D8B",
        "badge_text": "#fff",
        "icon": "☁️",
        "plotly_color": "#78909C",
        "plotly_bg": "#ECEFF1",
    },
    "rainy": {
        "bg_gradient": "linear-gradient(135deg, #1565C0 0%, #1976D2 40%, #64B5F6 100%)",
        "card_bg": "rgba(25,118,210,0.18)",
        "card_border": "#1E88E5",
        "accent": "#0D47A1",
        "text_primary": "#E3F2FD",
        "text_secondary": "#BBDEFB",
        "badge_bg": "#1565C0",
        "badge_text": "#fff",
        "icon": "🌧️",
        "plotly_color": "#1E88E5",
        "plotly_bg": "#E3F2FD",
    },
    "stormy": {
        "bg_gradient": "linear-gradient(135deg, #1A0533 0%, #4A148C 45%, #7B1FA2 100%)",
        "card_bg": "rgba(74,20,140,0.28)",
        "card_border": "#9C27B0",
        "accent": "#CE93D8",
        "text_primary": "#F3E5F5",
        "text_secondary": "#CE93D8",
        "badge_bg": "#7B1FA2",
        "badge_text": "#fff",
        "icon": "⛈️",
        "plotly_color": "#AB47BC",
        "plotly_bg": "#F3E5F5",
    },
    "snowy": {
        "bg_gradient": "linear-gradient(135deg, #B0BEC5 0%, #E0F7FA 50%, #FFFFFF 100%)",
        "card_bg": "rgba(224,247,250,0.4)",
        "card_border": "#80DEEA",
        "accent": "#00838F",
        "text_primary": "#003D47",
        "text_secondary": "#00606D",
        "badge_bg": "#0097A7",
        "badge_text": "#fff",
        "icon": "❄️",
        "plotly_color": "#0097A7",
        "plotly_bg": "#E0F7FA",
    },
    "foggy": {
        "bg_gradient": "linear-gradient(135deg, #757575 0%, #BDBDBD 50%, #EEEEEE 100%)",
        "card_bg": "rgba(189,189,189,0.25)",
        "card_border": "#9E9E9E",
        "accent": "#424242",
        "text_primary": "#212121",
        "text_secondary": "#616161",
        "badge_bg": "#616161",
        "badge_text": "#fff",
        "icon": "🌫️",
        "plotly_color": "#757575",
        "plotly_bg": "#F5F5F5",
    },
}

# ─────────────────────────────────────────────
# SMART NOTIFICATIONS
# ─────────────────────────────────────────────
def get_notifications(condition_type, temp_c, wind_kph, humidity, uv_index=None):
    notes = []
    icons = []

    c = condition_type
    if c == "rainy":
        notes.append("Rainy day ahead — carry an umbrella! ☂️")
        notes.append("Wear waterproof shoes to stay dry 👟")
        icons += ["🌧️", "👟"]
    elif c == "stormy":
        notes.append("⚠️ Storm alert! Stay indoors if possible.")
        notes.append("Avoid open areas and trees during thunderstorms 🌩️")
        icons += ["⚠️", "🌩️"]
    elif c == "snowy":
        notes.append("Bundle up! It's snowing outside ❄️")
        notes.append("Roads may be icy — drive carefully 🚗")
        icons += ["❄️", "🚗"]
    elif c == "foggy":
        notes.append("Low visibility due to fog — drive slow 🌫️")
        notes.append("Use headlights while driving in fog 🚦")
        icons += ["🌫️", "🚦"]
    elif c == "sunny":
        notes.append("Great day for outdoor activities! 🌞")
        notes.append("Apply sunscreen — UV levels may be high 🧴")
        icons += ["🌞", "🧴"]
    elif c == "cloudy":
        notes.append("Mild and overcast — a good day for a walk 🚶")
        icons += ["☁️"]

    if temp_c >= 35:
        notes.append("Extreme heat! Stay hydrated and avoid midday sun 🥵")
    elif temp_c <= 5:
        notes.append("Very cold! Wear layers and a heavy jacket 🧥")

    if wind_kph >= 50:
        notes.append("Strong winds expected — secure loose objects 💨")
    if humidity >= 85:
        notes.append("High humidity — stay in shaded, ventilated areas 💧")

    return notes

# ─────────────────────────────────────────────
# GEOCODING (Open-Meteo Geocoding API — free)
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def geocode_city(city_name):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=5&language=en&format=json"
    try:
        r = requests.get(url, timeout=8)
        data = r.json()
        if "results" in data and data["results"]:
            return data["results"]  # list of {name, latitude, longitude, country, ...}
    except Exception:
        pass
    return None

# ─────────────────────────────────────────────
# WEATHER FETCH (Open-Meteo — completely free)
# ─────────────────────────────────────────────
@st.cache_data(ttl=600)
def fetch_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        f"weather_code,wind_speed_10m,wind_direction_10m,surface_pressure,visibility"
        f"&hourly=temperature_2m,precipitation_probability,weather_code,wind_speed_10m"
        f"&daily=temperature_2m_max,temperature_2m_min,weather_code,"
        f"precipitation_sum,wind_speed_10m_max,uv_index_max,sunrise,sunset"
        f"&timezone=auto&forecast_days=7"
    )
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception as e:
        return None

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def wind_direction_label(deg):
    dirs = ["N","NE","E","SE","S","SW","W","NW"]
    return dirs[round(deg / 45) % 8]

def format_time(iso_str):
    try:
        return datetime.fromisoformat(iso_str).strftime("%I:%M %p")
    except:
        return iso_str

def c_to_f(c): return round(c * 9/5 + 32, 1)

# ─────────────────────────────────────────────
# CSS INJECTION
# ─────────────────────────────────────────────
def inject_css(theme):
    t = THEMES[theme]
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500&display=swap');

    /* Reset app background */
    .stApp {{
        background: {t['bg_gradient']};
        min-height: 100vh;
        font-family: 'Inter', sans-serif;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: rgba(0,0,0,0.35) !important;
        backdrop-filter: blur(18px);
        border-right: 1px solid {t['card_border']}44;
    }}
    [data-testid="stSidebar"] * {{
        color: {t['text_primary']} !important;
    }}

    /* Sidebar inputs */
    [data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stSelectbox select {{
        background: {t['card_bg']} !important;
        border: 1px solid {t['card_border']} !important;
        color: {t['text_primary']} !important;
        border-radius: 10px;
    }}

    /* Metric cards */
    .metric-card {{
        background: {t['card_bg']};
        border: 1px solid {t['card_border']}88;
        border-radius: 18px;
        padding: 20px 18px;
        backdrop-filter: blur(12px);
        text-align: center;
        transition: transform 0.2s ease;
    }}
    .metric-card:hover {{ transform: translateY(-3px); }}

    .metric-value {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: {t['text_primary']};
        margin: 6px 0 2px 0;
    }}
    .metric-label {{
        font-size: 0.8rem;
        color: {t['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 500;
    }}
    .metric-icon {{
        font-size: 1.7rem;
    }}

    /* Hero section */
    .hero-temp {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 6rem;
        font-weight: 700;
        color: {t['text_primary']};
        line-height: 1;
        text-shadow: 0 4px 24px rgba(0,0,0,0.12);
    }}
    .hero-city {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.8rem;
        font-weight: 600;
        color: {t['text_primary']};
    }}
    .hero-condition {{
        font-size: 1.1rem;
        color: {t['text_secondary']};
        font-weight: 500;
        margin-top: 4px;
    }}

    /* Notification cards */
    .notif-card {{
        background: {t['card_bg']};
        border-left: 4px solid {t['accent']};
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 10px;
        color: {t['text_primary']};
        font-size: 0.95rem;
        backdrop-filter: blur(8px);
    }}

    /* Badge */
    .badge {{
        display: inline-block;
        background: {t['badge_bg']};
        color: {t['badge_text']};
        padding: 4px 14px;
        border-radius: 50px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }}

    /* Forecast day cards */
    .forecast-card {{
        background: {t['card_bg']};
        border: 1px solid {t['card_border']}66;
        border-radius: 16px;
        padding: 14px 10px;
        text-align: center;
        backdrop-filter: blur(10px);
    }}
    .forecast-day {{
        font-size: 0.8rem;
        font-weight: 600;
        color: {t['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}
    .forecast-icon {{ font-size: 1.8rem; margin: 8px 0; }}
    .forecast-temp {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: {t['text_primary']};
    }}
    .forecast-min {{
        font-size: 0.85rem;
        color: {t['text_secondary']};
    }}

    /* Section header */
    .section-header {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.05rem;
        font-weight: 600;
        color: {t['text_primary']};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 24px 0 12px 0;
        padding-bottom: 6px;
        border-bottom: 2px solid {t['card_border']}66;
    }}

    /* Brand */
    .brand {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: {t['text_primary']};
        letter-spacing: -0.02em;
    }}
    .brand span {{ color: {t['accent']}; }}

    /* Streamlit button override */
    .stButton button {{
        background: {t['accent']} !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.5rem !important;
        transition: opacity 0.2s;
    }}
    .stButton button:hover {{ opacity: 0.85; }}

    /* Hide streamlit default header & footer */
    #MainMenu, footer, header {{ visibility: hidden; }}

    /* Plotly container glass effect */
    .js-plotly-plot {{
        border-radius: 16px;
        overflow: hidden;
    }}

    /* Selectbox & text input */
    .stTextInput input {{
        border-radius: 10px !important;
        border: 1.5px solid {t['card_border']} !important;
        background: {t['card_bg']} !important;
        color: {t['text_primary']} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PLOTLY CHART HELPERS
# ─────────────────────────────────────────────
def hex_opacity(hex_color, alpha):
    """Convert #RRGGBB + alpha float to rgba() string safe for Plotly."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

def hourly_temp_chart(hourly_data, theme_key, unit="C"):
    t = THEMES[theme_key]
    now = datetime.now()
    times = [datetime.fromisoformat(x) for x in hourly_data["time"]]
    temps = hourly_data["temperature_2m"]
    prec  = hourly_data["precipitation_probability"]

    # Only next 24h
    idx = [i for i,x in enumerate(times) if now <= x <= now + timedelta(hours=24)]
    x_vals = [times[i].strftime("%I %p") for i in idx]
    y_temps = [c_to_f(temps[i]) if unit=="F" else temps[i] for i in idx]
    y_prec  = [prec[i] for i in idx]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_temps, mode="lines+markers",
        name=f"Temp (°{unit})",
        line=dict(color=t["plotly_color"], width=3, shape="spline"),
        marker=dict(size=7, color=t["plotly_color"]),
        yaxis="y1"
    ))
    fig.add_trace(go.Bar(
        x=x_vals, y=y_prec, name="Rain Prob (%)",
        marker_color=hex_opacity(t["plotly_color"], 0.33),
        yaxis="y2", opacity=0.6
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text_primary"], family="Inter"),
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(title=f"°{unit}", showgrid=True, gridcolor=hex_opacity(t["card_border"], 0.27)),
        yaxis2=dict(title="Rain %", overlaying="y", side="right", showgrid=False, range=[0,100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=30, b=10),
        height=280,
    )
    return fig

def wind_gauge(speed_kph, theme_key):
    t = THEMES[theme_key]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=speed_kph,
        title={"text": "Wind Speed (km/h)", "font": {"color": t["text_primary"], "family": "Space Grotesk"}},
        number={"font": {"color": t["text_primary"], "family": "Space Grotesk"}},
        gauge={
            "axis": {"range": [0, 120], "tickcolor": t["text_secondary"]},
            "bar": {"color": t["plotly_color"]},
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": t["card_border"],
            "steps": [
                {"range": [0, 30], "color": hex_opacity(t["plotly_color"], 0.13)},
                {"range": [30, 60], "color": hex_opacity(t["plotly_color"], 0.27)},
                {"range": [60, 120], "color": hex_opacity(t["plotly_color"], 0.40)},
            ],
            "threshold": {"line": {"color": t["accent"], "width": 3}, "value": speed_kph}
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text_primary"]),
        margin=dict(l=10, r=10, t=30, b=10),
        height=230,
    )
    return fig

def humidity_chart(value, theme_key):
    t = THEMES[theme_key]
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        delta={"reference": 60, "increasing": {"color": "#EF5350"}, "decreasing": {"color": "#66BB6A"}},
        title={"text": "Humidity (%)", "font": {"color": t["text_primary"], "family": "Space Grotesk"}},
        number={"suffix": "%", "font": {"color": t["text_primary"], "family": "Space Grotesk"}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": t["plotly_color"]},
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": t["card_border"],
            "steps": [
                {"range": [0, 40], "color": hex_opacity(t["plotly_color"], 0.13)},
                {"range": [40, 70], "color": hex_opacity(t["plotly_color"], 0.27)},
                {"range": [70, 100], "color": "rgba(239,83,80,0.27)"},
            ],
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text_primary"]),
        margin=dict(l=10, r=10, t=30, b=10),
        height=230,
    )
    return fig

# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
def main():
    # --- Sidebar ---
    with st.sidebar:
        st.markdown('<div class="brand">Atmos<span>IQ</span></div>', unsafe_allow_html=True)
        st.markdown("*Your intelligent weather companion*")
        st.markdown("---")

        city_input = st.text_input("🔍 Search City", value="Kolkata", placeholder="e.g. Mumbai, London...")
        unit = st.selectbox("🌡️ Temperature Unit", ["Celsius (°C)", "Fahrenheit (°F)"])
        unit_key = "C" if "Celsius" in unit else "F"

        search_btn = st.button("Get Weather", use_container_width=True)

        st.markdown("---")
        st.markdown("#### About AtmosIQ")
        st.markdown("Powered by **Open-Meteo** free weather API. Real-time data, zero cost, privacy-first.")
        st.markdown("*Built for ESD Project*")

    # --- State ---
    if "weather" not in st.session_state:
        st.session_state.weather = None
        st.session_state.city_name = "Kolkata"
        st.session_state.lat = 22.5726
        st.session_state.lon = 88.3639
        st.session_state.condition_type = "sunny"

    # --- Trigger fetch ---
    if search_btn and city_input.strip():
        results = geocode_city(city_input.strip())
        if results:
            r = results[0]
            st.session_state.lat = r["latitude"]
            st.session_state.lon = r["longitude"]
            st.session_state.city_name = f"{r['name']}, {r.get('country','')}"
        else:
            st.error(f"City '{city_input}' not found. Try another name.")

    # Fetch weather (always, uses cache)
    raw = fetch_weather(st.session_state.lat, st.session_state.lon)

    if not raw:
        st.error("⚠️ Could not fetch weather data. Check your internet connection.")
        return

    # Parse current
    cur = raw["current"]
    wcode = cur["weather_code"]
    cond_label, cond_type = WMO_CODES.get(wcode, ("Unknown", "sunny"))
    temp_c = cur["temperature_2m"]
    feels_c = cur["apparent_temperature"]
    humidity = cur["relative_humidity_2m"]
    wind_kph = cur["wind_speed_10m"]
    wind_dir = cur["wind_direction_10m"]
    pressure = cur["surface_pressure"]
    visibility = cur.get("visibility", 0)

    temp_show = c_to_f(temp_c) if unit_key == "F" else temp_c
    feels_show = c_to_f(feels_c) if unit_key == "F" else feels_c

    # Inject theme CSS
    inject_css(cond_type)
    t = THEMES[cond_type]

    # Daily data
    daily = raw["daily"]
    hourly = raw["hourly"]

    # ── Hero Section ──
    col_hero, col_notif = st.columns([3, 2], gap="large")

    with col_hero:
        st.markdown(f'<div class="badge">{t["icon"]} Live Weather</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="hero-city">📍 {st.session_state.city_name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="hero-temp">{temp_show:.0f}°{unit_key}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="hero-condition">{t["icon"]} {cond_label} &nbsp;·&nbsp; Feels like {feels_show:.0f}°{unit_key}</div>', unsafe_allow_html=True)

        now_str = datetime.now().strftime("%A, %d %B %Y · %I:%M %p")
        ts = t["text_secondary"]
        st.markdown(f'<div style="color:{ts};font-size:0.85rem;margin-top:8px">{now_str}</div>', unsafe_allow_html=True)

        # Sunrise / Sunset
        if "sunrise" in daily and daily["sunrise"]:
            sr = format_time(daily["sunrise"][0])
            ss = format_time(daily["sunset"][0])
            st.markdown(
                f'<div style="margin-top:14px;color:{t["text_secondary"]};font-size:0.9rem">'
                f'🌅 Sunrise: <b style="color:{t["text_primary"]}">{sr}</b> &nbsp;|&nbsp; '
                f'🌇 Sunset: <b style="color:{t["text_primary"]}">{ss}</b></div>',
                unsafe_allow_html=True
            )

    with col_notif:
        st.markdown(f'<div class="section-header">🔔 Smart Alerts</div>', unsafe_allow_html=True)
        uv_today = daily.get("uv_index_max", [None])[0]
        notifications = get_notifications(cond_type, temp_c, wind_kph, humidity, uv_today)
        for n in notifications:
            st.markdown(f'<div class="notif-card">{n}</div>', unsafe_allow_html=True)
        if not notifications:
            st.markdown('<div class="notif-card">✅ All conditions look normal. Enjoy your day!</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Metric Cards ──
    st.markdown(f'<div class="section-header">📊 Current Conditions</div>', unsafe_allow_html=True)
    m1, m2, m3, m4, m5, m6 = st.columns(6)

    metrics = [
        ("💧", "Humidity", f"{humidity}%", m1),
        ("💨", "Wind", f"{wind_kph} km/h", m2),
        ("🧭", "Direction", wind_direction_label(wind_dir), m3),
        ("🔽", "Pressure", f"{pressure:.0f} hPa", m4),
        ("👁️", "Visibility", f"{visibility/1000:.1f} km" if visibility else "N/A", m5),
        ("☀️", "UV Index", str(uv_today) if uv_today else "N/A", m6),
    ]

    for icon, label, value, col in metrics:
        with col:
            st.markdown(
                f'<div class="metric-card"><div class="metric-icon">{icon}</div>'
                f'<div class="metric-value">{value}</div>'
                f'<div class="metric-label">{label}</div></div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 24h Forecast Chart ──
    st.markdown(f'<div class="section-header">📈 24-Hour Temperature & Rain Probability</div>', unsafe_allow_html=True)
    fig_hourly = hourly_temp_chart(hourly, cond_type, unit_key)
    st.plotly_chart(fig_hourly, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Wind & Humidity Gauges ──
    g1, g2 = st.columns(2)
    with g1:
        st.markdown(f'<div class="section-header">💨 Wind Gauge</div>', unsafe_allow_html=True)
        st.plotly_chart(wind_gauge(wind_kph, cond_type), use_container_width=True, config={"displayModeBar": False})
    with g2:
        st.markdown(f'<div class="section-header">💧 Humidity Gauge</div>', unsafe_allow_html=True)
        st.plotly_chart(humidity_chart(humidity, cond_type), use_container_width=True, config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 7-Day Forecast ──
    st.markdown(f'<div class="section-header">📅 7-Day Forecast</div>', unsafe_allow_html=True)
    day_cols = st.columns(7)
    for i, col in enumerate(day_cols):
        try:
            date_str = daily["time"][i]
            day_name = datetime.fromisoformat(date_str).strftime("%a")
            max_t = daily["temperature_2m_max"][i]
            min_t = daily["temperature_2m_min"][i]
            d_code = daily["weather_code"][i]
            d_label, d_type = WMO_CODES.get(d_code, ("", "sunny"))
            d_icon = THEMES[d_type]["icon"]
            rain_mm = daily.get("precipitation_sum", [0]*7)[i] or 0

            if unit_key == "F":
                max_t = c_to_f(max_t)
                min_t = c_to_f(min_t)

            with col:
                st.markdown(
                    f'<div class="forecast-card">'
                    f'<div class="forecast-day">{"Today" if i==0 else day_name}</div>'
                    f'<div class="forecast-icon">{d_icon}</div>'
                    f'<div class="forecast-temp">{max_t:.0f}°</div>'
                    f'<div class="forecast-min">{min_t:.0f}° low</div>'
                    f'<div style="font-size:0.72rem;color:{t["text_secondary"]};margin-top:4px">🌧 {rain_mm:.1f}mm</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        except Exception:
            pass

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 7-Day High/Low Bar Chart ──
    st.markdown(f'<div class="section-header">📊 Weekly Temperature Range</div>', unsafe_allow_html=True)
    days_labels = []
    highs, lows = [], []
    for i in range(7):
        try:
            d = datetime.fromisoformat(daily["time"][i])
            days_labels.append("Today" if i==0 else d.strftime("%a"))
            h = daily["temperature_2m_max"][i]
            l = daily["temperature_2m_min"][i]
            highs.append(c_to_f(h) if unit_key=="F" else h)
            lows.append(c_to_f(l) if unit_key=="F" else l)
        except:
            pass

    fig_week = go.Figure()
    fig_week.add_trace(go.Bar(
        name=f"High (°{unit_key})", x=days_labels, y=highs,
        marker_color=t["plotly_color"], marker_line_width=0
    ))
    fig_week.add_trace(go.Bar(
        name=f"Low (°{unit_key})", x=days_labels, y=lows,
        marker_color=hex_opacity(t["plotly_color"], 0.47), marker_line_width=0
    ))
    fig_week.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text_primary"], family="Inter"),
        xaxis=dict(showgrid=False),
        yaxis=dict(title=f"°{unit_key}", showgrid=True, gridcolor=hex_opacity(t["card_border"], 0.27)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=10, r=10, t=30, b=10),
        height=280,
    )
    st.plotly_chart(fig_week, use_container_width=True, config={"displayModeBar": False})

    # ── Footer ──
    st.markdown(
        f'<div style="text-align:center;color:{t["text_secondary"]};font-size:0.8rem;margin-top:40px;padding:20px 0">'
        f'⚡ AtmosIQ · Powered by Open-Meteo Free API ·'
        f'</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
