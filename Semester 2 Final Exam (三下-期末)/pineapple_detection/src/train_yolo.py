"""
train_yolo.py
-------------
訓練 YOLOv8n 鳳梨偵測模型
執行：python src/train_yolo.py
"""

from ultralytics import YOLO
from pathlib import Path
import yaml
import shutil

# ══════════════════════════════════════════
CFG = {
    "data_yaml"  : "dataset/data.yaml",   # 解壓後的 data.yaml 路徑
    "model"      : "yolov8n.pt",          # nano：RPi 3 上最快
    "epochs"     : 100,
    "imgsz"      : 640,
    "batch"      : 8,                    # CPU 訓練可改 8
    "patience"   : 50,                    # early stopping
    "project"    : "outputs",
    "name"       : "yolov8n_pineapple",
    "device"     : "0",                 # 有 GPU 改 "0"
}
# ══════════════════════════════════════════


def fix_data_yaml():
    """
    Roboflow 下載的 data.yaml 路徑是相對路徑 ../train/images
    需要改成絕對路徑才能正確讀取
    """
    yaml_path = Path(CFG["data_yaml"])
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    dataset_root = yaml_path.parent.resolve()

    # 修正路徑
    for key in ["train", "val", "test"]:
        if key in data and data[key]:
            p = Path(data[key])
            if not p.is_absolute():
                # ../train/images → dataset/train/images
                fixed = (dataset_root / p).resolve()
                data[key] = str(fixed)

    # 存成新檔避免覆蓋原始
    fixed_yaml = yaml_path.parent / "data_fixed.yaml"
    with open(fixed_yaml, "w") as f:
        yaml.dump(data, f)

    print(f"data.yaml 路徑已修正 → {fixed_yaml}")
    print(f"  train: {data.get('train')}")
    print(f"  val:   {data.get('val')}")
    return str(fixed_yaml)


def main():
    Path("outputs").mkdir(exist_ok=True)

    print("=" * 55)
    print("  YOLOv8n 鳳梨偵測訓練")
    print(f"  Dataset : {CFG['data_yaml']}")
    print(f"  Epochs  : {CFG['epochs']}")
    print(f"  Device  : {CFG['device']}")
    print("=" * 55)

    fixed_yaml = "dataset/data_fixed.yaml"

    model = YOLO(CFG["model"])   # 自動下載 yolov8n.pt

    results = model.train(
        data      = fixed_yaml,
        epochs    = CFG["epochs"],
        imgsz     = CFG["imgsz"],
        batch     = CFG["batch"],
        patience  = CFG["patience"],
        project   = CFG["project"],
        name      = CFG["name"],
        device    = CFG["device"],
        # augmentation（對小資料集很重要）
        hsv_h     = 0.015,
        hsv_s     = 0.7,
        hsv_v     = 0.4,
        flipud    = 0.3,
        fliplr    = 0.5,
        mosaic    = 1.0,
        mixup     = 0.1,
    )

    # 最佳權重位置
    best = Path(f"outputs/{CFG['name']}/weights/best.pt")
    dest = Path("outputs/yolov8n_pineapple_best.pt")
    if best.exists():
        shutil.copy2(best, dest)
        print(f"\n✅ 最佳權重儲存 → {dest}")

    print("\n訓練完成！執行 python src/evaluate_yolo.py 查看結果")


if __name__ == "__main__":
    main()
