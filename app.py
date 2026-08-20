import os
import json
import re
import random
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Tải biến môi trường từ tệp .env (nếu có)
load_dotenv(override=True)

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Hà Nội Food AI — Khám Phá Ẩm Thực Hà Nội",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS tạo giao diện hiện đại & thân thiện
st.markdown("""
<style>
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
</style>
""", unsafe_allow_html=True)

# Khởi tạo Session State
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []

# Đọc cấu hình từ môi trường / Secrets
env_api_key = os.getenv("GEMINI_API_KEY", "").strip()
if not env_api_key and hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
    env_api_key = st.secrets["GEMINI_API_KEY"].strip()

default_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()


# --- SIDEBAR: BỘ LỌC TÌM KIẾM DÀNH CHO NGƯỜI DÙNG ---
with st.sidebar:
    st.header("🎯 Bộ Lọc Tìm Kiếm")
    
    # Mục cấu hình thu gọn (chỉ mở ra khi chưa có API Key)
    with st.expander("⚙️ Cấu hình API Key", expanded=not bool(env_api_key)):
        user_api_key = st.text_input(
            "Gemini API Key:",
            value=env_api_key,
            type="password",
            help="Nhập API Key cá nhân từ Google AI Studio nếu ứng dụng chưa tự nhận chìa khóa."
        )
        if env_api_key:
            st.caption("✅ Đã sẵn sàng API Key từ Server / .env")

    api_key = user_api_key if user_api_key else env_api_key

    selected_district = st.selectbox(
        "📍 Khu vực (Quận):",
        ["Tất cả Hà Nội", "Hoàn Kiếm", "Ba Đình", "Đống Đa", "Hai Bà Trưng", "Cầu Giấy", "Tây Hồ", "Thanh Xuân", "Nam Từ Liêm", "Bắc Từ Liêm", "Hoàng Mai", "Long Biên", "Hà Đông"]
    )
    
    selected_vibe = st.selectbox(
        "✨ Dịp / Phong cách:",
        ["Mọi phong cách", "Local truyền thống / Bình dân", "Hẹn hò lãng mạn / Riêng tư", "Tụ tập bạn bè / Nhậu", "Ăn đêm / Mở muộn", "Ăn vặt / Trà chanh", "Sang trọng / Fine Dining"]
    )
    
    selected_budget = st.select_slider(
        "💰 Mức ngân sách / người:",
        options=["Mọi mức giá", "Sinh viên (< 50k)", "Bình dân (50k - 150k)", "Khá (150k - 300k)", "Sang chảnh (> 300k)"]
    )
    
    st.markdown("---")
    
    # Danh sách quán đã lưu
    st.subheader(f"⭐ Quán Đã Lưu ({len(st.session_state.favorites)})")
    if st.session_state.favorites:
        for idx, fav in enumerate(st.session_state.favorites):
            with st.expander(f"**{idx+1}. {fav['name']}** ({fav.get('district', '')})"):
                st.caption(f"📍 Địa chỉ: {fav.get('address', '')}")
                st.caption(f"🍽️ Món ngon: {fav.get('signature_dishes', '')}")
                maps_url = f"https://www.google.com/maps/search/?api=1&query={fav.get('name', '')}+{fav.get('address', '')}".replace(" ", "+")
                st.link_button("🗺️ Mở Google Maps", maps_url, use_container_width=True)
                
        if st.button("🗑️ Xóa danh sách đã lưu", use_container_width=True):
            st.session_state.favorites = []
            st.rerun()
    else:
        st.caption("Chưa có quán nào trong danh sách yêu thích.")


# --- HÀM GỌI AI PHÂN TÍCH (XỬ LÝ ẨN TRONG BACKGROUND) ---
def search_food_with_ai(query_text, district, vibe, budget, api_key_val, model_name="gemini-3.6-flash"):
    models_to_try = [model_name]
    fallback_candidates = ["gemini-3.6-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"]
    for m in fallback_candidates:
        if m not in models_to_try:
            models_to_try.append(m)

    last_error = None
    has_quota_error = False

    for current_model in models_to_try:
        try:
            client = genai.Client(api_key=api_key_val)
            
            prompt = f"""
            Bạn là một chuyên gia ẩm thực bản địa sành sỏi tại Hà Nội.
            Nhiệm vụ của bạn: Tìm kiếm và tổng hợp các review thực tế mới nhất trên Google Maps, TikTok, Food Reviewer Facebook, Threads về món ăn/yêu cầu sau:
            
            - Món ăn / Yêu cầu tìm kiếm: "{query_text}"
            - Khu vực ưu tiên: {district}
            - Dịp / Không khí: {vibe}
            - Ngân sách dự kiến: {budget}

            Yêu cầu quan trọng:
            1. Tìm từ 3 đến 6 quán ăn ngon, chuẩn vị, chất lượng thật sự được người bản địa (local) và review mạng đánh giá cao.
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
            
            response = client.models.generate_content(
                model=current_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    tools=[{"google_search": {}}]
                )
            )
            
            raw_text = response.text.strip()
            cleaned_json = re.sub(r"^```json\s*", "", raw_text)
            cleaned_json = re.sub(r"^```\s*", "", cleaned_json)
            cleaned_json = re.sub(r"\s*```$", "", cleaned_json).strip()
            
            return json.loads(cleaned_json)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                has_quota_error = True
            last_error = e
            continue

    # Thông báo lỗi thân thiện cho người dùng cuối
    if has_quota_error:
        st.error("⏳ **Hệ thống AI đang quá tải lượt tìm kiếm.** Vui lòng thử lại sau 1-2 phút!")
    else:
        st.error("⚠️ **Không thể kết nối dịch vụ AI vào lúc này.** Vui lòng thử lại sau!")
    return None


# --- GIAO DIỆN CHÍNH ---
st.markdown('<div class="main-title">🍲 Hà Nội Food AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Khám phá quán ăn ngon chuẩn vị theo review thời gian thực từ Google Maps, TikTok & Facebook</div>', unsafe_allow_html=True)

# Ô tìm kiếm chính
user_query = st.text_input(
    "Nhập món ăn hoặc từ khóa muốn tìm hôm nay:",
    placeholder="Ví dụ: bún chả que tre nướng, phở bò sốt vang phố cổ, steak hẹn hò ấm cúng...",
    label_visibility="collapsed"
)

# Gợi ý nhanh
st.caption("💡 **Gợi ý tìm nhanh:**")
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
        if st.button(tag, key=f"tag_{i}", use_container_width=True):
            selected_tag = tag.split(" ", 1)[1] # Bỏ emoji

col_btn1, col_btn2 = st.columns([3, 1])
with col_btn1:
    btn_search = st.button("🔍 Tìm Kiếm Ngay", use_container_width=True, type="primary")
with col_btn2:
    btn_random = st.button("🎲 Gợi Ý Bất Kỳ", use_container_width=True)

# Xử lý khi nhấn nút gợi ý ngẫu nhiên
if btn_random:
    random_prompts = [
        "Quán phở bò sốt vang nóng hổi chuẩn vị phố cổ",
        "Quán ốc luộc lá chanh nước chấm đậm đà đông khách",
        "Quán nướng vỉa hè sốt me/bơ tỏi ngon rẻ tụ tập bạn bè",
        "Bánh mì chảo đẫm pate trứng lòng đào cho bữa xế",
        "Nhà hàng pasta steak phong cách vintage ấm cúng để hẹn hò"
    ]
    user_query = random.choice(random_prompts)
    st.info(f"💡 AI đang tìm gợi ý: **{user_query}**")
    btn_search = True

if selected_tag:
    user_query = selected_tag
    st.info(f"💡 Bạn đã chọn: **{user_query}**")
    btn_search = True

# Thực hiện tìm kiếm
if btn_search:
    if not api_key:
        st.error("⚠️ Chưa nhận diện được API Key. Vui lòng mở mục **⚙️ Cấu hình API Key** ở menu bên trái để dán API Key hoặc tạo tệp `.env`.")
    elif not user_query.strip():
        st.warning("⚠️ Vui lòng nhập món ăn hoặc chọn gợi ý bạn muốn tìm!")
    else:
        with st.spinner("🤖 AI đang tổng hợp các review mới nhất trên TikTok, Google Maps và Facebook..."):
            results = search_food_with_ai(user_query, selected_district, selected_vibe, selected_budget, api_key, default_model)
            if results:
                st.session_state.search_results = results

# --- HIỂN THỊ KẾT QUẢ TÌM KIẾM ---
if st.session_state.search_results:
    st.markdown("---")
    st.subheader(f"✨ Gợi ý {len(st.session_state.search_results)} quán ăn phù hợp nhất:")
    
    for idx, item in enumerate(st.session_state.search_results):
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
                    if st.button("⭐ Lưu quán", key=f"save_{idx}", use_container_width=True):
                        st.session_state.favorites.append(item)
                        st.rerun()
                else:
                    st.caption("✅ Đã lưu vào danh sách")