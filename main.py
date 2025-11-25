import streamlit as st
import pandas as pd
import numpy as np
import math
import base64
import requests
from streamlit_folium import st_folium
import folium

# --- تنظیمات اولیه ---
st.set_page_config(page_title="محاسبه‌گر خورشیدی", page_icon="☀️", layout="wide")

# ================== تابع تبدیل اعداد به فارسی ==================
def to_persian_number(number):
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    trans_table = str.maketrans(english_digits, persian_digits)
    
    if isinstance(number, (int, float)):
        number = f"{number:,.0f}" if isinstance(number, int) or number == int(number) else f"{number:,.2f}"
    
    return str(number).translate(trans_table)

def format_currency(amount):
    if abs(amount) >= 1_000_000_000:
        return f"{to_persian_number(round(amount/1_000_000_000, 2))} میلیارد"
    else:
        return f"{to_persian_number(int(amount/1_000_000))} میلیون"

# ================== بارگذاری تصاویر ==================
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

logo_b64 = get_base64_image("logo.png")
bg1_b64 = get_base64_image("bg1.jpg")
bg2_b64 = get_base64_image("bg2.jpg")
bg3_b64 = get_base64_image("bg3.jpg")

# ================== تابع بارگذاری فونت ==================
def load_font(font_path):
    try:
        with open(font_path, "rb") as f:
            data = f.read()
        b64_font = base64.b64encode(data).decode()
        
        st.markdown(f"""
            <style>
                @font-face {{
                    font-family: 'IRANYekanX';
                    src: url(data:font/ttf;base64,{b64_font}) format('truetype');
                }}
                
                html, body, [class*="css"], .stMarkdown, .stMetric, h1, h2, h3, h4, h5, p, span, div, label {{
                    font-family: 'IRANYekanX', sans-serif !important;
                    direction: rtl;
                    text-align: center;
                }}
                
                .main .block-container {{
                    padding: 0 !important;
                    max-width: 100% !important;
                }}
                
                [data-testid="stMetricValue"] {{
                    font-size: clamp(1rem, 3vw, 1.5rem) !important;
                    font-weight: bold;
                    color: #00C853 !important;
                    text-align: center !important;
                }}
                
                [data-testid="stMetricLabel"] {{
                    text-align: center !important;
                }}
                
                .streamlit-expanderHeader {{
                    direction: rtl !important;
                    display: flex !important;
                    flex-direction: row-reverse !important;
                    justify-content: center !important;
                }}
                
                [data-testid="stExpander"] > details > summary {{
                    flex-direction: row-reverse !important;
                }}
                
                .profit-box {{
                    background: linear-gradient(135deg, #00C853 0%, #00E676 100%);
                    padding: clamp(1rem, 3vw, 1.5rem);
                    border-radius: 15px;
                    color: white;
                    text-align: center;
                    margin: 1rem auto;
                    max-width: 600px;
                }}
                
                .highlight-box {{
                    background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%);
                    padding: clamp(0.8rem, 2vw, 1.2rem);
                    border-radius: 12px;
                    color: white;
                    text-align: center;
                }}
                
                .info-box {{
                    background: linear-gradient(135deg, #2196F3 0%, #42A5F5 100%);
                    padding: clamp(0.8rem, 2vw, 1rem);
                    border-radius: 10px;
                    color: white;
                    text-align: center;
                    margin: 0.5rem auto;
                    max-width: 500px;
                }}
                
                .warning-box {{
                    background: linear-gradient(135deg, #FF9800 0%, #FFB74D 100%);
                    padding: 1rem;
                    border-radius: 10px;
                    color: white;
                    text-align: center;
                    margin: 0.5rem 0;
                }}
                
                .winner-box {{
                    padding: 1rem;
                    border-radius: 10px;
                    text-align: center;
                    margin-top: 1rem;
                }}
                
                .stButton > button {{
                    background: linear-gradient(135deg, #FF4B4B 0%, #FF6B6B 100%);
                    color: white;
                    font-size: clamp(1rem, 2.5vw, 1.3rem);
                    padding: clamp(0.8rem, 2vw, 1rem) clamp(1rem, 3vw, 2rem);
                    border-radius: 12px;
                    border: none;
                    width: 100%;
                    max-width: 400px;
                    margin: 0 auto;
                    display: block;
                }}
                
                /* هیرو سکشن */
                .hero-section {{
                    position: relative;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                    overflow: hidden;
                    margin: -1rem -1rem 2rem -1rem;
                }}
                
                .hero-bg {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-size: cover;
                    background-position: center;
                    animation: slideshow 15s infinite;
                    z-index: 0;
                }}
                
                .hero-bg::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(135deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.4) 100%);
                    z-index: 1;
                }}
                
                @keyframes slideshow {{
                    0%, 30% {{ background-image: url('data:image/jpeg;base64,{bg1_b64}'); }}
                    33%, 63% {{ background-image: url('data:image/jpeg;base64,{bg2_b64}'); }}
                    66%, 100% {{ background-image: url('data:image/jpeg;base64,{bg3_b64}'); }}
                }}
                
                .hero-content {{
                    position: relative;
                    z-index: 2;
                    color: white;
                    padding: clamp(1rem, 4vw, 2rem);
                    max-width: 900px;
                    width: 100%;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                }}
                
                .logo-img {{
                    width: clamp(80px, 15vw, 120px);
                    height: clamp(80px, 15vw, 120px);
                    border-radius: 50%;
                    box-shadow: 0 10px 40px rgba(255,255,0,0.3);
                    margin-bottom: clamp(1rem, 3vw, 1.5rem);
                }}
                
                .hero-title {{
                    font-size: clamp(1.5rem, 5vw, 3rem);
                    font-weight: bold;
                    margin-bottom: 0.5rem;
                    text-shadow: 2px 2px 10px rgba(0,0,0,0.5);
                    text-align: center;
                    width: 100%;
                }}
                
                .hero-subtitle {{
                    font-size: clamp(0.9rem, 2.5vw, 1.3rem);
                    margin-bottom: clamp(1.5rem, 4vw, 2rem);
                    opacity: 0.9;
                    text-align: center;
                    width: 100%;
                }}
                
                .hero-stats {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: clamp(1rem, 5vw, 3rem);
                    flex-wrap: wrap;
                    width: 100%;
                }}
                
                .stat-item {{
                    text-align: center;
                    min-width: clamp(80px, 20vw, 120px);
                }}
                
                .stat-value {{
                    font-size: clamp(1.3rem, 4vw, 2.5rem);
                    font-weight: bold;
                    color: #FFD700;
                    text-shadow: 2px 2px 10px rgba(0,0,0,0.5);
                }}
                
                .stat-label {{
                    font-size: clamp(0.7rem, 1.8vw, 0.9rem);
                    opacity: 0.8;
                }}
                
                .calc-container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: clamp(1rem, 3vw, 2rem);
                    text-align: center;
                }}
                
                .calc-container h3 {{
                    text-align: center !important;
                }}
                
                #MainMenu {{visibility: hidden;}}
                footer {{visibility: hidden;}}
                header {{visibility: hidden;}}
                
                /* رسپانسیو برای موبایل */
                @media (max-width: 768px) {{
                    .hero-stats {{
                        gap: 1rem;
                    }}
                    .stat-item {{
                        flex: 0 0 30%;
                    }}
                }}
            </style>
        """, unsafe_allow_html=True)
        return True
    except FileNotFoundError:
        return False

load_font("IRANYekanX-Bold.ttf")

# ================== هیرو سکشن ==================
st.markdown(f"""
<div class="hero-section">
    <div class="hero-bg"></div>
    <div class="hero-content">
        <img src="data:image/png;base64,{logo_b64}" class="logo-img" alt="لوگو">
        <h1 class="hero-title">شرکت توزیع نیروی  برق تهران بزرگ</h1>
        <p class="hero-subtitle">نرم افزار محاسبه نیروگاه های خورشیدی</p>
        <div class="hero-stats">
            <div class="stat-item">
                <div class="stat-value">۲۰</div>
                <div class="stat-label">سال قرارداد</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">۳,۸۲۰</div>
                <div class="stat-label">تومان/kWh</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">۳۰٪</div>
                <div class="stat-label">رشد سالانه</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ================== ثوابت فرمول ساتبا ==================
T_BASE = 3820  # نرخ پایه (تومان/kWh)

# ================== پنل‌های خارجی ==================
FOREIGN_PANELS = {
    "Jinko Solar (Tiger Pro, Eagle)": {
        "power_range": (550, 620),
        "default_power": 580,
        "length_mm": 2278,
        "width_mm": 1134,
        "thickness_mm": 30,
        "area": 2.58,
        "efficiency": 22.5,
        "origin": "خارجی"
    },
    "Trina Solar (Vertex S, Vertex N)": {
        "power_range": (430, 510),
        "default_power": 470,
        "length_mm": 1762,
        "width_mm": 1134,
        "thickness_mm": 30,
        "area": 2.00,
        "efficiency": 21.8,
        "origin": "خارجی"
    },
    "Canadian Solar (HiKu6, TOPHiKu6)": {
        "power_range": (540, 610),
        "default_power": 575,
        "length_mm": 2261,
        "width_mm": 1134,
        "thickness_mm": 35,
        "area": 2.56,
        "efficiency": 22.3,
        "origin": "خارجی"
    },
    "JA Solar (DeepBlue 4.0)": {
        "power_range": (430, 500),
        "default_power": 465,
        "length_mm": 1762,
        "width_mm": 1134,
        "thickness_mm": 30,
        "area": 2.00,
        "efficiency": 21.5,
        "origin": "خارجی"
    },
    "LONGi Solar (Hi-MO 6)": {
        "power_range": (420, 490),
        "default_power": 455,
        "length_mm": 1722,
        "width_mm": 1134,
        "thickness_mm": 30,
        "area": 1.95,
        "efficiency": 22.0,
        "origin": "خارجی"
    },
    "AE Solar (Topcon Series)": {
        "power_range": (550, 620),
        "default_power": 580,
        "length_mm": 2278,
        "width_mm": 1133,
        "thickness_mm": 30,
        "area": 2.58,
        "efficiency": 22.4,
        "origin": "خارجی"
    },
    "Q Cells (Q.Peak Duo)": {
        "power_range": (400, 470),
        "default_power": 435,
        "length_mm": 1879,
        "width_mm": 1045,
        "thickness_mm": 32,
        "area": 1.96,
        "efficiency": 21.6,
        "origin": "خارجی"
    },
    "SunPower (Maxeon 6)": {
        "power_range": (410, 450),
        "default_power": 430,
        "length_mm": 1872,
        "width_mm": 1032,
        "thickness_mm": 40,
        "area": 1.93,
        "efficiency": 22.8,
        "origin": "خارجی"
    },
    "REC Solar (Alpha Pure)": {
        "power_range": (405, 450),
        "default_power": 425,
        "length_mm": 1730,
        "width_mm": 1118,
        "thickness_mm": 30,
        "area": 1.93,
        "efficiency": 22.2,
        "origin": "خارجی"
    },
    "Znshine Solar (Zebra Series)": {
        "power_range": (600, 700),
        "default_power": 650,
        "length_mm": 2465,
        "width_mm": 1134,
        "thickness_mm": 35,
        "area": 2.79,
        "efficiency": 23.0,
        "origin": "خارجی"
    },
}

# ================== پنل‌های ایرانی ==================
IRANIAN_PANELS = {
    "مانا انرژی پاک (PERC, TOPCon)": {
        "power_range": (400, 550),
        "default_power": 475,
        "length_mm": 1956,
        "width_mm": 992,
        "thickness_mm": 35,
        "area": 1.94,
        "efficiency": 21.5,
        "origin": "ایرانی"
    },
    "تابان انرژی (Taban Mono)": {
        "power_range": (380, 500),
        "default_power": 440,
        "length_mm": 1956,
        "width_mm": 992,
        "thickness_mm": 40,
        "area": 1.94,
        "efficiency": 21.0,
        "origin": "ایرانی"
    },
    "سولار صنعت فیروزه": {
        "power_range": (380, 480),
        "default_power": 430,
        "length_mm": 1956,
        "width_mm": 992,
        "thickness_mm": 40,
        "area": 1.94,
        "efficiency": 20.8,
        "origin": "ایرانی"
    },
    "پایدار سولار (Bifacial)": {
        "power_range": (540, 620),
        "default_power": 580,
        "length_mm": 2278,
        "width_mm": 1134,
        "thickness_mm": 30,
        "area": 2.58,
        "efficiency": 22.3,
        "origin": "ایرانی"
    },
    "ماناسازان": {
        "power_range": (380, 480),
        "default_power": 430,
        "length_mm": 1956,
        "width_mm": 992,
        "thickness_mm": 35,
        "area": 1.94,
        "efficiency": 20.8,
        "origin": "ایرانی"
    },
    "انرژی‌های نوین مهرآباد": {
        "power_range": (380, 480),
        "default_power": 430,
        "length_mm": 1956,
        "width_mm": 992,
        "thickness_mm": 30,
        "area": 1.94,
        "efficiency": 20.8,
        "origin": "ایرانی"
    },
    "برق آفتابی هدایت نور یزد": {
        "power_range": (380, 480),
        "default_power": 430,
        "length_mm": 1956,
        "width_mm": 992,
        "thickness_mm": 30,
        "area": 1.94,
        "efficiency": 20.5,
        "origin": "ایرانی"
    },
    "الکترونیک سازان سمنان": {
        "power_range": (380, 480),
        "default_power": 430,
        "length_mm": 1956,
        "width_mm": 992,
        "thickness_mm": 30,
        "area": 1.94,
        "efficiency": 20.5,
        "origin": "ایرانی"
    },
}

# ترکیب همه پنل‌ها
ALL_PANELS = {**FOREIGN_PANELS, **IRANIAN_PANELS}

# ================== اینورترها ==================
INVERTERS = {
    "Growatt": {
        "models": {3: "MIN 3000TL-X", 5: "MIN 5000TL-X", 6: "MIN 6000TL-X", 8: "MOD 8KTL3-X", 10: "MOD 10KTL3-X", 15: "MOD 15KTL3-X", 20: "MOD 20KTL3-X"},
        "warranty": 5, "origin": "چین", "price_per_kw": 1_800_000,
    },
    "Huawei": {
        "models": {3: "SUN2000-3KTL", 5: "SUN2000-5KTL", 6: "SUN2000-6KTL", 8: "SUN2000-8KTL", 10: "SUN2000-10KTL", 15: "SUN2000-15KTL", 20: "SUN2000-20KTL"},
        "warranty": 5, "origin": "چین", "price_per_kw": 2_200_000,
    },
    "Sungrow": {
        "models": {3: "SG3.0RS", 5: "SG5.0RS", 6: "SG6.0RS", 8: "SG8.0RT", 10: "SG10RT", 15: "SG15RT", 20: "SG20RT"},
        "warranty": 5, "origin": "چین", "price_per_kw": 2_000_000,
    },
    "Fronius": {
        "models": {3: "Primo 3.0", 5: "Primo 5.0", 6: "Primo 6.0", 8: "Symo 8.2", 10: "Symo 10.0", 15: "Symo 15.0", 20: "Symo 20.0"},
        "warranty": 7, "origin": "اتریش", "price_per_kw": 3_500_000,
    },
}

def get_suitable_inverter(capacity_kw, brand):
    inverter_data = INVERTERS.get(brand)
    if not inverter_data:
        return None
    
    models = inverter_data["models"]
    suitable_size = None
    
    for size in sorted(models.keys()):
        if size >= capacity_kw:
            suitable_size = size
            break
    
    if suitable_size is None:
        suitable_size = max(models.keys())
    
    return {
        "brand": brand,
        "model": models[suitable_size],
        "size_kw": suitable_size,
        "warranty": inverter_data["warranty"],
        "origin": inverter_data["origin"],
        "price": suitable_size * inverter_data["price_per_kw"],
    }

# ================== فرمول ساتبا - ماهانه ==================
def calculate_satba_rate_monthly(month_index, monthly_inflation, k3, k4):
    k1 = (1 + monthly_inflation) ** month_index
    k2 = 1.0
    B = T_BASE * k1 * k2 * k3 * k4
    return B

# ================== PVGIS ==================
@st.cache_data(ttl=86400)
def get_pvgis_data(lat, lon, peak_power_kw, tilt=35):
    try:
        url = "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"
        params = {
            "lat": lat, "lon": lon, "peakpower": peak_power_kw,
            "loss": 14, "mountingplace": "building", "angle": tilt,
            "aspect": 0, "outputformat": "json", "pvcalculation": 1,
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            monthly = data['outputs']['monthly']['fixed']
            monthly_production = {}
            
            persian_months = {1: "دی", 2: "بهمن", 3: "اسفند", 4: "فروردین", 5: "اردیبهشت", 6: "خرداد",
                             7: "تیر", 8: "مرداد", 9: "شهریور", 10: "مهر", 11: "آبان", 12: "آذر"}
            miladi_to_shamsi = {1: 10, 2: 11, 3: 12, 4: 1, 5: 2, 6: 3, 7: 4, 8: 5, 9: 6, 10: 7, 11: 8, 12: 9}
            
            for month_data in monthly:
                miladi_month = month_data['month']
                shamsi_month = miladi_to_shamsi[miladi_month]
                month_name = persian_months[shamsi_month]
                monthly_production[month_name] = month_data['E_m']
            
            yearly = data['outputs']['totals']['fixed']['E_y']
            return {'success': True, 'yearly': yearly, 'monthly': monthly_production, 'source': 'PVGIS'}
        else:
            return {'success': False}
    except:
        return {'success': False}

def calculate_solar_production(lat, lon, capacity_kw, tilt=35):
    base_ghi = 2100 - (lat - 25) * 25
    base_ghi = max(1600, min(2300, base_ghi))
    pr = 0.78
    yearly = capacity_kw * (base_ghi / 1000) * pr
    
    monthly_factors = {
        "فروردین": 0.070, "اردیبهشت": 0.095, "خرداد": 0.105,
        "تیر": 0.110, "مرداد": 0.115, "شهریور": 0.100,
        "مهر": 0.090, "آبان": 0.080, "آذر": 0.065,
        "دی": 0.055, "بهمن": 0.055, "اسفند": 0.060,
    }
    
    monthly_production = {m: yearly * f for m, f in monthly_factors.items()}
    return {'success': True, 'yearly': yearly, 'monthly': monthly_production, 'source': 'محاسبه محلی', 'ghi': base_ghi}

def calculate_roi(yearly_incomes, initial_cost):
    cumulative = 0
    for year_idx, income in enumerate(yearly_incomes, start=1):
        cumulative += income
        if cumulative >= initial_cost:
            remaining = initial_cost - (cumulative - income)
            month_fraction = (remaining / income) * 12 if income > 0 else 0
            return year_idx - 1 + (month_fraction / 12)
    return None

# ================== بخش محاسبه ==================
st.markdown('<div class="calc-container">', unsafe_allow_html=True)

st.markdown("### 🌍 محل نصب")

default_lat, default_lon = 35.6892, 51.3890
m = folium.Map(location=[default_lat, default_lon], zoom_start=6, tiles='OpenStreetMap')
m.add_child(folium.LatLngPopup())
folium.Marker([default_lat, default_lon], popup="تهران", icon=folium.Icon(color="red", icon="home")).add_to(m)

map_output = st_folium(m, height=350, width=None, returned_objects=["last_clicked"])

if map_output and map_output.get('last_clicked'):
    lat = map_output['last_clicked']['lat']
    lon = map_output['last_clicked']['lng']
    
    city = "موقعیت انتخابی"
    if 35.5 < lat < 35.9 and 51.1 < lon < 51.7: city = "تهران"
    elif 32.4 < lat < 32.8 and 51.5 < lon < 51.9: city = "اصفهان"
    elif 29.4 < lat < 29.8 and 52.4 < lon < 52.7: city = "شیراز"
    elif 36.1 < lat < 36.5 and 59.4 < lon < 59.8: city = "مشهد"
    elif 37.9 < lat < 38.3 and 46.2 < lon < 46.5: city = "تبریز"
    elif 30.2 < lat < 30.5 and 48.2 < lon < 48.5: city = "اهواز"
    
    st.success(f"📍 **{city}**")
else:
    lat, lon = default_lat, default_lon
    st.info("📍 تهران")

st.markdown("---")

# ================== ورودی‌ها ==================
st.markdown("### 📏 مشخصات پروژه")

col1, col2, col3 = st.columns(3)

with col1:
    roof_area = st.number_input("متراژ بام (m²)", value=30, min_value=10, max_value=500, step=5)

with col2:
    tilt_angle = st.number_input("زاویه نصب (درجه)", value=35, min_value=10, max_value=45, step=5)

with col3:
    shading_options = {"بدون سایه": 0, "کمی سایه ۱۰٪": 0.10, "سایه متوسط ۲۰٪": 0.20}
    shading_choice = st.selectbox("وضعیت سایه", list(shading_options.keys()))
    shading_loss = shading_options[shading_choice]

# ================== انتخاب پنل ==================
st.markdown("---")
st.markdown("### 💡 انتخاب پنل")

col_panel1, col_panel2 = st.columns(2)

with col_panel1:
    panel_origin = st.radio("نوع پنل", ["همه", "خارجی", "ایرانی"], horizontal=True)

if panel_origin == "خارجی":
    available_panels = FOREIGN_PANELS
elif panel_origin == "ایرانی":
    available_panels = IRANIAN_PANELS
else:
    available_panels = ALL_PANELS

with col_panel2:
    selected_panel_name = st.selectbox(
        "انتخاب برند پنل",
        list(available_panels.keys()),
        format_func=lambda x: f"{x} ({available_panels[x]['origin']})"
    )

selected_panel_data = available_panels[selected_panel_name]

# انتخاب توان پنل
panel_power = st.slider(
    "توان پنل (وات)",
    min_value=selected_panel_data['power_range'][0],
    max_value=selected_panel_data['power_range'][1],
    value=selected_panel_data['default_power'],
    step=5
)

# محاسبه تعداد و ظرفیت
usable_area = roof_area * 0.75
panel_count = math.floor(usable_area / selected_panel_data['area'])
capacity_kw = round((panel_count * panel_power) / 1000, 2)
total_panel_area = round(panel_count * selected_panel_data['area'], 2)

# نمایش نتیجه انتخاب
p1, p2, p3, p4 = st.columns(4)
p1.metric("تعداد پنل", f"{to_persian_number(panel_count)} عدد")
p2.metric("ظرفیت کل", f"{to_persian_number(capacity_kw)} kW")
p3.metric("مساحت اشغالی", f"{to_persian_number(total_panel_area)} m²")
p4.metric("مساحت باقیمانده", f"{to_persian_number(round(roof_area - total_panel_area, 1))} m²")

# ================== انتخاب اینورتر ==================
st.markdown("---")
st.markdown("### ⚡ انتخاب اینورتر")

inverter_brand = st.selectbox(
    "برند اینورتر",
    list(INVERTERS.keys()),
    format_func=lambda x: f"{x} ({INVERTERS[x]['origin']})"
)

selected_inverter = get_suitable_inverter(capacity_kw, inverter_brand)

if selected_inverter:
    inv_col1, inv_col2, inv_col3 = st.columns(3)
    inv_col1.metric("مدل", selected_inverter['model'])
    inv_col2.metric("ظرفیت", f"{to_persian_number(selected_inverter['size_kw'])} kW")
    inv_col3.metric("قیمت تقریبی", format_currency(selected_inverter['price']))

# ================== مقادیر ثابت قرارداد ==================
k4 = 1.0
contract_years = 20
k3 = 1.2
cost_per_watt = 35000
annual_inflation = 0.30
monthly_inflation = (1 + annual_inflation) ** (1/12) - 1

# هزینه کل
panel_cost = capacity_kw * 1000 * cost_per_watt
inverter_cost = selected_inverter['price'] if selected_inverter else 0
initial_cost = panel_cost + inverter_cost

st.markdown(f"""
<div class="info-box">
    💰 هزینه کل: {format_currency(initial_cost)} تومان
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ================== دکمه محاسبه ==================
if st.button("🚀 محاسبه درآمد", type="primary", use_container_width=True):
    
    with st.spinner("📡 دریافت داده‌های ماهواره‌ای..."):
        pvgis_result = get_pvgis_data(lat, lon, capacity_kw, tilt_angle)
    
    if pvgis_result['success']:
        yearly_production = pvgis_result['yearly'] * (1 - shading_loss)
        monthly_prod = {m: v * (1 - shading_loss) for m, v in pvgis_result['monthly'].items()}
        data_source = pvgis_result['source']
    else:
        local_result = calculate_solar_production(lat, lon, capacity_kw, tilt_angle)
        yearly_production = local_result['yearly'] * (1 - shading_loss)
        monthly_prod = {m: v * (1 - shading_loss) for m, v in local_result['monthly'].items()}
        data_source = local_result['source']
    
    DEGRADATION = 0.007
    
    months_order = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
    
    contract_months = contract_years * 12
    
    yearly_data = []
    income_list = []
    
    for year in range(1, contract_years + 1):
        degradation_factor = 1 - ((year - 1) * DEGRADATION)
        year_income = 0
        year_production = 0
        
        for month_idx in range(12):
            global_month = (year - 1) * 12 + month_idx
            month_name = months_order[month_idx]
            
            prod = monthly_prod.get(month_name, yearly_production/12) * degradation_factor
            rate = calculate_satba_rate_monthly(global_month, monthly_inflation, k3, k4)
            income = prod * rate
            
            year_income += income
            year_production += prod
        
        income_list.append(year_income)
        yearly_data.append({
            "سال": year,
            "تولید (kWh)": int(year_production),
            "درآمد (تومان)": int(year_income),
        })
    
    df_yearly = pd.DataFrame(yearly_data)
    roi_years = calculate_roi(income_list, initial_cost)
    total_income = sum(income_list)
    profit = total_income - initial_cost
    
    # ================== نمایش نتایج ==================
    
    st.markdown(f"""
    <div class="profit-box">
        <h2>💰 سود خالص ۲۰ ساله</h2>
        <h1 style="font-size: clamp(1.8rem, 5vw, 2.5rem);">{format_currency(profit)} تومان</h1>
    </div>
    """, unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    
    with m1:
        st.metric("هزینه احداث", format_currency(initial_cost))
    
    with m2:
        st.metric("تولید سالانه", f"{to_persian_number(int(yearly_production))} kWh")
    
    with m3:
        income_y1 = int(yearly_data[0]['درآمد (تومان)'])
        st.metric("درآمد سال اول", format_currency(income_y1))
    
    with m4:
        if roi_years and roi_years <= contract_years:
            years = int(roi_years)
            months = int((roi_years - years) * 12)
            roi_text = f"{to_persian_number(years)} سال و {to_persian_number(months)} ماه"
        else:
            roi_text = f"> {contract_years} سال"
        st.metric("بازگشت سرمایه", roi_text)
    
    # نمودار تولید ماهیانه (مستطیلی)
    st.markdown("### 📅 تولید ماهیانه")
    prod_values = [monthly_prod.get(m, 0) for m in months_order]
    chart_monthly = pd.DataFrame({'ماه': months_order, 'تولید (kWh)': prod_values}).set_index('ماه')
    st.bar_chart(chart_monthly, color="#FF6B35")
    
    # نمودار درآمد سالانه
    st.markdown("### 📈 درآمد سالانه")
    
    chart_income = pd.DataFrame({
        'سال': df_yearly['سال'],
        'درآمد (میلیارد)': df_yearly['درآمد (تومان)'] / 1e9
    }).set_index('سال')
    st.line_chart(chart_income, color="#00C853")
    
    # جدول سالانه
    with st.expander("جدول سالانه"):
        df_show = df_yearly.copy()
        df_show['سال'] = df_show['سال'].apply(to_persian_number)
        df_show['تولید (kWh)'] = df_show['تولید (kWh)'].apply(lambda x: to_persian_number(x))
        df_show['درآمد (تومان)'] = df_show['درآمد (تومان)'].apply(lambda x: to_persian_number(x))
        st.dataframe(df_show, use_container_width=True, hide_index=True)

st.markdown('</div>', unsafe_allow_html=True)

# ================== فوتر ==================
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; background: #1a1a2e; border-radius: 10px; color: white;">
    <p style="color: #FFD700; font-size: clamp(1rem, 2.5vw, 1.2rem); font-weight: bold;">
        نظارت عالیه: مهندس نقی اکبرپور
    </p>
    <p style="color: #FFD700; font-size: clamp(1rem, 2.5vw, 1.2rem); font-weight: bold;">
        طراح : مهندس محمدصادق منتظریها
    </p>
</div>
""", unsafe_allow_html=True)
