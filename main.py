import streamlit as st
import pvlib
import pandas as pd
import math
import base64
from pvlib.modelchain import ModelChain
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

# --- تنظیمات اولیه ---
st.set_page_config(page_title="محاسبه‌گر خورشیدی", page_icon="☀️", layout="centered")

# ================== تابع بارگذاری فونت اختصاصی ==================
def load_font(font_path):
    try:
        with open(font_path, "rb") as f:
            data = f.read()
        b64_font = base64.b64encode(data).decode()
        
        # تزریق CSS برای تغییر فونت کل برنامه
        st.markdown(f"""
            <style>
                @font-face {{
                    font-family: 'IRANYekanX';
                    src: url(data:font/ttf;base64,{b64_font}) format('truetype');
                }}
                
                /* اعمال فونت به همه اجزا */
                html, body, [class*="css"], .stMarkdown, .stMetric, h1, h2, h3, p {{
                    font-family: 'IRANYekanX', sans-serif !important;
                    direction: rtl;
                    text-align: right;
                }}
                
                /* تنظیمات اسلایدر */
                .stSlider {{ direction: ltr !important; }}
                .stSlider label {{ direction: rtl !important; width: 100%; }}
                
                /* مخفی کردن منوها */
                #MainMenu {{visibility: hidden;}}
                footer {{visibility: hidden;}}
            </style>
        """, unsafe_allow_html=True)
        return True
    except FileNotFoundError:
        st.warning(f"⚠️ فایل فونت '{font_path}' پیدا نشد. لطفاً فایل را کنار برنامه قرار دهید.")
        return False

# فراخوانی فونت (نام فایل را دقیق وارد کنید)
load_font("IRANYekanX-Bold.ttf")

# ================== ورودی‌های ساده ==================
st.title("☀️ محاسبه سود نیروگاه خورشیدی")
st.markdown("ورودی‌های ساده را وارد کنید، سیستم بقیه موارد را محاسبه می‌کند.")

col1, col2 = st.columns(2)
with col1:
    roof_area = st.number_input("متراژ بام (متر مربع)", value=40, step=5, min_value=10)
with col2:
    tilt_angle = st.slider("زاویه نصب پنل", 0, 60, 30)

# تنظیمات پشت صحنه
LAT, LON = 35.68, 51.38 
BASE_RATE = 3820 
INFLATION = 0.40 
CLOUD_LOSS_FACTOR = 0.85 
DEGRADATION_RATE = 0.02 # افت ۲ درصد

# ================== توابع هوشمند ==================
def suggest_system(area):
    panel_watts = 550
    panel_area = 2.6 
    count = math.floor((area * 0.8) / panel_area)
    capacity_kw = (count * panel_watts) / 1000
    
    if capacity_kw <= 5: inverter_size = 5
    elif capacity_kw <= 10: inverter_size = 10
    elif capacity_kw <= 20: inverter_size = 20
    else: inverter_size = math.ceil(capacity_kw / 5) * 5
    
    return {
        "count": count,
        "capacity": capacity_kw,
        "panel_name": "550W Mono PERC",
        "inverter_name": f"{inverter_size}kW متصل به شبکه"
    }

# ================== دکمه محاسبه ==================
if st.button("محاسبه درآمد و تجهیزات", type="primary"):
    
    sys_info = suggest_system(roof_area)
    
    if sys_info["count"] < 4:
        st.warning("⚠️ متراژ برای احداث نیروگاه اقتصادی کمی پایین است.")
    
    # --- 1. محاسبات فنی ---
    with st.spinner("⚙️ در حال شبیه‌سازی..."):
        loc = Location(LAT, LON, tz='Asia/Tehran', altitude=1200)
        times = pd.date_range("2024-01-01", "2024-12-31 23:00", freq="h", tz="Asia/Tehran")
        weather = loc.get_clearsky(times)
        
        system = PVSystem(
            surface_tilt=tilt_angle, surface_azimuth=180,
            module_parameters={"pdc0": 550, "gamma_pdc": -0.0035},
            inverter_parameters={"pdc0": sys_info["capacity"]*1000, "eta_inv_nom": 0.97},
            temperature_model_parameters=TEMPERATURE_MODEL_PARAMETERS["sapm"]["open_rack_glass_glass"],
            modules_per_string=sys_info["count"], strings_per_inverter=1,
            losses_parameters={'soiling': 3, 'shading': 2}
        )
        
        mc = ModelChain(system, loc, aoi_model="physical", spectral_model="no_loss")
        mc.run_model(weather)
        
        ideal_ac = mc.results.ac.sum() / 1000
        real_ac_annual = ideal_ac * CLOUD_LOSS_FACTOR

    # --- 2. محاسبات مالی ---
    data = []
    cumulative = 0
    inflation_mult = 1 + INFLATION
    
    for year in range(1, 21):
        degradation = 1 - ((year - 1) * DEGRADATION_RATE)
        prod = real_ac_annual * degradation
        rate = BASE_RATE * (inflation_mult ** (year-1))
        income = prod * rate
        cumulative += income
        
        data.append({
            "سال": year,
            "درآمد (تومان)": round(income),
            "تولید (kWh)": round(prod)
        })
        
    df = pd.DataFrame(data)

    # ================== نمایش خروجی ==================
    st.markdown("---")
    
    st.subheader("🛠️ سیستم پیشنهادی")
    c1, c2, c3 = st.columns(3)
    c1.info(f"📦 **تعداد پنل:**\n\n {sys_info['count']} عدد")
    c2.info(f"⚡ **ظرفیت:**\n\n {sys_info['capacity']:.2f} کیلووات")
    c3.info(f"🔌 **اینورتر:**\n\n {sys_info['inverter_name']}")

    st.subheader("💰 برآورد درآمد")
    m1, m2, m3 = st.columns(3)
    m1.metric("تولید واقعی (سال اول)", f"{int(real_ac_annual):,} kWh")
    m2.metric("درآمد سال اول", f"{int(data[0]['درآمد (تومان)']):,} تومان")
    m3.metric("مجموع درآمد ۲۰ ساله", f"{int(cumulative/1e9):,} میلیارد تومان")
    
    st.caption(f"⚠️ محاسبات با در نظر گرفتن ۲٪ افت سالانه و ۱۵٪ افت شرایط محیطی انجام شده است.")

    st.subheader("📈 نمودار درآمد سالانه")
    
    # رسم نمودار با استریم‌لیت (که فونت CSS را به ارث می‌برد)
    chart_data = df.set_index("سال")[["درآمد (تومان)"]]
    st.line_chart(chart_data, color="#FF4B4B")
    
    with st.expander("مشاهده جدول دقیق"):
        st.dataframe(df.style.format("{:,}"))