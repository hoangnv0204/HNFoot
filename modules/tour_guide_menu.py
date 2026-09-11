import random
import streamlit as st
from utils.ai_helper import search_ai_recommendations

def render_tour_guide_sidebar():
    selected_origin = st.selectbox(
        "📍 Nơi khởi hành (Điểm đi):",
        ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Bắc Ninh", "Khác"]
    )
    selected_duration_guide = st.selectbox(
        "⏱️ Thời gian chuyến đi:",
        ["3 ngày 2 đêm", "2 ngày 1 đêm", "1 ngày (Đi trong ngày)", "4 ngày 3 đêm", "5 ngày 4 đêm"]
    )
    selected_time_guide = st.selectbox(
        "📅 Thời điểm đi (Mùa):",
        ["Tự động (Theo tháng 8 hiện tại)", "Tháng này (Thời tiết thật)", "Mùa Xuân", "Mùa Hè", "Mùa Thu", "Mùa Đông"]
    )
    selected_departure_time = st.selectbox(
        "🌅 Khung giờ xuất phát:",
        ["Tự động (Giờ tối ưu)", "Buổi Sáng (5h - 9h)", "Buổi Chiều (12h - 15h)", "Buổi Tối / Đêm (18h - 22h)"]
    )
    selected_preferred_vehicle = st.selectbox(
        "🚗 Phương tiện mong muốn:",
        ["Tự động gợi ý tốt nhất", "Xe khách Limousine / Giường nằm", "Tàu hỏa hỏa tốc", "Máy bay", "Xe máy phượt", "Ô tô cá nhân / Tự lái"]
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
    return (
        selected_origin,
        selected_duration_guide,
        selected_time_guide,
        selected_departure_time,
        selected_preferred_vehicle,
        selected_companion_guide,
        selected_budget_guide,
        btn_filter_search
    )


def render_tour_guide_main(selected_origin, selected_duration_guide, selected_time_guide, selected_departure_time, selected_preferred_vehicle, selected_companion_guide, selected_budget_guide, btn_filter_search, api_key, default_model):
    st.markdown('<div class="sub-title">Cẩm nang du lịch trọn gói: Gợi ý Đặt xe, Top Homestay ok nhất, Outfit & Lịch trình chi tiết tiện đường</div>', unsafe_allow_html=True)

    col_loc1, col_loc2 = st.columns(2)
    with col_loc1:
        origin_input = st.text_input("📍 Điểm khởi hành (Nơi đi):", value=selected_origin)
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
                    f"Mùa: {selected_time_guide} | Xuất phát: {selected_departure_time} | Phương tiện mong muốn: {selected_preferred_vehicle}",
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
                        if act.get('outfit_suggestion'):
                            st.success(f"👗 **Gợi ý outfit & tone màu:** {act.get('outfit_suggestion')}")
                            
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

        # Google Sheets Export Section (5 Cột)
        st.markdown("---")
        st.markdown("### 📊 Tạo Bảng Google Sheets (Cẩm Nang Du Lịch 5 Cột)")
        st.caption("Xuất toàn bộ lịch trình chuyến đi thành bảng chuẩn 5 cột (`Thời gian`, `Lịch Trình`, `Google Maps`, `Note`, `Gợi ý tone màu quần áo`) sẵn sàng để dán vào Google Sheets hoặc tải về tệp Excel / CSV.")

        import pandas as pd

        outfit_general = guide.get("outfit_guide", {})
        gen_colors = ", ".join(outfit_general.get("recommended_colors", []))
        gen_style = outfit_general.get("style_name", "")
        fallback_outfit = f"Tone: {gen_colors} ({gen_style})" if gen_colors else gen_style

        sheet_data = []
        table_rows_html = []
        day_list = guide.get("day_by_day_itinerary", [])

        for day_idx, day_item in enumerate(day_list):
            day_title = day_item.get("day_title", f"Ngày {day_idx+1}")
            
            # Big Day Header Row in Table
            table_rows_html.append(f"""
            <tr style="background-color: #e6f4ea;">
                <td colspan="5" style="padding: 12px 15px; border: 1px solid #0b8043; font-size: 15px; font-weight: 800; color: #0d652d; background: linear-gradient(90deg, #e6f4ea 0%, #ffffff 100%); letter-spacing: 0.5px;">
                    📌 {day_title.upper()}
                </td>
            </tr>
            """)

            sheet_data.append({
                "Thời gian": f"📌 {day_title.upper()}",
                "Lịch Trình": "",
                "Google Maps": "",
                "Note": "",
                "Gợi ý tone màu quần áo": ""
            })

            activities = day_item.get("activities", [])
            for act_idx, act in enumerate(activities):
                time_range = act.get('time', '')
                title = act.get('title', '')
                loc = act.get('location', '')
                desc = act.get('description', '')
                itinerary_val = f"{title} - {loc} ({desc})" if loc else f"{title} ({desc})"
                
                maps_url = f"https://www.google.com/maps/search/?api=1&query={title}+{loc}".replace(" ", "+")
                
                notes = []
                if act.get('route_note'):
                    notes.append(f"🚏 Đường đi: {act.get('route_note')}")
                if act.get('pro_tip'):
                    notes.append(f"💡 Mẹo local: {act.get('pro_tip')}")
                note_val = " | ".join(notes) if notes else "—"

                outfit_val = act.get('outfit_suggestion') or fallback_outfit or "Trang phục năng động, thoải mái"

                sheet_data.append({
                    "Thời gian": f"⏰ {time_range}",
                    "Lịch Trình": itinerary_val,
                    "Google Maps": maps_url,
                    "Note": note_val,
                    "Gợi ý tone màu quần áo": outfit_val
                })

                time_html = f"⏰ <b>{time_range}</b>"
                itinerary_html = f"<b>{title}</b><br/>📍 <i>{loc}</i><br/>📝 {desc}" if loc else f"<b>{title}</b><br/>📝 {desc}"
                maps_link_html = f'<a href="{maps_url}" target="_blank" style="color: #0f9d58; font-weight: bold; text-decoration: none; display: inline-block; padding: 4px 8px; background: #e6f4ea; border-radius: 4px; border: 1px solid #0b8043;">🗺️ Mở Maps</a>'
                note_html = "<br/>".join(notes) if notes else "—"

                row_bg = "#ffffff" if act_idx % 2 == 0 else "#f9fbf9"

                table_rows_html.append(f"""
                <tr style="background-color: {row_bg};">
                    <td style="padding: 10px; border: 1px solid #dcdcdc; vertical-align: top; font-size: 13px; font-weight: bold; color: #1a73e8; width: 14%;">{time_html}</td>
                    <td style="padding: 10px; border: 1px solid #dcdcdc; vertical-align: top; font-size: 13px; width: 32%;">{itinerary_html}</td>
                    <td style="padding: 10px; border: 1px solid #dcdcdc; vertical-align: top; text-align: center; font-size: 13px; width: 14%;">{maps_link_html}</td>
                    <td style="padding: 10px; border: 1px solid #dcdcdc; vertical-align: top; font-size: 13px; width: 20%;">{note_html}</td>
                    <td style="padding: 10px; border: 1px solid #dcdcdc; vertical-align: top; font-size: 13px; width: 20%; color: #d93025; font-weight: 500;">👗 {outfit_val}</td>
                </tr>
                """)

        df_sheet = pd.DataFrame(sheet_data)
        csv_data = df_sheet.to_csv(index=False, encoding='utf-8-sig')
        tsv_data = df_sheet.to_csv(index=False, sep='\t', encoding='utf-8')

        table_body = "\n".join(table_rows_html)
        full_html_table = f"""
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; font-family: 'Segoe UI', Arial, sans-serif; color: #333333; border: 1px solid #0b8043; border-radius: 8px; overflow: hidden;">
            <thead>
                <tr style="background: linear-gradient(180deg, #0f9d58 0%, #0b8043 100%); color: #ffffff; text-align: center; font-weight: bold; font-size: 15px;">
                    <th style="width: 14%; padding: 12px; border: 1px solid #0b8043;">⏰ Thời gian</th>
                    <th style="width: 32%; padding: 12px; border: 1px solid #0b8043;">🗺️ Lịch Trình</th>
                    <th style="width: 14%; padding: 12px; border: 1px solid #0b8043;">📍 Google Maps</th>
                    <th style="width: 20%; padding: 12px; border: 1px solid #0b8043;">📝 Note</th>
                    <th style="width: 20%; padding: 12px; border: 1px solid #0b8043;">👗 Gợi ý tone màu quần áo</th>
                </tr>
            </thead>
            <tbody>
                {table_body}
            </tbody>
        </table>
        """

        with st.expander("👁️ Xem trước Bảng Google Sheets (Phân Loại Theo Ngày)", expanded=True):
            st.markdown(full_html_table, unsafe_allow_html=True)

        col_doc1, col_doc2 = st.columns([1, 1])
        with col_doc1:
            st.download_button(
                label="📥 Tải tệp CSV / Excel Đầy Đủ (.csv)",
                data=csv_data.encode("utf-8-sig"),
                file_name=f"Cam_Nang_Du_Lich_{dest_input}.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
        with col_doc2:
            escaped_tsv = tsv_data.replace("`", "\\`").replace("\n", "\\n").replace("\r", "")
            escaped_html = full_html_table.replace("`", "\\`").replace("\n", " ")
            copy_html = f"""
            <script>
            function openAndCopySheets() {{
                const tsvText = `{escaped_tsv}`;
                const htmlText = `{escaped_html}`;
                const blobHtml = new Blob([htmlText], {{ type: 'text/html' }});
                const blobText = new Blob([tsvText], {{ type: 'text/plain' }});
                const item = new ClipboardItem({{
                    'text/html': blobHtml,
                    'text/plain': blobText
                }});
                
                // Copy formatted 5-column table to clipboard
                navigator.clipboard.write([item]).then(function() {{
                    window.open('https://sheets.new', '_blank');
                    document.getElementById('status').innerHTML = '🚀 <b>Đã chép tự động toàn bộ 5 cột & mở Google Sheets!</b><br/>👉 Bạn chỉ cần nhấn <b>Ctrl + V</b> (hoặc Cmd + V) tại ô A1 để dán bảng đầy đủ ngay!';
                }}).catch(function(err) {{
                    navigator.clipboard.writeText(tsvText);
                    window.open('https://sheets.new', '_blank');
                    document.getElementById('status').innerHTML = '🚀 <b>Đã chép dữ liệu & mở Google Sheets!</b><br/>👉 Bạn chỉ cần nhấn <b>Ctrl + V</b> tại ô A1 để dán!';
                }});
            }}
            </script>
            <button onclick="openAndCopySheets()" style="width:100%; padding: 10px 16px; background-color:#0f9d58; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer; font-size:15px; box-shadow: 0 2px 4px rgba(0,0,0,0.15);">
                📊 Mở Trực Tiếp & Điền Đầy Đủ Google Sheets
            </button>
            <div id="status" style="margin-top:8px; font-size:13px; color:#0b8043; background:#e6f4ea; padding:8px; border-radius:4px; font-weight:bold;"></div>
            """
            if hasattr(st, "html"):
                st.html(copy_html)
            else:
                import streamlit.components.v1 as components
                components.html(copy_html, height=75)

