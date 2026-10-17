"""
TRỰC QUAN HÓA SỐ LIỆU ĐÁNH GIÁ (ĐIỂM CỘNG +1: ĐỒ THỊ + CSV LOG)
Yêu cầu:
- Đọc file eval_summary.csv do run_eval.py sinh ra
- Vẽ biểu đồ Token Usage theo câu hỏi
- Vẽ biểu đồ Latency theo phân loại câu hỏi
- Lưu thành các file PNG để chèn vào Báo cáo Word
"""
import os
import pandas as pd
import matplotlib.pyplot as plt

def generate_charts():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(base_dir, "logs")
    csv_path = os.path.join(logs_dir, "eval_summary.csv")

    if not os.path.exists(csv_path):
        print(f"[WARN] Chưa tìm thấy file {csv_path}. Vui lòng chạy 'make eval' trước.")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        print("[WARN] File CSV rỗng, không thể vẽ đồ thị.")
        return

    os.makedirs(logs_dir, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # 1. Đồ thị 1: Phân bổ Token Usage theo từng câu hỏi (Bar Chart xếp chồng Prompt vs Completion)
    plt.figure(figsize=(10, 5))
    x = range(len(df))
    plt.bar(x, df.get("prompt_tokens", 0), label="Prompt Tokens", color="#4A90E2", alpha=0.85)
    plt.bar(x, df.get("completion_tokens", 0), bottom=df.get("prompt_tokens", 0),
            label="Completion Tokens", color="#50E3C2", alpha=0.85)

    plt.xlabel("Mã câu hỏi kiểm thử (Test ID)", fontweight="bold")
    plt.ylabel("Số lượng Tokens tiêu thụ", fontweight="bold")
    plt.title("Biểu đồ Phân bổ Token Usage theo từng Câu hỏi Kiểm thử (AIPR)", fontsize=13, fontweight="bold")
    plt.xticks(x, df["id"], rotation=45)
    plt.legend()
    plt.tight_layout()

    token_chart_path = os.path.join(logs_dir, "eval_tokens_chart.png")
    plt.savefig(token_chart_path, dpi=200)
    plt.close()
    print(f"[OK] Đã xuất biểu đồ Token Usage tại: {token_chart_path}")

    # 2. Đồ thị 2: Độ trễ (Latency) trung bình theo phân loại câu hỏi (Bar Chart theo Type)
    if "type" in df.columns and "latency_seconds" in df.columns:
        latency_by_type = df.groupby("type")["latency_seconds"].mean().reset_index()

        plt.figure(figsize=(8, 4.5))
        bars = plt.bar(latency_by_type["type"], latency_by_type["latency_seconds"], color="#FF7675", width=0.55)
        plt.xlabel("Phân loại câu hỏi (Question Type)", fontweight="bold")
        plt.ylabel("Độ trễ trung bình (Giây)", fontweight="bold")
        plt.title("Độ trễ Trung bình (Latency) theo Phân loại Câu hỏi", fontsize=13, fontweight="bold")
        plt.xticks(rotation=20)

        # Ghi giá trị số lên đầu mỗi cột
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2.0, height + 0.1, f"{height:.2f}s", ha="center", va="bottom", fontsize=10)

        plt.tight_layout()
        latency_chart_path = os.path.join(logs_dir, "eval_latency_chart.png")
        plt.savefig(latency_chart_path, dpi=200)
        plt.close()
        print(f"[OK] Đã xuất biểu đồ Latency tại: {latency_chart_path}")

if __name__ == "__main__":
    generate_charts()
