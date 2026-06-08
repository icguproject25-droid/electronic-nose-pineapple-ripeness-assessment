# 第五章 使用案例圖

本資料夾整理「水果（鳳梨）電子鼻非破壞性熟度檢測系統」之使用案例圖（Use Case Diagram）。

依據系統需求分析結果，將消費端、農民端、系統端與照片品種辨識補充功能繪製為 UML 使用案例圖，以描述各角色與系統功能之互動關係。

---

## 使用案例圖清單

| 編號    | 使用案例名稱      | 角色                | 檔案                                          |
| ----- | ----------- | ----------------- | ------------------------------------------- |
| UC-01 | 消費者開始掃描鳳梨   | 消費者               | UC-01-consumer-scan-usecase.png             |
| UC-02 | 消費者查看成熟度結果  | 消費者               | UC-02-consumer-view-result-usecase.png      |
| UC-03 | 消費者查看歷史紀錄   | 消費者               | UC-03-consumer-history-usecase.png          |
| UC-04 | 消費者切換語言     | 消費者               | UC-04-consumer-language-usecase.png         |
| UC-05 | 消費者查看鳳梨知識內容 | 消費者               | UC-05-consumer-knowledge-usecase.png        |
| UC-06 | 農民建立批次      | 農民                | UC-06-farmer-create-batch-usecase.png       |
| UC-07 | 農民執行批次掃描    | 農民                | UC-07-farmer-batch-scan-usecase.png         |
| UC-08 | 農民查看批次結果    | 農民                | UC-08-farmer-view-batch-result-usecase.png  |
| UC-09 | 農民匯出報表      | 農民                | UC-09-farmer-export-report-usecase.png      |
| UC-10 | 農民查看批次歷史    | 農民                | UC-10-farmer-batch-history-usecase.png      |
| UC-11 | 系統執行空氣基線校正  | 開發者／測試人員／系統管理者    | UC-11-air-baseline-calibration-usecase.png  |
| UC-12 | 系統進行模型推論    | 系統／Raspberry Pi 3 | UC-12-model-inference-usecase.png           |
| UC-13 | 補充照片品種辨識    | 使用者               | UC-13-photo-variety-recognition-usecase.png |

---

## 消費端使用案例圖

消費端使用案例主要描述一般使用者透過 App 進行鳳梨成熟度檢測相關操作，包含掃描鳳梨、查看成熟度結果、查閱歷史紀錄、切換語言以及瀏覽鳳梨知識內容等功能。

相關使用案例：

* UC-01 消費者開始掃描鳳梨
* UC-02 消費者查看成熟度結果
* UC-03 消費者查看歷史紀錄
* UC-04 消費者切換語言
* UC-05 消費者查看鳳梨知識內容

---

## 農民端使用案例圖

農民端使用案例主要描述農民利用系統進行批次管理與成熟度分析之流程，包含建立批次、執行批次掃描、查看批次結果、匯出報表以及查閱批次歷史紀錄等功能。

相關使用案例：

* UC-06 農民建立批次
* UC-07 農民執行批次掃描
* UC-08 農民查看批次結果
* UC-09 農民匯出報表
* UC-10 農民查看批次歷史

---

## 系統端使用案例圖

系統端使用案例主要描述系統運作與維護相關功能，包含空氣基線校正與成熟度模型推論等核心流程。

相關使用案例：

* UC-11 系統執行空氣基線校正
* UC-12 系統進行模型推論

---

## 照片品種辨識補充使用案例圖

照片品種辨識補充使用案例主要描述使用者透過 App 或 Flask 整合網頁上傳鳳梨照片後，系統進行照片內容檢查、YOLOv8n 鳳梨偵測與 EfficientNet-B0 品種分類之流程。此功能作為成熟度檢測之外的輔助資訊，用於辨識金鑽鳳梨、土鳳梨、牛奶鳳梨與西瓜鳳梨等品種。

相關使用案例：

* UC-13 補充照片品種辨識

---

## 補充說明

本章主要以 UML 使用案例圖呈現系統功能與角色之互動關係。

使用案例之詳細描述、正常情節與例外情節請參閱：

```text
06-use-case-scenarios/
```

活動圖請參閱：

```text
07-activity-diagrams/
```

類別圖請參閱：

```text
08-class-diagram/
```
