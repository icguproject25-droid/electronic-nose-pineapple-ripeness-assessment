"""
evaluate_yolo.py
----------------
評估 YOLOv8n 在 valid set 上的 mAP、Precision、Recall
執行：python src/evaluate_yolo.py
"""

from ultralytics import YOLO
from pathlib import Path

CKPT = "outputs\\yolov8n_pineapple5\\weights\\best.pt"
DATA = "dataset\\data_fixed.yaml"
IMGSZ    = 640
DEVICE   = "cpu"


def main():
    model = YOLO(CKPT)

    print("=" * 55)
    print("  YOLOv8n 評估（valid set）")
    print("=" * 55)

    metrics = model.val(
        data   = DATA,
        imgsz  = IMGSZ,
        device = DEVICE,
        split  = "val",
    )

    print(f"\n  mAP@50   : {metrics.box.map50:.4f}  ({metrics.box.map50*100:.1f}%)")
    print(f"  mAP@50-95: {metrics.box.map:.4f}  ({metrics.box.map*100:.1f}%)")
    print(f"  Precision: {metrics.box.mp:.4f}")
    print(f"  Recall   : {metrics.box.mr:.4f}")


if __name__ == "__main__":
    main()
