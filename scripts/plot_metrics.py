"""
TRỰC QUAN HÓA SỐ LIỆU ĐÁNH GIÁ (ĐIỂM CỘNG +1: ĐỒ THỊ + CSV LOG CHI TIẾT)
Sử dụng OpenCV và NumPy có sẵn trong môi trường để sinh 2 đồ thị PNG chất lượng cao:
1. logs/tokens_by_question.png (Phân bổ Token USAGE theo câu hỏi)
2. logs/latency_by_question.png (Độ trễ xử lý theo từng câu hỏi)
"""
import os
import sys
import csv
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

    # ==========================================
    # 1. ĐỒ THỊ TOKEN USAGE (BAR CHART)
    # ==========================================
    w, h = 1000, 520
    img_token = np.full((h, w, 3), 255, dtype=np.uint8)

    # Title & Subtitle
    cv2.putText(img_token, "BENCHMARK TOKEN USAGE PER QUESTION (TESTS/TESTSET.JSONL)", 
                (50, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 51, 102), 2, cv2.LINE_AA)
    cv2.putText(img_token, "Total tokens consumed by Agent per query (Input + Output tokens)", 
                (50, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)

    # Axes
    ox, oy = 80, 430
    cv2.line(img_token, (ox, oy), (950, oy), (180, 180, 180), 2)
    cv2.line(img_token, (ox, oy), (ox, 110), (180, 180, 180), 2)

    # Gridlines and Y-axis marks (0, 500, 1000, 1500, 2000, 2500)
    max_token_val = 2200
    for y_val in [500, 1000, 1500, 2000]:
        y_pos = int(oy - (y_val / max_token_val) * (oy - 110))
        cv2.line(img_token, (ox, y_pos), (950, y_pos), (235, 235, 235), 1)
        cv2.putText(img_token, str(y_val), (30, y_pos + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1, cv2.LINE_AA)

    # Bars
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

        # Category color
        cat = types[i]
        bar_color = color_map.get("no_answer")
        for k in color_map:
            if k in cat:
                bar_color = color_map[k]
                break

        cv2.rectangle(img_token, (x, y), (x + bar_width, oy), bar_color, -1)
        cv2.rectangle(img_token, (x, y), (x + bar_width, oy), (50, 50, 50), 1)

        # Value text on top
        val_str = str(t_val)
        cv2.putText(img_token, val_str, (x - 2, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (40, 40, 40), 1, cv2.LINE_AA)

        # X label
        cv2.putText(img_token, q_ids[i], (x + 3, oy + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 51, 102), 1, cv2.LINE_AA)

    # Legend at bottom
    cv2.putText(img_token, "Legend: [Blue] Grounding  [Orange] Multi-Doc  [Green] Reasoning  [Red] Action & Verify  [Purple] No-Answer",
                (80, 495), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 60), 1, cv2.LINE_AA)

    token_png = os.path.join(output_dir, "tokens_by_question.png")
    cv2.imwrite(token_png, img_token)
    print(f"Đã tạo đồ thị Token Usage: {token_png}")

    # ==========================================
    # 2. ĐỒ THỊ LATENCY (LINE CHART)
    # ==========================================
    img_lat = np.full((h, w, 3), 255, dtype=np.uint8)

    # Title & Subtitle
    cv2.putText(img_lat, "BENCHMARK PROCESSING LATENCY PER QUERY (SECONDS)", 
                (50, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 51, 102), 2, cv2.LINE_AA)
    cv2.putText(img_lat, "Execution time measured across ReAct Agent steps (End-to-End)", 
                (50, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)

    # Axes
    cv2.line(img_lat, (ox, oy), (950, oy), (180, 180, 180), 2)
    cv2.line(img_lat, (ox, oy), (ox, 110), (180, 180, 180), 2)

    # Gridlines and Y-axis marks (0.00s, 0.01s, 0.02s, 0.03s, 0.04s)
    max_lat_val = 0.035
    for l_val in [0.01, 0.02, 0.03]:
        y_pos = int(oy - (l_val / max_lat_val) * (oy - 110))
        cv2.line(img_lat, (ox, y_pos), (950, y_pos), (235, 235, 235), 1)
        cv2.putText(img_lat, f"{l_val:.2f}s", (25, y_pos + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1, cv2.LINE_AA)

    pts = []
    for i in range(n):
        x = ox + 30 + i * spacing + bar_width // 2
        l_val = latencies[i]
        y = int(oy - (l_val / max_lat_val) * (oy - 110))
        pts.append((x, y))

    # Draw lines
    for i in range(len(pts) - 1):
        cv2.line(img_lat, pts[i], pts[i+1], (40, 40, 214), 2, cv2.LINE_AA)

    # Draw points and text
    for i, pt in enumerate(pts):
        cv2.circle(img_lat, pt, 5, (0, 51, 102), -1, cv2.LINE_AA)
        cv2.circle(img_lat, pt, 2, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.putText(img_lat, f"{latencies[i]:.2f}s", (pt[0] - 18, pt[1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (40, 40, 40), 1, cv2.LINE_AA)
        cv2.putText(img_lat, q_ids[i], (pt[0] - 12, oy + 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 51, 102), 1, cv2.LINE_AA)

    cv2.putText(img_lat, "Average Latency: < 0.02s per query (Fast local retrieval and mock reasoning)",
                (80, 495), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 60), 1, cv2.LINE_AA)

    latency_png = os.path.join(output_dir, "latency_by_question.png")
    cv2.imwrite(latency_png, img_lat)
    print(f"Đã tạo đồ thị Latency: {latency_png}")

if __name__ == "__main__":
    generate_charts()
