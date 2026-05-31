"""
prepare_yolo_data.py
--------------------
解壓 Roboflow 下載的 YOLOv8 zip 並修正 data.yaml 路徑。

背景說明：
  Roboflow 匯出的 zip 裡，data.yaml 的路徑寫法是 ../train/images，
  這是相對於 zip 根目錄的路徑，解壓後直接使用會找不到圖片。
  這支腳本會把路徑改成絕對路徑，並存成 data_fixed.yaml。

執行方式：
  python src/prepare_yolo_data.py

執行完成後應該看到：
  dataset/train/images/  ← 訓練圖片
  dataset/valid/images/  ← 驗證圖片
  dataset/data_fixed.yaml ← 路徑已修正的設定檔
"""

import zipfile
import yaml
from pathlib import Path


# Roboflow 下載的 zip 檔名（放在專案根目錄）
ZIP_PATH    = "Pineapple_v1i_yolov8.zip"

# 解壓目標目錄
DATASET_DIR = Path("dataset")


def main():
    # 如果 dataset/ 已存在就跳過解壓，避免覆蓋已有的資料
    if DATASET_DIR.exists():
        print(f"[!] {DATASET_DIR} 已存在，跳過解壓。")
    else:
        print(f"解壓 {ZIP_PATH} ...")
        with zipfile.ZipFile(ZIP_PATH, "r") as z:
            z.extractall(DATASET_DIR)
        print(f"解壓完成 → {DATASET_DIR}/")

    # 讀取 Roboflow 原始的 data.yaml
    yaml_path = DATASET_DIR / "data.yaml"
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    # 印出原始路徑，讓使用者確認內容
    print(f"\n原始 data.yaml 內容：")
    for key in ["train", "val", "test"]:
        if key in data:
            print(f"  {key}: {data[key]}")

    # ── 路徑修正邏輯 ────────────────────────────────────────
    # Roboflow 的路徑格式是 ../train/images
    # 解壓到 dataset/ 後，train/ 實際在 dataset/train/images
    # 所以去掉開頭的 '../' 前綴，再拼上 dataset/ 的絕對路徑
    root = DATASET_DIR.resolve()

    for key in ["train", "val", "test"]:
        if key in data and data[key]:
            orig  = data[key]
            # Path('../train/images').parts → ('..', 'train', 'images')
            # 過濾掉 '..' 只取後面的部分 → ('train', 'images')
            parts = [p for p in Path(orig).parts if p != ".."]
            if parts:
                data[key] = str(root / Path(*parts))  # 拼成絕對路徑

    # 存成 data_fixed.yaml，不覆蓋原始 data.yaml
    fixed_path = DATASET_DIR / "data_fixed.yaml"
    with open(fixed_path, "w") as f:
        yaml.dump(data, f)

    # 印出修正後的路徑，並確認目錄是否真的存在
    print(f"\n修正後路徑：")
    for key in ["train", "val", "test"]:
        if key in data:
            p      = Path(data[key])
            status = "✓ 存在" if p.exists() else "✗ 不存在！請確認 zip 解壓是否正確"
            print(f"  {key}: {data[key]}  [{status}]")

    print(f"\ndata_fixed.yaml 儲存 → {fixed_path}")
    print("\n完成！執行 python src/train_yolo.py 開始訓練")


if __name__ == "__main__":
    main()
