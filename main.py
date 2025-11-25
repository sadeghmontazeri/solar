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
                    text-align: right;
                }}
                
                .main .block-container {{
                    padding: 2rem 2rem;
                    max-width: 1200px;
                }}
                
                [data-testid="stMetricValue"] {{
                    font-size: 1.5rem !important;
                    font-weight: bold;
                    color: #00C853 !important;
                }}
                
                .streamlit-expanderHeader {{
                    direction: rtl !important;
                    display: flex !important;
                    flex-direction: row-reverse !important;
                }}
                
                [data-testid="stExpander"] > details > summary {{
                    flex-direction: row-reverse !important;
                }}
                
                .profit-box {{
                    background: linear-gradient(135deg, #00C853 0%, #00E676 100%);
                    padding: 1.5rem;
                    border-radius: 15px;
                    color: white;
                    text-align: center;
                    margin: 1rem 0;
                }}
                
                .highlight-box {{
                    background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%);
                    padding: 1.2rem;
                    border-radius: 12px;
                    color: white;
                    text-align: center;
                }}
                
                .info-box {{
                    background: linear-gradient(135deg, #2196F3 0%, #42A5F5 100%);
                    padding: 1rem;
                    border-radius: 10px;
                    color: white;
                    text-align: center;
                    margin: 0.5rem 0;
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
                    font-size: 1.3rem;
                    padding: 1rem 2rem;
                    border-radius: 12px;
                    border: none;
                    width: 100%;
                }}
                
                #MainMenu {{visibility: hidden;}}
                footer {{visibility: hidden;}}
            </style>
        """, unsafe_allow_html=True)
        return True
    except FileNotFoundError:
        return False

load_font("IRANYekanX-Bold.ttf")

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
    """
    فرمول ساتبا با افزایش ماهانه:
    B = T × K1 × K2 × K3 × K4
    
    month_index: شماره ماه از شروع (0 = ماه اول)
    monthly_inflation: تورم ماهانه
    """
    k1 = (1 + monthly_inflation) ** month_index
    k2 = 1.0  # ضریب ساعتی
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

def suggest_best_system(roof_area, panels_dict, selected_power=None):
    """پیشنهاد بهترین سیستم با در نظر گرفتن فاصله بین پنل‌ها"""
    usable_area = roof_area * 0.75  # 75% قابل استفاده
    suggestions = []
    
    for panel_name, panel_data in panels_dict.items():
        panel_area = panel_data["area"]
        power = selected_power if selected_power else panel_data["default_power"]
        
        # محدود کردن به رنج توان مجاز
        power = max(panel_data["power_range"][0], min(panel_data["power_range"][1], power))
        
        count = math.floor(usable_area / panel_area)
        if count > 0:
            capacity_kw = (count * power) / 1000
            suggestions.append({
                "panel_name": panel_name,
                "panel_power": power,
                "power_range": panel_data["power_range"],
                "count": count,
                "capacity_kw": round(capacity_kw, 2),
                "total_area": round(count * panel_area, 2),
                "efficiency": panel_data["efficiency"],
                "origin": panel_data["origin"],
                "dimensions": f"{panel_data['length_mm']} × {panel_data['width_mm']} × {panel_data['thickness_mm']} mm",
                "area_per_panel": panel_data["area"]
            })
    
    suggestions.sort(key=lambda x: x["capacity_kw"], reverse=True)
    return suggestions

def calculate_roi(yearly_incomes, initial_cost):
    cumulative = 0
    for year_idx, income in enumerate(yearly_incomes, start=1):
        cumulative += income
        if cumulative >= initial_cost:
            remaining = initial_cost - (cumulative - income)
            month_fraction = (remaining / income) * 12 if income > 0 else 0
            return year_idx - 1 + (month_fraction / 12)
    return None

# ================== UI اصلی ==================
st.markdown("""
<div style="text-align: center; padding: 1rem;">
    <h1 style="color: #FF4B4B;">☀️ محاسبه‌گر نیروگاه خورشیدی</h1>
    <h4 style="color: #666;">محاسبه دقیق </h4>
</div>
""", unsafe_allow_html=True)


# ================== نقشه ==================
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
    
    st.success(f"📍 **{city}** | عرض: {lat:.4f}° | طول: {lon:.4f}°")
else:
    lat, lon = default_lat, default_lon
    st.info("📍 تهران - برای دقت بیشتر روی نقشه کلیک کنید")

st.markdown("---")

# ================== ورودی‌ها ==================
st.markdown("### 📏 مشخصات پروژه")

col1, col2, col3 = st.columns(3)

with col1:
    roof_area = st.number_input("متراژ بام (m²)", value=30, min_value=10, max_value=500, step=5)
    st.caption(f"💡 ظرفیت تقریبی: {to_persian_number(round(roof_area * 0.75 / 10 * 1.5, 1))} تا {to_persian_number(round(roof_area * 0.75 / 10 * 2, 1))} کیلووات")

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

# نمایش اطلاعات پنل انتخابی
st.markdown(f"""
<div class="info-box">
    <b>ابعاد:</b> {selected_panel_data['dimensions'] if 'dimensions' in selected_panel_data else f"{selected_panel_data['length_mm']} × {selected_panel_data['width_mm']} × {selected_panel_data['thickness_mm']} mm"} | 
    <b>مساحت:</b> {to_persian_number(selected_panel_data['area'])} m² | 
    <b>رنج توان:</b> {to_persian_number(selected_panel_data['power_range'][0])} - {to_persian_number(selected_panel_data['power_range'][1])} وات |
    <b>بازده:</b> {to_persian_number(selected_panel_data['efficiency'])}%
</div>
""", unsafe_allow_html=True)

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
    format_func=lambda x: f"{x} ({INVERTERS[x]['origin']}) - گارانتی {INVERTERS[x]['warranty']} سال"
)

selected_inverter = get_suitable_inverter(capacity_kw, inverter_brand)

if selected_inverter:
    inv_col1, inv_col2, inv_col3 = st.columns(3)
    inv_col1.metric("مدل", selected_inverter['model'])
    inv_col2.metric("ظرفیت", f"{to_persian_number(selected_inverter['size_kw'])} kW")
    inv_col3.metric("قیمت تقریبی", format_currency(selected_inverter['price']))

# ================== مقادیر ثابت قرارداد ==================
k4 = 1.0  # قرارداد ۸ ساله
contract_years = 8
k3 = 1.2  # ساخت داخل ۲۰٪
cost_per_watt = 35000
annual_inflation = 0.30
monthly_inflation = (1 + annual_inflation) ** (1/12) - 1

# هزینه کل
panel_cost = capacity_kw * 1000 * cost_per_watt
inverter_cost = selected_inverter['price'] if selected_inverter else 0
initial_cost = panel_cost + inverter_cost

st.info(f"💰 **هزینه کل:** {format_currency(initial_cost)} تومان")

st.markdown("---")

# ================== دکمه محاسبه ==================
if st.button("🚀 محاسبه دقیق درآمد", type="primary", use_container_width=True):
    
    with st.spinner("📡 دریافت داده‌های ماهواره‌ای..."):
        pvgis_result = get_pvgis_data(lat, lon, capacity_kw, tilt_angle)
    
    if pvgis_result['success']:
        yearly_production = pvgis_result['yearly'] * (1 - shading_loss)
        monthly_prod = {m: v * (1 - shading_loss) for m, v in pvgis_result['monthly'].items()}
        data_source = pvgis_result['source']
        st.success(f"✅ داده‌های ماهواره‌ای {data_source} دریافت شد")
    else:
        st.warning("⚠️ استفاده از محاسبه محلی...")
        local_result = calculate_solar_production(lat, lon, capacity_kw, tilt_angle)
        yearly_production = local_result['yearly'] * (1 - shading_loss)
        monthly_prod = {m: v * (1 - shading_loss) for m, v in local_result['monthly'].items()}
        data_source = local_result['source']
    
    DEGRADATION = 0.007
    
    months_order = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
    
    total_months = 20 * 12
    contract_months = contract_years * 12
    
    all_monthly_data = []
    yearly_data = []
    income_list = []
    
    for year in range(1, 21):
        degradation_factor = 1 - ((year - 1) * DEGRADATION)
        year_income = 0
        year_production = 0
        
        for month_idx in range(12):
            global_month = (year - 1) * 12 + month_idx
            month_name = months_order[month_idx]
            
            prod = monthly_prod.get(month_name, yearly_production/12) * degradation_factor
            
            # تمام تولید به شبکه فروخته می‌شود
            if global_month < contract_months:
                rate = calculate_satba_rate_monthly(global_month, monthly_inflation, k3, k4)
            else:
                rate = 0
            
            income = prod * rate
            
            year_income += income
            year_production += prod
            
            all_monthly_data.append({
                "سال": year,
                "ماه": month_name,
                "تولید": int(prod),
                "نرخ": int(rate),
                "درآمد": int(income)
            })
        
        income_list.append(year_income)
        yearly_data.append({
            "سال": year,
            "تولید (kWh)": int(year_production),
            "درآمد (تومان)": int(year_income),
        })
    
    df_yearly = pd.DataFrame(yearly_data)
    roi_years = calculate_roi(income_list, initial_cost)
    total_20y = sum(income_list)
    profit_20y = total_20y - initial_cost
    income_contract = sum(income_list[:contract_years])
    
    # ================== نمایش نتایج ==================
    
    st.markdown(f"""
    <div class="profit-box">
        <h2>💰 سود خالص ۲۰ ساله</h2>
        <h1 style="font-size: 2.5rem;">{format_currency(profit_20y)} تومان</h1>
        <p>درآمد دوره قرارداد ({contract_years} سال): {format_currency(income_contract)}</p>
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
        if roi_years and roi_years <= 20:
            years = int(roi_years)
            months = int((roi_years - years) * 12)
            roi_text = f"{to_persian_number(years)} سال و {to_persian_number(months)} ماه"
        else:
            roi_text = "> ۲۰ سال"
        st.metric("بازگشت سرمایه", roi_text)
    
    # نمایش نرخ‌ها
    st.markdown("---")
    st.markdown("### 📈 نرخ خرید در طول زمان")
    
    rate_m1 = calculate_satba_rate_monthly(0, monthly_inflation, k3, k4)
    rate_m12 = calculate_satba_rate_monthly(11, monthly_inflation, k3, k4)
    rate_m24 = calculate_satba_rate_monthly(23, monthly_inflation, k3, k4)
    rate_m60 = calculate_satba_rate_monthly(59, monthly_inflation, k3, k4)
    rate_end = calculate_satba_rate_monthly(contract_months - 1, monthly_inflation, k3, k4)
    
    r1, r2, r3, r4, r5 = st.columns(5)
    r1.metric("ماه اول", f"{to_persian_number(int(rate_m1))} تومان")
    r2.metric("ماه ۱۲", f"{to_persian_number(int(rate_m12))} تومان")
    r3.metric("ماه ۲۴", f"{to_persian_number(int(rate_m24))} تومان")
    r4.metric("ماه ۶۰", f"{to_persian_number(int(rate_m60))} تومان")
    r5.metric(f"آخرین ماه قرارداد", f"{to_persian_number(int(rate_end))} تومان")
    
    # تولید ماهانه
    st.markdown("---")
    st.markdown("### 📅 تولید ماهانه")
    
    prod_values = [monthly_prod.get(m, 0) for m in months_order]
    chart_monthly = pd.DataFrame({'ماه': months_order, 'تولید (kWh)': prod_values}).set_index('ماه')
    st.bar_chart(chart_monthly, color="#FF6B35")
    
    # نمودار درآمد سالانه
    st.markdown("### 💰 درآمد سالانه")
    st.markdown(f"""
    <div class="warning-box">
        ⚠️ پس از پایان قرارداد {contract_years} ساله، درآمد به صفر می‌رسد
    </div>
    """, unsafe_allow_html=True)
    
    chart_income = pd.DataFrame({
        'سال': df_yearly['سال'],
        'درآمد (میلیون)': df_yearly['درآمد (تومان)'] / 1e6
    }).set_index('سال')
    st.line_chart(chart_income, color="#00C853")
    
    # جدول سالانه
    with st.expander("جدول سالانه", expanded=False):
        df_show = df_yearly.copy()
        df_show['سال'] = df_show['سال'].apply(to_persian_number)
        df_show['تولید (kWh)'] = df_show['تولید (kWh)'].apply(lambda x: to_persian_number(x))
        df_show['درآمد (تومان)'] = df_show['درآمد (تومان)'].apply(lambda x: to_persian_number(x))
        st.dataframe(df_show, use_container_width=True, hide_index=True)
    
    # ================== مقایسه ==================
    st.markdown("---")
    st.markdown("### 📊 مقایسه با سایر سرمایه‌گذاری‌ها")
    
    bank_return = initial_cost * ((1.25) ** 20)
    gold_return = initial_cost * ((1.30) ** 20)
    stock_return = initial_cost * ((1.20) ** 20)
    solar_return = total_20y
    
    investments = [
        ("☀️ نیروگاه خورشیدی", solar_return, solar_return - initial_cost),
        ("🏦 سپرده بانکی ۲۵٪", bank_return, bank_return - initial_cost),
        ("🥇 طلا ۳۰٪", gold_return, gold_return - initial_cost),
        ("📈 بورس ۲۰٪", stock_return, stock_return - initial_cost),
    ]
    
    investments_sorted = sorted(investments, key=lambda x: x[2], reverse=True)
    winner = investments_sorted[0][0]
    
    comp_data = {"سرمایه‌گذاری": [], "ارزش ۲۰ ساله": [], "سود خالص": [], "رتبه": []}
    
    for rank, (name, total, profit) in enumerate(investments_sorted, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else ""
        comp_data["سرمایه‌گذاری"].append(name)
        comp_data["ارزش ۲۰ ساله"].append(format_currency(total))
        comp_data["سود خالص"].append(format_currency(profit))
        comp_data["رتبه"].append(f"{medal} {to_persian_number(rank)}")
    
    st.table(pd.DataFrame(comp_data))
    
    if winner == "☀️ نیروگاه خورشیدی":
        st.markdown("""
        <div class="winner-box" style="background: #00C853; color: white;">
            <h3>🏆 نیروگاه خورشیدی سودآورترین گزینه است!</h3>
        </div>
        """, unsafe_allow_html=True)
    else:
        diff = investments_sorted[0][2] - profit_20y
        st.markdown(f"""
        <div class="winner-box" style="background: #FF6B35; color: white;">
            <h3>⚠️ {winner} با {format_currency(diff)} سود بیشتر رتبه اول است</h3>
        </div>
        """, unsafe_allow_html=True)

# فوتر
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; background: #f0f2f6; border-radius: 10px;">
    <p style="color: #666;">📐 محاسبه طبق فرمول ساتبا | 📡 داده‌های PVGIS</p>
    <p style="color: #666;">📏 هر ۱۰ متر مربع ≈ ۱.۵ تا ۲ کیلووات</p>
    <p style="color: #0068c9; font-weight: bold;">مهندس منتظری‌ها | مهندس اکبرپور</p>
</div>
""", unsafe_allow_html=True)
