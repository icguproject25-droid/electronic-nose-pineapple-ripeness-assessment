"""
prepare_yolo_data.py
--------------------
解壓 Roboflow 下載的 YOLOv8 zip 並修正 data.yaml 路徑
執行：python src/prepare_yolo_data.py
"""

import zipfile
import yaml
from pathlib import Path

ZIP_PATH    = "Pineapple_v1i_yolov8.zip"
DATASET_DIR = Path("dataset")


def main():
    if DATASET_DIR.exists():
        print(f"[!] {DATASET_DIR} 已存在，跳過解壓。")
    else:
        print(f"解壓 {ZIP_PATH} ...")
        with zipfile.ZipFile(ZIP_PATH, "r") as z:
            z.extractall(DATASET_DIR)
        print(f"解壓完成 → {DATASET_DIR}/")

    yaml_path = DATASET_DIR / "data.yaml"
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    print(f"\n原始 data.yaml 內容：")
    for key in ["train", "val", "test"]:
        if key in data:
            print(f"  {key}: {data[key]}")

    # Roboflow 的路徑是 ../train/images
    # zip 解壓到 dataset/ 後，train/ 在 dataset/train/images
    # 所以去掉 ../ 直接拼在 dataset/ 下面
    root = DATASET_DIR.resolve()

    for key in ["train", "val", "test"]:
        if key in data and data[key]:
            orig = data[key]
            # ../train/images → parts = ['..', 'train', 'images']
            # 去掉開頭的 '..' → ['train', 'images']
            parts = [p for p in Path(orig).parts if p != ".."]
            if parts:
                data[key] = str(root / Path(*parts))

    fixed_path = DATASET_DIR / "data_fixed.yaml"
    with open(fixed_path, "w") as f:
        yaml.dump(data, f)

    print(f"\n修正後路徑：")
    for key in ["train", "val", "test"]:
        if key in data:
            p = Path(data[key])
            status = "✓ 存在" if p.exists() else "✗ 不存在！"
            print(f"  {key}: {data[key]}  [{status}]")

    print(f"\ndata_fixed.yaml 儲存 → {fixed_path}")
    print("\n✅ 完成！執行 python src/train_yolo.py 開始訓練")


if __name__ == "__main__":
    main()
