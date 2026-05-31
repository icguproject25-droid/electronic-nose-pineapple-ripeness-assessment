"""
train_yolo.py
-------------
訓練 YOLOv8n 鳳梨偵測模型。

訓練完成後最佳權重會自動複製到：
  outputs/yolov8n_pineapple_best.pt

執行前請先確認資料集已解壓（執行 prepare_yolo_data.py），
且 dataset/data_fixed.yaml 存在。

執行方式：
  python src/train_yolo.py
"""

from ultralytics import YOLO
from pathlib import Path
import yaml
import shutil


# ══════════════════════════════════════════
# 訓練設定，集中管理所有可調整的參數
# ══════════════════════════════════════════
CFG = {
    "data_yaml"  : "dataset/data.yaml",    # Roboflow 解壓後的 data.yaml 路徑
    "model"      : "yolov8n.pt",           # 使用 YOLOv8 nano 版本：
                                            # n < s < m < l < x，n 最輕量最快，
                                            # 適合 Raspberry Pi 3 等邊緣裝置
    "epochs"     : 100,                    # 最大訓練輪數
    "imgsz"      : 640,                    # 訓練圖片尺寸（YOLOv8 標準輸入大小）
    "batch"      : 8,                      # 批次大小，CPU 訓練建議 8，GPU 可調高到 16
    "patience"   : 50,                     # early stopping：連續 50 epoch 沒有進步就提前停止
    "project"    : "outputs",              # 訓練結果存放的根目錄
    "name"       : "yolov8n_pineapple",    # 本次訓練的子目錄名稱
    "device"     : "0",                    # 推論裝置：有 GPU 填 "0"，純 CPU 填 "cpu"
}
# ══════════════════════════════════════════


def fix_data_yaml():
    """
    修正 Roboflow 下載的 data.yaml 路徑問題。

    問題說明：
      Roboflow 產生的 data.yaml 使用相對路徑（如 ../train/images），
      當工作目錄不是 dataset/ 時，YOLO 會找不到圖片。

    解決方式：
      把 train/val/test 路徑改成絕對路徑，
      並存成 data_fixed.yaml，避免覆蓋原始檔案。
    """
    yaml_path = Path(CFG["data_yaml"])
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    dataset_root = yaml_path.parent.resolve()  # 取得 dataset/ 的絕對路徑

    # 逐一修正 train / val / test 的路徑
    for key in ["train", "val", "test"]:
        if key in data and data[key]:
            p = Path(data[key])
            if not p.is_absolute():
                # 例如 ../train/images → dataset/train/images（絕對路徑）
                fixed = (dataset_root / p).resolve()
                data[key] = str(fixed)

    # 存成 data_fixed.yaml，不覆蓋 Roboflow 原始的 data.yaml
    fixed_yaml = yaml_path.parent / "data_fixed.yaml"
    with open(fixed_yaml, "w") as f:
        yaml.dump(data, f)

    print(f"data.yaml 路徑已修正 → {fixed_yaml}")
    print(f"  train: {data.get('train')}")
    print(f"  val:   {data.get('val')}")
    return str(fixed_yaml)


def main():
    Path("outputs").mkdir(exist_ok=True)  # 確保輸出目錄存在

    print("=" * 55)
    print("  YOLOv8n 鳳梨偵測訓練")
    print(f"  Dataset : {CFG['data_yaml']}")
    print(f"  Epochs  : {CFG['epochs']}")
    print(f"  Device  : {CFG['device']}")
    print("=" * 55)

    # 使用已修正路徑的 data.yaml
    fixed_yaml = "dataset/data_fixed.yaml"

    # 載入 YOLOv8n 預訓練模型（第一次執行會自動下載 yolov8n.pt）
    model = YOLO(CFG["model"])

    results = model.train(
        data      = fixed_yaml,
        epochs    = CFG["epochs"],
        imgsz     = CFG["imgsz"],
        batch     = CFG["batch"],
        patience  = CFG["patience"],
        project   = CFG["project"],
        name      = CFG["name"],
        device    = CFG["device"],

        # ── 資料增強參數（Data Augmentation）────────────────
        # 對小資料集（4100 張）來說，增強非常重要，
        # 可以讓模型見到更多變化，提高泛化能力
        hsv_h  = 0.015,   # 色調（Hue）隨機偏移 ±1.5%，模擬不同光源的色調變化
        hsv_s  = 0.7,     # 飽和度（Saturation）隨機縮放，模擬陰天/晴天差異
        hsv_v  = 0.4,     # 亮度（Value）隨機縮放，模擬曝光差異
        flipud = 0.3,     # 30% 機率上下翻轉，因為俯拍時方向不固定
        fliplr = 0.5,     # 50% 機率左右翻轉，標準增強
        mosaic = 1.0,     # Mosaic 增強：把 4 張圖拼在一起，幫助偵測小目標
        mixup  = 0.1,     # 10% 機率 Mixup：疊加兩張圖，增加多樣性
    )

    # 訓練結束後，把最佳權重複製到固定路徑，方便後續直接引用
    best = Path(f"outputs/{CFG['name']}/weights/best.pt")
    dest = Path("outputs/yolov8n_pineapple_best.pt")
    if best.exists():
        shutil.copy2(best, dest)
        print(f"\n最佳權重儲存 → {dest}")

    print("\n訓練完成！執行 python src/evaluate_yolo.py 查看評估結果")


if __name__ == "__main__":
    main()
