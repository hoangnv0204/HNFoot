import os
import json
import re
import time
from datetime import datetime
import streamlit as st
from google import genai
from google.genai import types

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

def search_ai_recommendations(mode, query_text, district, cat_or_type, extra1, extra2, budget_or_cost, api_key_val, model_name="gemini-3.6-flash"):
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
