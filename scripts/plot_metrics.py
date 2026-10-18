"""
TRỰC QUAN HÓA SỐ LIỆU ĐÁNH GIÁ (ĐIỂM CỘNG +1: ĐỒ THỊ + CSV LOG CHI TIẾT)
Sử dụng OpenCV và NumPy để sinh 2 đồ thị PNG chất lượng cao tự động co dãn tỉ lệ:
1. logs/tokens_by_question.png (Phân bổ Token USAGE theo câu hỏi)
2. logs/latency_by_question.png (Độ trễ xử lý theo từng câu hỏi)
"""
import os
import sys
import csv
import math
import cv2
import numpy as np

def generate_charts():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    csv_path = os.path.join(os.path.dirname(__file__), "..", "logs", "eval_results.csv")
    output_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    
    if not os.path.exists(csv_path):
        print(f"Lỗi: Không tìm thấy file {csv_path}")
        return

    q_ids = []
    types = []
    tokens = []
    latencies = []

    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q_ids.append(row["id"])
            types.append(row["type"])
            tokens.append(int(row["tokens"]))
            latencies.append(float(row["latency"]))

    n = len(q_ids)
    if n == 0:
        return

    # Kích thước khung ảnh chuẩn
    w, h = 1000, 520
    ox, oy = 80, 430

    # ==========================================
    # 1. ĐỒ THỊ TOKEN USAGE (BAR CHART CO DÃN ĐỘNG)
    # ==========================================
    img_token = np.full((h, w, 3), 255, dtype=np.uint8)

    # Tiêu đề
    cv2.putText(img_token, "BENCHMARK TOKEN USAGE PER QUESTION (TESTS/TESTSET.JSONL)", 
                (50, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 51, 102), 2, cv2.LINE_AA)
    cv2.putText(img_token, "Total tokens consumed by Agent per query (Input + Output tokens)", 
                (50, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)

    # Trục tọa độ
    cv2.line(img_token, (ox, oy), (950, oy), (180, 180, 180), 2)
    cv2.line(img_token, (ox, oy), (ox, 110), (180, 180, 180), 2)

    # Tính toán thang đo trục Y tự động cho Token
    actual_max_token = max(tokens) if tokens else 10000
    if actual_max_token <= 2500:
        max_token_val = 2500
        step_token = 500
    elif actual_max_token <= 15000:
        max_token_val = int(math.ceil(actual_max_token / 2500.0) * 2500)
        step_token = 2500
    else:
        max_token_val = int(math.ceil(actual_max_token / 5000.0) * 5000)
        step_token = 5000

    for y_val in range(step_token, max_token_val + 1, step_token):
        y_pos = int(oy - (y_val / max_token_val) * (oy - 110))
        cv2.line(img_token, (ox, y_pos), (950, y_pos), (235, 235, 235), 1)
        label_text = f"{y_val // 1000}k" if y_val >= 1000 else str(y_val)
        cv2.putText(img_token, label_text, (35, y_pos + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1, cv2.LINE_AA)

    # Vẽ cột
    bar_width = 38
    spacing = 58
    color_map = {
        "grounding": (180, 105, 31),        # Blue in BGR
        "multi_doc": (14, 127, 255),        # Orange in BGR
        "reasoning": (44, 160, 44),         # Green in BGR
        "missing": (0, 165, 255),           # Amber
        "action": (40, 40, 214),            # Red in BGR
        "no_answer": (180, 105, 148)        # Purple
    }

    for i in range(n):
        x = ox + 30 + i * spacing
        t_val = tokens[i]
        b_height = int((t_val / max_token_val) * (oy - 110))
        y = oy - b_height

        cat = types[i]
        bar_color = color_map.get("no_answer")
        for k in color_map:
            if k in cat:
                bar_color = color_map[k]
                break

        cv2.rectangle(img_token, (x, y), (x + bar_width, oy), bar_color, -1)
        cv2.rectangle(img_token, (x, y), (x + bar_width, oy), (50, 50, 50), 1)

        val_str = str(t_val)
        cv2.putText(img_token, val_str, (x - 2, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (40, 40, 40), 1, cv2.LINE_AA)
        cv2.putText(img_token, q_ids[i], (x + 3, oy + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 51, 102), 1, cv2.LINE_AA)

    cv2.putText(img_token, "Legend: [Blue] Grounding  [Orange] Multi-Doc  [Green] Reasoning  [Red] Action & Verify  [Purple] No-Answer",
                (80, 495), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 60), 1, cv2.LINE_AA)

    token_png = os.path.join(output_dir, "tokens_by_question.png")
    cv2.imwrite(token_png, img_token)
    print(f"Đã tạo đồ thị Token Usage: {token_png}")

    # ==========================================
    # 2. ĐỒ THỊ LATENCY (LINE CHART CO DÃN ĐỘNG)
    # ==========================================
    img_lat = np.full((h, w, 3), 255, dtype=np.uint8)

    cv2.putText(img_lat, "BENCHMARK PROCESSING LATENCY PER QUERY (SECONDS)", 
                (50, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 51, 102), 2, cv2.LINE_AA)
    cv2.putText(img_lat, "Execution time measured across ReAct Agent steps (End-to-End)", 
                (50, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)

    cv2.line(img_lat, (ox, oy), (950, oy), (180, 180, 180), 2)
    cv2.line(img_lat, (ox, oy), (ox, 110), (180, 180, 180), 2)

    # Tính toán thang đo trục Y tự động cho Latency
    actual_max_lat = max(latencies) if latencies else 30.0
    if actual_max_lat <= 0.05:
        max_lat_val = 0.04
        step_lat = 0.01
        fmt = "{:.2f}s"
    elif actual_max_lat <= 10.0:
        max_lat_val = float(math.ceil(actual_max_lat / 2.0) * 2.0)
        step_lat = 2.0
        fmt = "{:.0f}s"
    else:
        max_lat_val = float(math.ceil(actual_max_lat / 5.0) * 5.0)
        step_lat = 5.0
        fmt = "{:.0f}s"

    cur_val = step_lat
    while cur_val <= max_lat_val + 0.001:
        y_pos = int(oy - (cur_val / max_lat_val) * (oy - 110))
        cv2.line(img_lat, (ox, y_pos), (950, y_pos), (235, 235, 235), 1)
        cv2.putText(img_lat, fmt.format(cur_val), (25, y_pos + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1, cv2.LINE_AA)
        cur_val += step_lat

    pts = []
    for i in range(n):
        x = ox + 30 + i * spacing + bar_width // 2
        l_val = latencies[i]
        y = int(oy - (l_val / max_lat_val) * (oy - 110))
        pts.append((x, y))

    for i in range(len(pts) - 1):
        cv2.line(img_lat, pts[i], pts[i+1], (40, 40, 214), 2, cv2.LINE_AA)

    for i, pt in enumerate(pts):
        cv2.circle(img_lat, pt, 5, (0, 51, 102), -1, cv2.LINE_AA)
        cv2.circle(img_lat, pt, 2, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.putText(img_lat, f"{latencies[i]:.1f}s", (pt[0] - 16, pt[1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (40, 40, 40), 1, cv2.LINE_AA)
        cv2.putText(img_lat, q_ids[i], (pt[0] - 12, oy + 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 51, 102), 1, cv2.LINE_AA)

    avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
    cv2.putText(img_lat, f"Average Latency: {avg_lat:.2f}s per query (End-to-End ReAct Agent with Gemini API)",
                (80, 495), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 60), 1, cv2.LINE_AA)

    latency_png = os.path.join(output_dir, "latency_by_question.png")
    cv2.imwrite(latency_png, img_lat)
    print(f"Đã tạo đồ thị Latency: {latency_png}")

if __name__ == "__main__":
    generate_charts()
