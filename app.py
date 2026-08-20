import os
import warnings
import streamlit as st
from dotenv import load_dotenv

# Import các modules giao diện và helper
from modules.food_menu import render_food_sidebar, render_food_main
from modules.travel_menu import render_travel_sidebar, render_travel_main
from modules.itinerary_menu import render_itinerary_sidebar, render_itinerary_main
from modules.tour_guide_menu import render_tour_guide_sidebar, render_tour_guide_main

# Tắt cảnh báo từ SDK
warnings.filterwarnings("ignore")

# Tải biến môi trường từ tệp .env (nếu có)
load_dotenv(override=True)

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Hà Nội & Việt Nam Travel AI — Khám Phá & Du Lịch Trọn Gói",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS tạo giao diện hiện đại & ẩn các thành phần thừa
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    .stAppToolbar {display: none;}
    
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF8E53);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #555555;
        font-size: 1.05rem;
        margin-bottom: 1.2rem;
    }
    .color-badge {
        display: inline-block;
        padding: 4px 12px;
        margin: 3px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.9rem;
        background-color: #F0F2F6;
        color: #333333;
        border: 1px solid #DDDDDD;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo Session State
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "food_results" not in st.session_state:
    st.session_state.food_results = []
if "travel_results" not in st.session_state:
    st.session_state.travel_results = []
if "itinerary_result" not in st.session_state:
    st.session_state.itinerary_result = None
if "tour_guide_result" not in st.session_state:
    st.session_state.tour_guide_result = None

# Đọc cấu hình ngầm từ môi trường / Streamlit Secrets
api_key = os.getenv("GEMINI_API_KEY", "").strip()
if not api_key and hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"].strip()

default_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()


# --- CHỌN MENU DANH MỤC CHÍNH ---
st.markdown('<div class="main-title">🗺️ Khám Phá & Du Lịch AI</div>', unsafe_allow_html=True)
app_mode = st.radio(
    "Chọn danh mục khám phá:",
    options=[
        "🍲 Khám Phá Ẩm Thực",
        "🎡 Địa Điểm Đi Chơi & Giải Trí",
        "🗓️ Lịch Trình Tự Động (Theo Mùa & Thời Gian Thật)",
        "🧳 Cẩm Nang Du Lịch Full (Outfit + Phương Tiện + Lịch Trình)"
    ],
    horizontal=True
)

st.markdown("---")

# --- SIDEBAR: ĐIỀU HƯỚNG BỘ LỌC THEO MODULE ---
with st.sidebar:
    st.header("🎯 Bộ Lọc Tìm Kiếm")

    if app_mode == "🍲 Khám Phá Ẩm Thực":
        sidebar_data = render_food_sidebar()
    elif app_mode == "🎡 Địa Điểm Đi Chơi & Giải Trí":
        sidebar_data = render_travel_sidebar()
    elif app_mode == "🗓️ Lịch Trình Tự Động (Theo Mùa & Thời Gian Thật)":
        sidebar_data = render_itinerary_sidebar()
    else: # Menu 4
        sidebar_data = render_tour_guide_sidebar()

    st.markdown("---")
    
    # Danh sách địa điểm/quán ăn đã lưu
    st.subheader(f"⭐ Đã Lưu ({len(st.session_state.favorites)})")
    if st.session_state.favorites:
        for idx, fav in enumerate(st.session_state.favorites):
            with st.expander(f"**{idx+1}. {fav['name']}** ({fav.get('district', '')})"):
                st.caption(f"📍 Địa chỉ: {fav.get('address', '')}")
                if "signature_dishes" in fav:
                    st.caption(f"🍽️ Món ngon: {fav.get('signature_dishes', '')}")
                elif "signature_activities" in fav:
                    st.caption(f"🎡 Trải nghiệm: {fav.get('signature_activities', '')}")
                maps_url = f"https://www.google.com/maps/search/?api=1&query={fav.get('name', '')}+{fav.get('address', '')}".replace(" ", "+")
                st.link_button("🗺️ Mở Google Maps", maps_url, use_container_width=True)
                
        if st.button("🗑️ Xóa danh sách đã lưu", use_container_width=True):
            st.session_state.favorites = []
            st.rerun()
    else:
        st.caption("Chưa có địa điểm nào trong danh sách yêu thích.")


# --- ĐIỀU HƯỚNG GIAO DIỆN CHÍNH THEO MODULE ---
if app_mode == "🍲 Khám Phá Ẩm Thực":
    render_food_main(*sidebar_data, api_key=api_key, default_model=default_model)
elif app_mode == "🎡 Địa Điểm Đi Chơi & Giải Trí":
    render_travel_main(*sidebar_data, api_key=api_key, default_model=default_model)
elif app_mode == "🗓️ Lịch Trình Tự Động (Theo Mùa & Thời Gian Thật)":
    render_itinerary_main(*sidebar_data, api_key=api_key, default_model=default_model)
else: # Menu 4
    render_tour_guide_main(*sidebar_data, api_key=api_key, default_model=default_model)