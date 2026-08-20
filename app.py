import os
import json
import re
import random
import warnings
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Tắt cảnh báo không cần thiết từ SDK
warnings.filterwarnings("ignore")

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

    selected_category = st.selectbox(
        "🍜 Thể loại món ăn:",
        ["Tất cả loại món", "Bún / Phở / Miến", "Lẩu / Nướng", "Ốc / Ăn vặt", "Steak / Món Âu", "Cơm / Món Việt", "Trà chanh / Cafe / Tráng miệng"]
    )
    
    selected_vibe = st.selectbox(
        "✨ Dịp / Phong cách:",
        ["Mọi phong cách", "Local truyền thống / Bình dân", "Hẹn hò lãng mạn / Riêng tư", "Tụ tập bạn bè / Nhậu", "Ăn đêm / Mở muộn", "Ăn vặt / Trà chanh", "Sang trọng / Fine Dining"]
    )
    
    selected_budget = st.select_slider(
        "💰 Mức ngân sách / người:",
        options=["Mọi mức giá", "Sinh viên (< 50k)", "Bình dân (50k - 150k)", "Khá (150k - 300k)", "Sang chảnh (> 300k)"]
    )

    btn_filter_search = st.button("✨ Khám Phá Theo Bộ Lọc", use_container_width=True, type="primary")
    
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


# Theo dõi sự thay đổi của bộ lọc để tự động gợi ý
current_filter_state = (selected_district, selected_category, selected_vibe, selected_budget)
filter_changed = False

if "prev_filter_state" in st.session_state:
    if st.session_state.prev_filter_state != current_filter_state:
        filter_changed = True
st.session_state.prev_filter_state = current_filter_state


# --- HÀM GỌI AI PHÂN TÍCH (XỬ LÝ ẨN TRONG BACKGROUND) ---
def search_food_with_ai(query_text, district, category, vibe, budget, api_key_val, model_name="gemini-3.6-flash"):
    import time

    models_to_try = [model_name]
    fallback_candidates = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    for m in fallback_candidates:
        if m not in models_to_try:
            models_to_try.append(m)

    debug_logs = []
    masked_key = api_key_val[:6] + "..." + api_key_val[-4:] if len(api_key_val) > 10 else "Chưa có / Rỗng"
    debug_logs.append(f"🔑 **API Key đang dùng:** `{masked_key}`")

    # Chiến lược 2 chế độ: 1. Có Google Search Grounding -> 2. Cơ sở tri thức AI (khi bị Quota 429)
    configs_to_try = [
        ("Chế độ 1: Tìm kiếm mạng thời gian thực (Google Search Grounding)", [{"google_search": {}}]),
        ("Chế độ 2: Tri thức AI bản địa tích hợp (No Search Tool)", None)
    ]

    client = genai.Client(api_key=api_key_val)

    prompt = f"""
    Bạn là một chuyên gia ẩm thực bản địa sành sỏi tại Hà Nội.
    Nhiệm vụ của bạn: Tìm kiếm và tổng hợp các quán ăn ngon, chuẩn vị, nổi tiếng tại Hà Nội theo các bộ lọc tiêu chí sau:
    
    - Từ khóa / Món yêu cầu: "{query_text if query_text.strip() else 'Các quán ăn nổi tiếng chuẩn vị'}"
    - Khu vực ưu tiên: {district}
    - Thể loại món ăn: {category}
    - Dịp / Không khí: {vibe}
    - Ngân sách dự kiến: {budget}

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

    for current_model in models_to_try:
        for mode_title, tools_config in configs_to_try:
            # Thử tối đa 2 lần đối với lỗi quá tải tạm thời (503 UNAVAILABLE)
            for attempt in range(2):
                try:
                    config_kwargs = {"temperature": 0.3}
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
                    debug_logs.append(f"❌ Mô hình `{current_model}` ({mode_title} - Thử {attempt+1}) thất bại: `{err_str}`")
                    print(f"[DEBUG_LOG] {current_model} ({mode_title}) attempt {attempt+1} failed: {err_str}")
                    
                    # Nếu gặp lỗi 503 (Server quá tải tạm thời), đợi 1 giây rồi thử lại
                    if "503" in err_str or "UNAVAILABLE" in err_str:
                        time.sleep(1)
                        continue
                    else:
                        # Với lỗi 429 Quota hoặc 404, chuyển sang chế độ/mô hình tiếp theo ngay
                        break

    st.error("⚠️ **Hệ thống AI đang quá tải lượt gọi tạm thời từ Google. Vui lòng bấm thử lại sau vài giây!**")

    with st.expander("🛠️ Chi tiết nhật ký lỗi (Debug Logs)", expanded=True):
        for log in debug_logs:
            st.markdown(f"- {log}")
    return None


# --- GIAO DIỆN CHÍNH ---
st.markdown('<div class="main-title">🍲 Hà Nội Food AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Tự động gợi ý quán ăn ngon chuẩn vị theo Bộ lọc hoặc Tìm kiếm tùy chọn</div>', unsafe_allow_html=True)

# Ô tìm kiếm tùy chọn
user_query = st.text_input(
    "Nhập món ăn hoặc từ khóa muốn tìm (Tùy chọn - Không bắt buộc):",
    placeholder="Ví dụ: bún chả que tre nướng, phở bò sốt vang phố cổ, steak hẹn hò ấm cúng... (Hoặc chỉ cần chọn bộ lọc bên trái)",
    label_visibility="collapsed"
)

# Gợi ý nhanh
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
        if st.button(tag, key=f"tag_{i}", use_container_width=True):
            selected_tag = tag.split(" ", 1)[1] # Bỏ emoji

col_btn1, col_btn2 = st.columns([3, 1])
with col_btn1:
    btn_search = st.button("🔍 Khám Phá Quán Ăn", use_container_width=True, type="primary")
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
    st.info(f"💡 AI đang gợi ý món: **{user_query}**")
    btn_search = True

if selected_tag:
    user_query = selected_tag
    st.info(f"💡 Bạn đã chọn: **{user_query}**")
    btn_search = True

# Kích hoạt tìm kiếm nếu nhấn nút, chọn tag, bấm nút bộ lọc sidebar, hoặc đổi bộ lọc
should_search = btn_search or btn_filter_search or filter_changed

# Tự động tìm kiếm ở lần load đầu tiên nếu chưa có kết quả
if "has_initial_searched" not in st.session_state:
    st.session_state.has_initial_searched = True
    should_search = True

# Thực hiện tìm kiếm
if should_search:
    if not api_key:
        st.error("⚠️ Chưa nhận diện được API Key. Vui lòng mở mục **⚙️ Cấu hình API Key** ở menu bên trái để dán API Key hoặc tạo tệp `.env`.")
    else:
        filter_summary = f"Quận: {selected_district} | Thể loại: {selected_category} | Phong cách: {selected_vibe} | Giá: {selected_budget}"
        if user_query.strip():
            spinner_msg = f"🤖 AI đang rà soát gợi ý cho **'{user_query}'** ({filter_summary})..."
        else:
            spinner_msg = f"🤖 AI đang tự động tổng hợp gợi ý quán ăn theo bộ lọc (**{filter_summary}**)..."
            
        with st.spinner(spinner_msg):
            results = search_food_with_ai(user_query, selected_district, selected_category, selected_vibe, selected_budget, api_key, default_model)
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