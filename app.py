import os
import json
import re
import random
import warnings
from datetime import datetime
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv

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

# Tự động xác định mùa thực tế tại Hà Nội / Việt Nam
def get_current_hanoi_season():
    month = datetime.now().month
    if month in [3, 4, 5]:
        return "Mùa Xuân (Thời tiết ấm áp, dạo phố ngắm hoa nở)"
    elif month in [6, 7, 8]:
        return "Mùa Hè (Thời tiết nắng ấm, nhiều hoạt động sôi động)"
    elif month in [9, 10, 11]:
        return "Mùa Thu (Thời tiết mát mẻ, dễ chịu, rất đẹp để đi du lịch)"
    else:
        return "Mùa Đông (Thời tiết se lạnh, thích hợp du lịch núi hoặc ngắm cảnh)"

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

# --- SIDEBAR: BỘ LỌC TÌM KIẾM DÀNH CHO NGƯỜI DÙNG ---
with st.sidebar:
    st.header("🎯 Bộ Lọc Tìm Kiếm")

    if app_mode == "🍲 Khám Phá Ẩm Thực":
        selected_district = st.selectbox(
            "📍 Khu vực (Quận):",
            ["Tất cả Hà Nội", "Hoàn Kiếm & Phố Cổ", "Ba Đình", "Đống Đa", "Hai Bà Trưng", "Cầu Giấy", "Tây Hồ", "Thanh Xuân", "Nam Từ Liêm", "Bắc Từ Liêm", "Hoàng Mai", "Long Biên", "Hà Đông"]
        )
        selected_meal = st.selectbox(
            "⏰ Bữa ăn trong ngày:",
            ["Mọi bữa ăn", "Bữa sáng (6h - 10h)", "Bữa trưa (10h - 14h)", "Bữa xế / Ăn vặt (14h - 18h)", "Bữa tối (18h - 22h)", "Ăn đêm (Sau 22h)"]
        )
        selected_category = st.selectbox(
            "🍜 Thể loại món ăn:",
            ["Tất cả loại món", "Bún / Phở / Miến", "Lẩu / Nướng", "Ốc / Ăn vặt", "Steak / Món Âu", "Cơm / Món Việt", "Trà chanh / Cafe / Tráng miệng"]
        )
        selected_vibe = st.selectbox(
            "✨ Dịp / Phong cách:",
            ["Mọi phong cách", "Local truyền thống / Bình dân", "Hẹn hò lãng mạn / Riêng tư", "Tụ tập bạn bè / Nhậu", "Ăn đêm / Mở muộn", "Sang trọng / Fine Dining"]
        )
        selected_budget = st.select_slider(
            "💰 Mức ngân sách / người:",
            options=["Mọi mức giá", "Sinh viên (< 50k)", "Bình dân (50k - 150k)", "Khá (150k - 300k)", "Sang chảnh (> 300k)"]
        )
        btn_filter_search = st.button("✨ Khám Phá Theo Bộ Lọc", use_container_width=True, type="primary")

    elif app_mode == "🎡 Địa Điểm Đi Chơi & Giải Trí":
        selected_district = st.selectbox(
            "📍 Khu vực (Quận):",
            ["Tất cả Hà Nội", "Hoàn Kiếm & Phố Cổ", "Ba Đình", "Đống Đa", "Hai Bà Trưng", "Cầu Giấy", "Tây Hồ", "Thanh Xuân", "Nam Từ Liêm", "Bắc Từ Liêm", "Hoàng Mai", "Long Biên", "Hà Đông"]
        )
        selected_activity_type = st.selectbox(
            "🎭 Loại hình đi chơi / Giải trí:",
            ["Tất cả loại hình", "Cafe view đẹp / Check-in", "Công viên / Không gian xanh", "Bảo tàng / Di tích lịch sử", "Khu vui chơi / Game Center", "Phố bộ hành / Chợ đêm", "Hồ Tây / Hẹn hò lãng mạn", "Bar / Pub / Chill đêm"]
        )
        selected_companion = st.selectbox(
            "👥 Đối tượng đi cùng:",
            ["Mọi đối tượng", "Đi một mình / Yên tĩnh", "Hẹn hò cặp đôi", "Nhóm bạn đông người", "Gia đình có trẻ nhỏ"]
        )
        selected_cost = st.select_slider(
            "💰 Mức chi phí dự kiến:",
            options=["Mọi mức giá", "Miễn phí (0đ)", "Tiết kiệm (< 50k)", "Vừa phải (50k - 200k)", "Cao cấp (> 200k)"]
        )
        btn_filter_search = st.button("✨ Khám Phá Theo Bộ Lọc", use_container_width=True, type="primary")

    elif app_mode == "🗓️ Lịch Trình Tự Động (Theo Mùa & Thời Gian Thật)":
        selected_district = st.selectbox(
            "📍 Khu vực (Quận):",
            ["Tất cả Hà Nội", "Hoàn Kiếm & Phố Cổ", "Ba Đình", "Đống Đa", "Hai Bà Trưng", "Cầu Giấy", "Tây Hồ", "Thanh Xuân", "Nam Từ Liêm", "Bắc Từ Liêm", "Hoàng Mai", "Long Biên", "Hà Đông"]
        )
        selected_day_type = st.selectbox(
            "📅 Ngày đi chơi:",
            ["Tự động (Hôm nay)", "Ngày trong tuần (T2 - T6)", "Cuối tuần (T7 - CN / Phố đi bộ)"]
        )
        selected_duration = st.selectbox(
            "⏱️ Thời lượng chuyến đi:",
            ["Cả ngày (Sáng ➔ Tối)", "Buổi Sáng & Trưa (7h - 13h)", "Buổi Chiều & Tối (14h - 21h)", "Tối & Ăn Đêm (18h - 24h)"]
        )
        selected_season_input = st.selectbox(
            "🍂 Mùa trong năm:",
            ["Tự động (Theo mùa thật hiện tại)", "Mùa Thu Hà Nội (Đẹp nhất)", "Mùa Hè (Sôi động / Hồ Tây)", "Mùa Đông (Se lạnh / Đồ nướng lẩu)", "Mùa Xuân (Dạo phố / Chơi Tết)"]
        )
        selected_vibe_itinerary = st.selectbox(
            "🎨 Phong cách trải nghiệm:",
            ["Chill & Thư giãn", "Check-in & Sống ảo", "Ẩm thực & Food Tour", "Văn hóa & Lịch sử Phố Cổ", "Hẹn hò lãng mạn cặp đôi"]
        )
        btn_filter_search = st.button("🎲 Tạo Lịch Trình Ngẫu Nhiên", use_container_width=True, type="primary")

    else: # MENU 4: Cẩm nang du lịch trọn gói
        selected_origin = st.selectbox(
            "📍 Nơi khởi hành (Điểm đi):",
            ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Bắc Ninh", "Khác"]
        )
        selected_duration_guide = st.selectbox(
            "⏱️ Thời gian chuyến đi:",
            ["3 ngày 2 đêm", "2 ngày 1 đêm", "1 ngày (Đi trong ngày)", "4 ngày 3 đêm", "5 ngày 4 đêm"]
        )
        selected_time_guide = st.selectbox(
            "📅 Thời điểm đi:",
            ["Tự động (Theo tháng 8 hiện tại)", "Tháng này (Thời tiết thật)", "Mùa Xuân", "Mùa Hè", "Mùa Thu", "Mùa Đông"]
        )
        selected_companion_guide = st.selectbox(
            "👥 Bạn đồng hành:",
            ["Hẹn hò cặp đôi", "Nhóm bạn trẻ / Phượt", "Gia đình / Trẻ nhỏ", "Đi một mình (Solo travel)"]
        )
        selected_budget_guide = st.select_slider(
            "💰 Ngân sách chuyến đi:",
            options=["Tiết kiệm", "Phổ thông / Tiêu chuẩn", "Sang chảnh / Resort"]
        )
        btn_filter_search = st.button("🧳 Lên Cẩm Nang Du Lịch", use_container_width=True, type="primary")
    
    st.markdown("---")
    
    # Danh sách đã lưu
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


# --- HÀM GỌI AI PHÂN TÍCH (ẨN TRONG BACKGROUND) ---
def search_ai_recommendations(mode, query_text, district, cat_or_type, extra1, extra2, budget_or_cost, api_key_val, model_name="gemini-3.6-flash"):
    import time

    models_to_try = [model_name]
    fallback_candidates = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    for m in fallback_candidates:
        if m not in models_to_try:
            models_to_try.append(m)

    configs_to_try = [
        ("Chế độ 1: Grounding", [{"google_search": {}}]),
        ("Chế độ 2: Knowledge Base", None)
    ]

    client = genai.Client(api_key=api_key_val)

    if mode == "food":
        prompt = f"""
        Bạn là một chuyên gia ẩm thực bản địa sành sỏi tại Hà Nội.
        Nhiệm vụ của bạn: Tìm kiếm và tổng hợp các quán ăn ngon, chuẩn vị, nổi tiếng tại Hà Nội theo các bộ lọc tiêu chí sau:
        
        - Từ khóa / Món yêu cầu: "{query_text if query_text.strip() else 'Các quán ăn nổi tiếng chuẩn vị'}"
        - Khu vực ưu tiên: {district}
        - Bữa ăn trong ngày: {extra1}
        - Thể loại món ăn: {cat_or_type}
        - Dịp / Không khí: {extra2}
        - Ngân sách dự kiến: {budget_or_cost}

        Yêu cầu quan trọng:
        1. Tìm từ 3 đến 6 quán ăn ngon, chuẩn vị, chất lượng thật sự được người bản địa (local) và review đánh giá cao phù hợp với các bộ lọc trên.
        2. Tóm tắt trung thực cả điểm khen và điểm lưu ý/hạn chế (nếu có: đông phải xếp hàng, chỗ để xe hẹp,...).
        3. Xuất kết quả bắt buộc ở định dạng JSON thuần túy (không markdown bọc ngoài, không text thừa) là một danh sách các Object theo mẫu:
        [
          {{
            "name": "Tên quán ăn",
            "district": "Quận (ví dụ: Hoàn Kiếm)",
            "address": "Địa chỉ cụ thể kèm ngõ/phố",
            "price_range": "Khoảng giá (VNĐ)",
            "signature_dishes": "Các món nổi bật nhất định phải thử",
            "review_summary": "Tóm tắt review từ TikTok/FB/Google (vị nước dùng, độ tươi, phục vụ...)",
            "pros": "Điểm cộng lớn nhất",
            "cons": "Điểm trừ hoặc lưu ý khi đến quán (chờ lâu, gửi xe...)",
            "score": "Điểm đánh giá trung bình (ví dụ: 4.6/5.0)"
          }}
        ]
        """
    elif mode == "travel":
        prompt = f"""
        Bạn là một hướng dẫn viên du lịch và chuyên gia trải nghiệm bản địa sành sỏi tại Hà Nội.
        Nhiệm vụ của bạn: Tìm kiếm và tổng hợp các địa điểm đi chơi, giải trí, check-in hot nhất tại Hà Nội theo các bộ lọc tiêu chí sau:
        
        - Từ khóa / Yêu cầu tìm kiếm: "{query_text if query_text.strip() else 'Các địa điểm đi chơi hot nhất'}"
        - Khu vực ưu tiên: {district}
        - Loại hình giải trí: {cat_or_type}
        - Đối tượng đi cùng: {extra1}
        - Chi phí dự kiến: {budget_or_cost}

        Yêu cầu quan trọng:
        1. Tìm từ 3 đến 6 địa điểm đi chơi, tham quan, cafe check-in hoặc giải trí thật sự hấp dẫn và nổi tiếng được giới trẻ & local đánh giá cao.
        2. Tóm tắt trung thực trải nghiệm thực tế, góc sống ảo/hoạt động nên thử và các lưu ý (vé gửi xe, giờ mở cửa, độ đông đúc...).
        3. Xuất kết quả bắt buộc ở định dạng JSON thuần túy (không markdown bọc ngoài, không text thừa) là một danh sách các Object theo mẫu:
        [
          {{
            "name": "Tên địa điểm đi chơi",
            "district": "Quận (ví dụ: Tây Hồ)",
            "address": "Địa chỉ cụ thể",
            "price_range": "Chi phí / Vé vào cửa (VNĐ)",
            "signature_activities": "Trải nghiệm / Góc check-in / Hoạt động nhất định phải thử",
            "review_summary": "Tóm tắt review không khí, không gian và trải nghiệm thực tế",
            "pros": "Điểm cộng lớn nhất (view đẹp, thoáng mát, sống ảo...)",
            "cons": "Điểm trừ hoặc lưu ý khi đến (đông cuối tuần, gửi xe xa...)",
            "score": "Điểm đánh giá trung bình (ví dụ: 4.7/5.0)"
          }}
        ]
        """
    elif mode == "itinerary":
        season_desc = get_current_hanoi_season() if "Tự động" in extra2 else extra2
        day_desc = datetime.now().strftime("Hôm nay (%A, %d/%m/%Y)") if "Tự động" in cat_or_type else cat_or_type
        
        prompt = f"""
        Bạn là một chuyên gia du lịch bản địa sành sỏi tại Hà Nội.
        Nhiệm vụ của bạn: Lên MỘT LỊCH TRÌNH ĐI CHƠI & ĂN UỐNG NGẪU NHIÊN, TỐI ƯU VÀ HẤP DẪN DÀNH CHO HÀ NỘI dựa theo thời tiết và mùa thực tế.
        
        - Khu vực ưu tiên: {district}
        - Ngày trong tuần: {day_desc}
        - Thời lượng chuyến đi: {extra1}
        - Mùa & Thời tiết: {season_desc}
        - Phong cách chuyến đi: {budget_or_cost}
        - Yêu cầu thêm: "{query_text if query_text.strip() else 'Tự động tạo lịch trình ngẫu nhiên độc đáo'}"

        Yêu cầu quan trọng:
        1. Thiết kế từ 3 đến 5 chặng dừng chân nối tiếp nhau hợp lý về thời gian, khoảng cách địa lý và thời tiết theo mùa tại Hà Nội.
        2. Kết hợp hài hòa giữa món ăn ngon bản địa + địa điểm đi chơi/cafe chill check-in.
        3. Xuất duy nhất một JSON Object thuần túy (không markdown bọc ngoài, không text thừa) theo mẫu:
        {{
          "itinerary_title": "Tên lịch trình hấp dẫn ngẫu nhiên",
          "season_vibe": "Đánh giá không khí mùa và lời khuyên chuẩn bị (trang phục, ô dù...)",
          "estimated_budget": "Mức ngân sách tổng dự kiến / người (VNĐ)",
          "timeline": [
            {{
              "time": "08:00 - 09:30",
              "activity_title": "Tên hoạt động / Điểm đến",
              "location": "Địa chỉ / Tên quán hoặc địa điểm cụ thể",
              "description": "Chi tiết trải nghiệm (món nên gọi hoặc góc sống ảo)",
              "pro_tip": "Mẹo local (ví dụ: gửi xe ở đâu, nên đi giờ nào...)"
            }}
          ]
        }}
        """
    else: # Mode: tour_guide (Menu 4)
        origin_loc = district
        dest_loc = cat_or_type
        duration_val = extra1
        time_val = get_current_hanoi_season() if "Tự động" in extra2 else extra2
        
        prompt = f"""
        Bạn là một chuyên gia du lịch hàng đầu và stylist tư vấn trang phục du lịch chuyên nghiệp.
        Nhiệm vụ: Lên MỘT BỘ CẨM NANG DU LỊCH TRỌN GÓI VÀ TỐI ƯU NHẤT khi du lịch từ nơi đi đến địa điểm du lịch.

        Thông tin chuyến đi:
        - Điểm khởi hành (Nơi đi): {origin_loc}
        - Điểm du lịch đến (Nơi đến): {dest_loc}
        - Thời gian chuyến đi: {duration_val}
        - Thời điểm / Mùa đi: {time_val}
        - Ngân sách & Bạn đồng hành: {budget_or_cost}
        - Yêu cầu thêm: "{query_text if query_text.strip() else 'Gợi ý du lịch tối ưu nhất'}"

        Yêu cầu quan trọng:
        1. Gợi ý cụ thể HÃNG XE / ĐƠN VỊ ĐẶT XE UY TÍN (kèm kinh nghiệm đặt vé và kênh đặt xe tốt nhất như Vexere, Hotline, Klook...).
        2. Gợi ý TOP 3 HOMESTAY / KHÁCH SẠN OK NHẤT tại điểm đến (Decor xinh, view ngắm cảnh đẹp, sát trung tâm, giá phòng hợp lý).
        3. LỊCH TRÌNH CHI TIẾT TỪNG NGÀY NỐI TIẾP TIỆN ĐƯỜNG DI CHUYỂN NHẤT (Sắp xếp theo thứ tự địa lý gần nhau từ điểm A ➔ điểm B ➔ điểm C để không bị ngược đường).
        4. Gợi ý Outfit phối màu cực ăn ảnh theo thời tiết thực tế.
        5. Gợi ý danh sách Quán ăn đặc sản nhất định phải thử kèm địa chỉ cụ thể.

        Yêu cầu xuất duy nhất MỘT JSON Object thuần túy (không markdown bọc ngoài, không text thừa) có cấu trúc chính xác sau:
        {{
          "trip_title": "Cẩm Nang Du Lịch (Tên Nơi Đến) Trọn Gói Từ (Tên Nơi Đi)",
          "weather_vibe": "Tóm tắt thời tiết, nhiệt độ thực tế tại nơi đến và lời khuyên chuẩn bị chung",
          "transportation": {{
            "vehicle_type": "Phương tiện di chuyển phù hợp nhất (Xe khách giường nằm Limousine / Máy bay / Tàu hỏa / Xe máy...)",
            "recommended_bus_lines": "Tên các Hãng xe / Hãng vận tải uy tín nổi tiếng (Ví dụ: Nhà xe Sao Việt, G8 Open Tour, Hà Sơn Hải Vân...)",
            "travel_time": "Thời gian di chuyển ước tính (Ví dụ: Khoảng 5 - 6 tiếng)",
            "ticket_price": "Mức giá vé / chi phí xe dự kiến (VNĐ)",
            "booking_tips": "Kinh nghiệm chọn hãng xe/chuyến xe, kênh đặt vé tiện lợi (Vexere, Klook, Hotline...) & giờ xuất phát tối ưu"
          }},
          "homestay_recommendations": [
            {{
              "name": "Tên Homestay / Khách sạn uy tín",
              "address": "Địa chỉ cụ thể tại điểm đến",
              "price_per_night": "Khoảng giá / đêm (VNĐ)",
              "highlight": "Điểm đắt giá nhất (Ví dụ: View thung lũng săn mây / Bể bơi vô cực / Decor phong cách Boho vintage...)",
              "review_summary": "Tóm tắt review thực tế từ khách đã ở"
            }}
          ],
          "outfit_guide": {{
            "style_name": "Phong cách ăn mặc phù hợp (Ví dụ: Boho / Vintage / Năng động check-in...)",
            "recommended_colors": ["Tên màu 1", "Tên màu 2", "Tên màu 3", "Tên màu 4"],
            "clothing_suggestions": "Gợi ý trang phục chi tiết phối đồ cho nam & nữ",
            "accessories": "Phụ kiện cần mang theo (Mũ, kính râm, giày climbing, ô gấp...)",
            "photo_tips": "Mẹo phối màu trang phục nổi bật nhất khi chụp ảnh tại địa điểm này"
          }},
          "day_by_day_itinerary": [
            {{
              "day_title": "Ngày 1: Tên chặng hành trình (Ví dụ: Khám phá Trung Tâm & Check-in Cafe tiện đường)",
              "activities": [
                {{
                  "time": "08:00 - 11:30",
                  "title": "Tên hoạt động / Điểm đến",
                  "location": "Địa chỉ / Tên địa danh cụ thể",
                  "description": "Chi tiết trải nghiệm",
                  "route_note": "Lưu ý di chuyển tiện đường (Ví dụ: Cách điểm ăn sáng 500m, trên cùng tuyến đường chính)",
                  "pro_tip": "Mẹo chụp ảnh / gửi xe / giờ tránh đông"
                }}
              ]
            }}
          ],
          "food_recommendations": [
            {{
              "name": "Tên quán ăn / Đặc sản",
              "address": "Địa chỉ cụ thể",
              "dishes": "Món đặc sản nên thử",
              "price_range": "Khoảng giá (VNĐ)"
            }}
          ],
          "estimated_total_cost": "Mức tổng chi phí dự kiến / người (VNĐ)"
        }}
        """

    for current_model in models_to_try:
        for mode_title, tools_config in configs_to_try:
            for attempt in range(2):
                try:
                    config_kwargs = {"temperature": 0.4 if mode in ["itinerary", "tour_guide"] else 0.3}
                    if tools_config:
                        config_kwargs["tools"] = tools_config

                    chat = client.chats.create(
                        model=current_model,
                        config=types.GenerateContentConfig(**config_kwargs)
                    )
                    response = chat.send_message(prompt)
                    
                    raw_text = response.text.strip()
                    cleaned_json = re.sub(r"^```json\s*", "", raw_text)
                    cleaned_json = re.sub(r"^```\s*", "", cleaned_json)
                    cleaned_json = re.sub(r"\s*```$", "", cleaned_json).strip()
                    
                    return json.loads(cleaned_json)
                except Exception as e:
                    err_str = str(e)
                    print(f"[DEBUG_LOG] {current_model} ({mode_title}) attempt {attempt+1} failed: {err_str}")
                    if "503" in err_str or "UNAVAILABLE" in err_str:
                        time.sleep(1)
                        continue
                    else:
                        break

    st.error("⚠️ **Hệ thống AI đang bận hoặc quá tải tạm thời từ Google. Vui lòng bấm thử lại sau vài giây!**")
    return None


# --- GIAO DIỆN HIỂN THỊ CHÍNH THEO MENU ---
if app_mode == "🍲 Khám Phá Ẩm Thực":
    st.markdown('<div class="sub-title">Khám phá các quán ăn ngon chuẩn vị theo bữa ăn, khu vực & ngân sách</div>', unsafe_allow_html=True)

    user_query = st.text_input(
        "Nhập món ăn hoặc từ khóa muốn tìm (Tùy chọn):",
        placeholder="Ví dụ: bún chả que tre nướng, phở bò sốt vang phố cổ, steak hẹn hò ấm cúng...",
        label_visibility="collapsed"
    )

    st.caption("💡 **Gợi ý món hot (Bấm để xem ngay):**")
    tag_cols = st.columns(5)
    quick_tags = [
        "🍜 Phở bò sốt vang phố cổ",
        "🧆 Bún chả que tre nướng",
        "🐚 Ốc luộc lá chanh đêm",
        "🍱 Bún đậu mắm tôm ngon",
        "🥩 Steak hẹn hò ấm cúng"
    ]
    selected_tag = None
    for i, tag in enumerate(quick_tags):
        with tag_cols[i]:
            if st.button(tag, key=f"food_tag_{i}", use_container_width=True):
                selected_tag = tag.split(" ", 1)[1]

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        btn_search = st.button("🔍 Khám Phá Quán Ăn", use_container_width=True, type="primary")
    with col_btn2:
        btn_random = st.button("🎲 Gợi Ý Bất Kỳ", use_container_width=True)

    if btn_random:
        random_prompts = [
            "Quán phở bò sốt vang nóng hổi chuẩn vị phố cổ",
            "Quán ốc luộc lá chanh nước chấm đậm đà đông khách",
            "Quán nướng vỉa hè sốt me/bơ tỏi ngon rẻ tụ tập bạn bè",
            "Bánh mì chảo đẫm pate trứng lòng đào cho bữa xế",
            "Nhà hàng pasta steak phong cách vintage ấm cúng để hẹn hò"
        ]
        user_query = random.choice(random_prompts)
        st.info(f"💡 AI đang gợi ý món: **{user_query}**")
        btn_search = True

    if selected_tag:
        user_query = selected_tag
        st.info(f"💡 Bạn đã chọn: **{user_query}**")
        btn_search = True

    should_search = btn_search or btn_filter_search

    if should_search:
        if not api_key:
            st.error("⚠️ Hệ thống đang bảo trì kết nối AI. Vui lòng thử lại sau!")
        else:
            filter_summary = f"Quận: {selected_district} | Bữa: {selected_meal} | Thể loại: {selected_category} | Giá: {selected_budget}"
            spinner_msg = f"🤖 AI đang tìm kiếm quán ăn phù hợp ({filter_summary})..."
                
            with st.spinner(spinner_msg):
                results = search_ai_recommendations("food", user_query, selected_district, selected_category, selected_meal, selected_vibe, selected_budget, api_key, default_model)
                if results:
                    st.session_state.food_results = results

    if st.session_state.food_results:
        st.markdown("---")
        st.subheader(f"✨ Gợi ý {len(st.session_state.food_results)} quán ăn phù hợp nhất:")
        
        for idx, item in enumerate(st.session_state.food_results):
            with st.container(border=True):
                col_info, col_action = st.columns([4, 1.2])
                
                with col_info:
                    st.markdown(f"### {idx+1}. {item.get('name', 'Quán ăn')} `⭐ {item.get('score', '4.5/5.0')}`")
                    st.markdown(f"📍 **Địa chỉ:** {item.get('address', 'Đang cập nhật')} *(Quận {item.get('district', '')})*")
                    st.markdown(f"💰 **Khoảng giá:** `{item.get('price_range', 'Đang cập nhật')}`")
                    st.markdown(f"🍽️ **Món nên gọi:** `{item.get('signature_dishes', '')}`")
                    st.markdown(f"💬 **Review tổng hợp:** {item.get('review_summary', '')}")
                    
                    col_p, col_c = st.columns(2)
                    with col_p:
                        st.success(f"👍 **Điểm cộng:** {item.get('pros', 'Đồ ăn tươi ngon')}")
                    with col_c:
                        st.warning(f"⚠️ **Lưu ý:** {item.get('cons', 'Không có')}")

                with col_action:
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={item.get('name', '')}+{item.get('address', '')}".replace(" ", "+")
                    st.link_button("🗺️ Mở Google Maps", maps_url, use_container_width=True)
                    
                    is_saved = any(f.get('name') == item.get('name') for f in st.session_state.favorites)
                    if not is_saved:
                        if st.button("⭐ Lưu quán", key=f"save_food_{idx}", use_container_width=True):
                            st.session_state.favorites.append(item)
                            st.rerun()
                    else:
                        st.caption("✅ Đã lưu vào danh sách")

elif app_mode == "🎡 Địa Điểm Đi Chơi & Giải Trí":
    st.markdown('<div class="sub-title">Khám phá địa điểm đi chơi, cafe view đẹp, khu giải trí & check-in hot nhất Hà Nội</div>', unsafe_allow_html=True)

    user_query = st.text_input(
        "Nhập địa điểm hoặc từ khóa trải nghiệm muốn tìm (Tùy chọn):",
        placeholder="Ví dụ: cafe chill Hồ Tây, bảo tàng nghệ thuật check-in, phố đi bộ đêm...",
        label_visibility="collapsed"
    )

    st.caption("💡 **Gợi ý điểm đến hot (Bấm để xem ngay):**")
    tag_cols = st.columns(5)
    quick_travel_tags = [
        "☕ Cafe chill ngắm Hồ Tây",
        "🏛️ Bốt Hàng Đậu & Phố Cổ",
        "🚲 Đạp xe Hồ Tây hoàng hôn",
        "🎨 Bảo tàng Mỹ thuật check-in",
        "🌌 Phố đi bộ Hồ Gươm đêm"
    ]
    selected_tag = None
    for i, tag in enumerate(quick_travel_tags):
        with tag_cols[i]:
            if st.button(tag, key=f"travel_tag_{i}", use_container_width=True):
                selected_tag = tag.split(" ", 1)[1]

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        btn_search = st.button("🔍 Khám Phá Địa Điểm", use_container_width=True, type="primary")
    with col_btn2:
        btn_random = st.button("🎲 Gợi Ý Bất Kỳ", use_container_width=True)

    if btn_random:
        random_travel_prompts = [
            "Quán cafe rooftop view ngắm trọn Hồ Tây hoàng hôn",
            "Bảo tàng Mỹ thuật Việt Nam kiến trúc Pháp cổ check-in đẹp",
            "Cung thiếu nhi Hà Nội mới phong cách hiện đại độc lạ",
            "Tổ hợp giải trí Complex 01 Tây Sơn không gian nghệ thuật",
            "Phố sách Hà Nội yên tĩnh đọc sách và chụp ảnh"
        ]
        user_query = random.choice(random_travel_prompts)
        st.info(f"💡 AI đang gợi ý điểm đến: **{user_query}**")
        btn_search = True

    if selected_tag:
        user_query = selected_tag
        st.info(f"💡 Bạn đã chọn: **{user_query}**")
        btn_search = True

    should_search = btn_search or btn_filter_search

    if should_search:
        if not api_key:
            st.error("⚠️ Hệ thống đang bảo trì kết nối AI. Vui lòng thử lại sau!")
        else:
            filter_summary = f"Quận: {selected_district} | Loại hình: {selected_activity_type} | Chi phí: {selected_cost}"
            spinner_msg = f"🤖 AI đang tìm kiếm địa điểm đi chơi phù hợp ({filter_summary})..."
                
            with st.spinner(spinner_msg):
                results = search_ai_recommendations("travel", user_query, selected_district, selected_activity_type, selected_companion, None, selected_cost, api_key, default_model)
                if results:
                    st.session_state.travel_results = results

    if st.session_state.travel_results:
        st.markdown("---")
        st.subheader(f"✨ Gợi ý {len(st.session_state.travel_results)} địa điểm đi chơi phù hợp nhất:")
        
        for idx, item in enumerate(st.session_state.travel_results):
            with st.container(border=True):
                col_info, col_action = st.columns([4, 1.2])
                
                with col_info:
                    st.markdown(f"### {idx+1}. {item.get('name', 'Địa điểm')} `⭐ {item.get('score', '4.7/5.0')}`")
                    st.markdown(f"📍 **Địa chỉ:** {item.get('address', 'Đang cập nhật')} *(Quận {item.get('district', '')})*")
                    st.markdown(f"🎟️ **Vé / Chi phí:** `{item.get('price_range', 'Đang cập nhật')}`")
                    st.markdown(f"🎯 **Trải nghiệm nên thử:** `{item.get('signature_activities', '')}`")
                    st.markdown(f"💬 **Review không gian:** {item.get('review_summary', '')}")
                    
                    col_p, col_c = st.columns(2)
                    with col_p:
                        st.success(f"👍 **Điểm cộng:** {item.get('pros', 'Không gian thoáng mát')}")
                    with col_c:
                        st.warning(f"⚠️ **Lưu ý:** {item.get('cons', 'Không có')}")

                with col_action:
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={item.get('name', '')}+{item.get('address', '')}".replace(" ", "+")
                    st.link_button("🗺️ Mở Google Maps", maps_url, use_container_width=True)
                    
                    is_saved = any(f.get('name') == item.get('name') for f in st.session_state.favorites)
                    if not is_saved:
                        if st.button("⭐ Lưu địa điểm", key=f"save_travel_{idx}", use_container_width=True):
                            st.session_state.favorites.append(item)
                            st.rerun()
                    else:
                        st.caption("✅ Đã lưu vào danh sách")

elif app_mode == "🗓️ Lịch Trình Tự Động (Theo Mùa & Thời Gian Thật)":
    st.markdown('<div class="sub-title">Tự động thiết kế lịch trình đi chơi & ăn uống trọn gói ngẫu nhiên theo mùa và thời gian thực Hà Nội</div>', unsafe_allow_html=True)

    current_season_text = get_current_hanoi_season()
    st.info(f"🌿 **Thời tiết & Mùa hiện tại ở Hà Nội:** {current_season_text}")

    user_query = st.text_input(
        "Nhập mong muốn lịch trình tùy chọn (Tùy chọn):",
        placeholder="Ví dụ: lịch trình chill phố cổ ngày thu, tour ẩm thực tối thứ 7, hẹn hò ngắm hoàng hôn...",
        label_visibility="collapsed"
    )

    st.caption("💡 **Gợi ý chủ đề hot (Bấm để tạo ngay):**")
    tag_cols = st.columns(5)
    quick_itin_tags = [
        "🍂 Lịch trình Mùa Thu Phố Cổ",
        "🚲 Lịch trình Chiều Tối Hồ Tây",
        "🍜 Food Tour Bún Phở 1 Ngày",
        "📸 Check-in Sống Ảo Hà Nội",
        "🕯️ Hẹn Hò Lãng Mạn Tối CN"
    ]
    selected_tag = None
    for i, tag in enumerate(quick_itin_tags):
        with tag_cols[i]:
            if st.button(tag, key=f"itin_tag_{i}", use_container_width=True):
                selected_tag = tag.split(" ", 1)[1]

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        btn_search = st.button("🎲 Tạo Lịch Trình Ngẫu Nhiên", use_container_width=True, type="primary")
    with col_btn2:
        btn_random = st.button("✨ Đổi Chủ Đề Ngẫu Nhiên", use_container_width=True)

    if btn_random:
        random_itin_prompts = [
            "Một ngày mùa thu dạo chơi phố cổ Hà Nội và thưởng thức cafe trứng",
            "Lịch trình chiều tối chill Hồ Tây đạp xe và ngắm hoàng hôn",
            "Tour khám phá bảo tàng nghệ thuật và cafe vintage lãng mạn",
            "Hành trình săn đồ ăn đêm và trải nghiệm phố đi bộ",
            "Lịch trình hẹn hò cặp đôi ấm cúng ăn steak và ngắm thành phố"
        ]
        user_query = random.choice(random_itin_prompts)
        st.info(f"💡 AI đang lên lịch trình: **{user_query}**")
        btn_search = True

    if selected_tag:
        user_query = selected_tag
        st.info(f"💡 Bạn đã chọn: **{user_query}**")
        btn_search = True

    should_search = btn_search or btn_filter_search

    if should_search:
        if not api_key:
            st.error("⚠️ Hệ thống đang bảo trì kết nối AI. Vui lòng thử lại sau!")
        else:
            spinner_msg = f"🤖 AI đang lên lịch trình tối ưu ngẫu nhiên cho bạn..."
                
            with st.spinner(spinner_msg):
                results = search_ai_recommendations("itinerary", user_query, selected_district, selected_day_type, selected_duration, selected_season_input, selected_vibe_itinerary, api_key, default_model)
                if results and isinstance(results, dict):
                    st.session_state.itinerary_result = results

    if st.session_state.itinerary_result:
        itin = st.session_state.itinerary_result
        st.markdown("---")
        st.subheader(f"🚩 {itin.get('itinerary_title', 'Lịch Trình Đi Chơi & Ăn Uống Hà Nội')}")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.info(f"🌿 **Vibe & Thời tiết:** {itin.get('season_vibe', 'Thời tiết lý tưởng')}")
        with col_m2:
            st.success(f"💰 **Ngân sách tổng dự kiến:** `{itin.get('estimated_budget', '200.000 - 500.000 VNĐ / người')}`")

        st.markdown("### 🗺️ Chi Tiết Hành Trình Từng Chặng:")
        
        timeline_list = itin.get("timeline", [])
        for step_idx, step in enumerate(timeline_list):
            with st.container(border=True):
                col_t, col_act = st.columns([1.2, 4])
                with col_t:
                    st.markdown(f"#### ⏰ `{step.get('time', '')}`")
                    st.caption(f"Chặng {step_idx+1}/{len(timeline_list)}")
                with col_act:
                    st.markdown(f"### {step_idx+1}. {step.get('activity_title', '')}")
                    st.markdown(f"📍 **Địa điểm:** {step.get('location', '')}")
                    st.markdown(f"📝 **Trải nghiệm:** {step.get('description', '')}")
                    if step.get('pro_tip'):
                        st.info(f"💡 **Mẹo local:** {step.get('pro_tip')}")
                    
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={step.get('location', '')}".replace(" ", "+")
                    st.link_button("🗺️ Mở vị trí Google Maps", maps_url)

else: # MENU 4: 🧳 Cẩm Nang Du Lịch Full (Outfit + Phương Tiện + Lịch Trình)
    st.markdown('<div class="sub-title">Cẩm nang du lịch trọn gói: Gợi ý Đặt xe, Top Homestay ok nhất, Outfit & Lịch trình chi tiết tiện đường</div>', unsafe_allow_html=True)

    col_loc1, col_loc2 = st.columns(2)
    with col_loc1:
        origin_input = st.text_input("📍 Điểm khởi hành (Nơi đi):", value="Hà Nội")
    with col_loc2:
        dest_input = st.text_input("🎯 Điểm du lịch muốn đến (Nơi đến):", value="Sapa")

    st.caption("💡 **Gợi ý điểm đến du lịch nổi tiếng (Bấm để chọn nhanh):**")
    tag_cols = st.columns(5)
    quick_dest_tags = [
        "🏔️ Sapa",
        "🌾 Hà Giang",
        "🌊 Đà Nẵng - Hội An",
        "🌲 Đà Lạt",
        "🚣 Ninh Bình"
    ]
    selected_dest_tag = None
    for i, tag in enumerate(quick_dest_tags):
        with tag_cols[i]:
            if st.button(tag, key=f"dest_tag_{i}", use_container_width=True):
                selected_dest_tag = tag.split(" ", 1)[1]

    if selected_dest_tag:
        dest_input = selected_dest_tag
        st.info(f"💡 Đã chọn điểm đến: **{dest_input}**")

    user_query = st.text_input(
        "Nhập mong muốn chuyến đi tùy chọn (Tùy chọn):",
        placeholder="Ví dụ: săn mây Sapa, nghỉ dưỡng biển Đà Nẵng, chụp ảnh cổ phục Hội An...",
        label_visibility="collapsed"
    )

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        btn_search = st.button("🧳 Lên Cẩm Nang Du Lịch Full", use_container_width=True, type="primary")
    with col_btn2:
        btn_random = st.button("🎲 Gợi Ý Chuyến Đi Bất Kỳ", use_container_width=True)

    if btn_random:
        random_destinations = [
            ("Hà Nội", "Sapa", "Săn mây Fansipan và check-in cafe bản Cát Cát"),
            ("Hà Nội", "Hà Giang", "Phượt mạo hiểm đèo Mã Pí Lèng và ngắm dòng sông Nho Quế"),
            ("Hà Nội", "Đà Nẵng", "Nghỉ dưỡng biển Mỹ Khê và khám phá phố cổ Hội An đêm"),
            ("TP. Hồ Chí Minh", "Đà Lạt", "Chill cafe sương mờ và chụp ảnh phong cách Vintage"),
            ("Hà Nội", "Ninh Bình", "Chèo thuyền Tràng An và leo núi Múa ngắm toàn cảnh")
        ]
        chosen = random.choice(random_destinations)
        origin_input, dest_input, user_query = chosen
        st.info(f"💡 AI gợi ý chuyến đi: **{origin_input} ➔ {dest_input}** ({user_query})")
        btn_search = True

    should_search = btn_search or btn_filter_search

    if should_search:
        if not api_key:
            st.error("⚠️ Hệ thống đang bảo trì kết nối AI. Vui lòng thử lại sau!")
        else:
            spinner_msg = f"🤖 AI đang tổng hợp Cẩm Nang Du Lịch ({origin_input} ➔ {dest_input}), gợi ý Đặt xe, Homestay & Lịch trình tiện đường..."
                
            with st.spinner(spinner_msg):
                results = search_ai_recommendations(
                    "tour_guide",
                    user_query,
                    origin_input,
                    dest_input,
                    selected_duration_guide,
                    selected_time_guide,
                    f"{selected_companion_guide} - Ngân sách: {selected_budget_guide}",
                    api_key,
                    default_model
                )
                if results and isinstance(results, dict):
                    st.session_state.tour_guide_result = results

    if st.session_state.tour_guide_result:
        guide = st.session_state.tour_guide_result
        st.markdown("---")
        st.subheader(f"🧳 {guide.get('trip_title', 'Cẩm Nang Du Lịch Trọn Gói')}")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.info(f"🌤️ **Thời tiết & Khuyên dùng:** {guide.get('weather_vibe', 'Thời tiết thuận lợi')}")
        with col_g2:
            st.success(f"💰 **Chi phí dự kiến tổng cộng:** `{guide.get('estimated_total_cost', '2.000.000 - 4.000.000 VNĐ / người')}`")

        # Khung Phương tiện di chuyển & Outfit
        col_trans, col_outfit = st.columns(2)
        
        with col_trans:
            with st.container(border=True):
                st.markdown("### 🛞 Phương Tiện Di Chuyển & Gợi Ý Đặt Xe")
                trans = guide.get("transportation", {})
                st.markdown(f"🚌 **Phương tiện khuyên dùng:** `{trans.get('vehicle_type', 'Xe giường nằm / Máy bay')}`")
                st.markdown(f"🚍 **Hãng xe / Đơn vị uy tín:** `{trans.get('recommended_bus_lines', 'Các nhà xe chất lượng cao')}`")
                st.markdown(f"⏱️ **Thời gian di chuyển:** `{trans.get('travel_time', 'Đang cập nhật')}`")
                st.markdown(f"🎟️ **Giá vé ước tính:** `{trans.get('ticket_price', 'Đang cập nhật')}`")
                st.info(f"💡 **Mẹo đặt vé & xuất phát:** {trans.get('booking_tips', 'Nên đặt vé trước 3-5 ngày qua Vexere hoặc hotline nhà xe')}")

        with col_outfit:
            with st.container(border=True):
                st.markdown("### 👗 Outfit & Phối Màu Trang Phục")
                outfit = guide.get("outfit_guide", {})
                st.markdown(f"💃 **Phong cách:** `{outfit.get('style_name', 'Vintage / Năng động')}`")
                
                colors = outfit.get("recommended_colors", [])
                color_badges_html = " ".join([f'<span class="color-badge">🎨 {c}</span>' for c in colors])
                st.markdown(f"🎨 **Tone màu cực ăn ảnh:** {color_badges_html}", unsafe_allow_html=True)
                
                st.markdown(f"🧥 **Gợi ý đồ mặc:** {outfit.get('clothing_suggestions', '')}")
                st.markdown(f"🧢 **Phụ kiện cần mang:** `{outfit.get('accessories', '')}`")
                st.success(f"📸 **Mẹo chụp ảnh đẹp:** {outfit.get('photo_tips', '')}")

        # Homestay & Khách sạn gợi ý ok nhất
        st.markdown("### 🏡 Top Homestay & Khách Sạn Uy Tín / View Đẹp Nhất:")
        hs_list = guide.get("homestay_recommendations", [])
        if hs_list:
            hs_cols = st.columns(min(len(hs_list), 3))
            for h_idx, hs in enumerate(hs_list):
                with hs_cols[h_idx % len(hs_cols)]:
                    with st.container(border=True):
                        st.markdown(f"#### 🏨 {hs.get('name', 'Homestay')}")
                        st.caption(f"📍 {hs.get('address', '')}")
                        st.markdown(f"💰 **Giá phòng:** `{hs.get('price_per_night', 'Đang cập nhật')}`")
                        st.markdown(f"✨ **Điểm nổi bật:** {hs.get('highlight', '')}")
                        st.caption(f"💬 *Review:* {hs.get('review_summary', '')}")
                        maps_url = f"https://www.google.com/maps/search/?api=1&query={hs.get('name', '')}+{hs.get('address', '')}".replace(" ", "+")
                        st.link_button("🗺️ Mở Google Maps", maps_url, use_container_width=True)

        # Lịch trình chi tiết từng ngày tiện đường di chuyển
        st.markdown("### 🗓️ Lịch Trình Chi Tiết Từng Ngày (Tối Ưu Tiện Đường):")
        day_list = guide.get("day_by_day_itinerary", [])
        for day_idx, day_item in enumerate(day_list):
            with st.expander(f"📌 **{day_item.get('day_title', f'Ngày {day_idx+1}')}**", expanded=True):
                activities = day_item.get("activities", [])
                for act_idx, act in enumerate(activities):
                    col_at, col_ad = st.columns([1.2, 4])
                    with col_at:
                        st.markdown(f"⏰ `{act.get('time', '')}`")
                    with col_ad:
                        st.markdown(f"### {act_idx+1}. {act.get('title', '')}")
                        st.caption(f"📍 **Địa điểm:** {act.get('location', '')}")
                        st.write(f"📝 **Trải nghiệm:** {act.get('description', '')}")
                        
                        if act.get('route_note'):
                            st.caption(f"🚏 **Đường đi tiện lợi:** {act.get('route_note')}")
                        if act.get('pro_tip'):
                            st.info(f"💡 **Mẹo local:** {act.get('pro_tip')}")
                            
                        maps_url = f"https://www.google.com/maps/search/?api=1&query={act.get('title', '')}+{act.get('location', '')}".replace(" ", "+")
                        st.link_button("🗺️ Mở vị trí Google Maps", maps_url)
                        st.markdown("---")

        # Quán ăn & Đặc sản khuyên thử
        st.markdown("### 🍲 Quán Ăn Đặc Sản Nhất Định Phải Thử:")
        food_list = guide.get("food_recommendations", [])
        if food_list:
            food_cols = st.columns(min(len(food_list), 3))
            for f_idx, food in enumerate(food_list):
                with food_cols[f_idx % len(food_cols)]:
                    with st.container(border=True):
                        st.markdown(f"#### 🍽️ {food.get('name', 'Quán ăn')}")
                        st.caption(f"📍 {food.get('address', '')}")
                        st.markdown(f"😋 **Món ngon:** `{food.get('dishes', '')}`")
                        st.markdown(f"💰 `{food.get('price_range', '')}`")
                        maps_url = f"https://www.google.com/maps/search/?api=1&query={food.get('name', '')}+{food.get('address', '')}".replace(" ", "+")
                        st.link_button("🗺️ Mở Google Maps", maps_url, use_container_width=True)