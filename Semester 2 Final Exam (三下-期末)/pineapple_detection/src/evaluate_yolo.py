"""
evaluate_yolo.py
----------------
評估訓練好的 YOLOv8n 模型在 validation set 上的偵測效能。

輸出指標說明：
  mAP@50   ：IoU 門檻 0.5 時的 mean Average Precision
             → 預測框和真實框重疊 50% 以上才算對
             → 我們的模型達到約 86%
  mAP@50-95：IoU 門檻 0.5~0.95（每 0.05 一格）的平均 mAP
             → 比 mAP@50 更嚴格的指標
  Precision：在所有預測為鳳梨的框中，有多少比例是真正的鳳梨
             → 高 Precision = 很少誤報（把非鳳梨說成鳳梨）
  Recall   ：在所有真實的鳳梨中，模型有多少比例偵測到了
             → 高 Recall = 很少漏報（有鳳梨但沒偵測到）

執行：python src/evaluate_yolo.py
"""

from ultralytics import YOLO
from pathlib import Path


# 要評估的模型權重路徑（使用訓練輸出中最佳的那個）
CKPT  = "outputs\\yolov8n_pineapple5\\weights\\best.pt"

# 使用已修正路徑的 data.yaml（由 prepare_yolo_data.py 或 train_yolo.py 產生）
DATA  = "dataset\\data_fixed.yaml"

IMGSZ  = 640    # 評估時的圖片尺寸，要和訓練時一致
DEVICE = "cpu"  # 沒有 GPU 就用 CPU


def main():
    # 載入要評估的模型
    model = YOLO(CKPT)

    print("=" * 55)
    print("  YOLOv8n 評估（validation set）")
    print(f"  權重：{CKPT}")
    print("=" * 55)

    # 在 validation set 上跑評估
    # split="val" 代表使用 data.yaml 中指定的 val 路徑
    metrics = model.val(
        data   = DATA,
        imgsz  = IMGSZ,
        device = DEVICE,
        split  = "val",
    )

    # 印出各項指標
    print(f"\n  mAP@50   : {metrics.box.map50:.4f}  ({metrics.box.map50*100:.1f}%)")
    print(f"  mAP@50-95: {metrics.box.map:.4f}  ({metrics.box.map*100:.1f}%)")
    print(f"  Precision: {metrics.box.mp:.4f}   （精確率，預測為鳳梨且正確的比例）")
    print(f"  Recall   : {metrics.box.mr:.4f}   （召回率，真實鳳梨中被偵測到的比例）")


if __name__ == "__main__":
    main()
