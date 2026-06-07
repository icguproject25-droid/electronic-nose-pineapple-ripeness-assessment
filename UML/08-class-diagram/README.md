# 第八章 類別圖（Class Diagrams）

本資料夾整理「水果（鳳梨）電子鼻非破壞性熟度檢測系統 / PineNose」第八章所需之類別圖。  
類別圖主要用來描述系統的**靜態結構**，也就是系統中有哪些主要類別、每個類別具有哪些屬性與操作，以及類別之間如何產生關係。

本章接續第七章活動圖，將前面使用案例與流程中出現的角色、資料、功能模組與介面整理成類別模型。  
其中包含使用者、消費端 App、農民端 App、掃描紀錄、感測資料、特徵向量、成熟度結果、批次、報表、校正模組、推論引擎、模型、照片品種辨識 API 等類別。

---

## 1. 本章目的

第七章活動圖主要描述「流程如何執行」，而第八章類別圖則描述「系統由哪些類別組成」。  
因此，本章類別圖的目的如下：

1. **建立整個資訊系統的靜態模型**  
   透過類別圖整理 PineNose 系統中的資料物件、控制模組與使用者介面。

2. **描述類別的屬性與操作**  
   每個類別皆包含主要屬性，例如使用者編號、掃描時間、感測數值、成熟度階段、批次狀態等；也包含主要操作，例如開始掃描、計算特徵、產生報表、執行推論等。

3. **表示類別之間的關係**  
   本章使用一般化、關聯、聚合、組合、相依與具體化等 UML 關係，呈現類別之間的結構。

4. **對應第七章活動圖流程**  
   第七章中的消費者掃描、農民批次掃描、空氣基線校正、模型推論與照片品種辨識流程，都能在本章類別圖中找到對應的類別。

5. **作為後續程式設計與資料設計依據**  
   類別圖可協助後續系統實作時釐清資料欄位、方法功能與模組責任。

---

## 2. 類別圖繪製原則

本章類別圖依照物件導向分析設計概念繪製，主要採用以下原則：

| 項目 | 說明 |
|---|---|
| 類別名稱 | 使用中文名稱搭配英文類別名稱，方便閱讀與對應程式設計 |
| 屬性 Attribute | 表示類別所保存的資料，例如 `掃描編號 : String`、`信心值 : double` |
| 操作 Operation | 表示類別可執行的功能，例如 `開始推論()`、`產生PDF()` |
| 能見度 Visibility | 使用 `+`、`-`、`#`、`~` 表示 public、private、protected、package |
| stereotype | 使用 `<<entity>>`、`<<control>>`、`<<boundary>>` 區分類別角色 |
| 一般化 Generalization | 表示繼承關係，例如 Consumer 與 Farmer 繼承 User |
| 組合 Composition | 表示強生命週期關係，例如掃描紀錄包含感測資料、特徵向量與成熟度結果 |
| 聚合 Aggregation | 表示整體與部分關係，但部分可獨立存在 |
| 相依 Dependency | 表示某類別使用另一類別提供的服務 |
| 具體化 Realization | 表示類別實作介面，例如 ExtraTreesModel 實作 PredictiveModel |

---

## 3. stereotype 說明

| stereotype | 中文說明 | 本系統中的例子 |
|---|---|---|
| `<<entity>>` | 資料實體類別，主要保存系統資料 | User、ScanRecord、SensorData、Batch、Report |
| `<<control>>` | 控制類別，負責流程控制、資料處理或演算法邏輯 | InferenceEngine、CalibrationModule、FeatureExtractor |
| `<<boundary>>` | 邊界類別，負責使用者介面、API 或外部系統溝通 | ConsumerApp、FarmerApp、FlaskTestInterface、PhotoRecognitionAPI |

---

## 4. 類別圖檔案清單

| 編號 | 圖片檔名 | 內容說明 |
|---|---|---|
| 8-1 CH | `8-1 Ch08 整體資訊系統類別圖_CH.png` | 中文版整體資訊系統類別圖 |
| 8-1 EN | `8-1 Ch08 整體資訊系統類別圖_EN.png` | 英文版整體資訊系統類別圖 |
| 8-2 | `8-2 整體資訊系統類別總覽圖.png` | 將整體系統濃縮成較容易閱讀的總覽圖 |
| 8-3 | `8-3 使用者&掃描紀錄&成熟度結果類別圖.png` | 使用者、消費端掃描、歷史紀錄與成熟度結果 |
| 8-4 | `8-4 農民端批次&掃描&報表類別圖.png` | 農民批次管理、批次掃描、統計摘要與報表 |
| 8-5 | `8-5 系統&感測&校正&推論模型類別圖.png` | Arduino、Raspberry Pi、感測資料、校正與模型推論 |
| 8-6 | `8-6 照片品種辨識類別圖.png` | 照片上傳、內容檢查、YOLO 偵測、EfficientNet 分類與 API 回傳 |

---

## 5. 8-1 整體資訊系統類別圖（中文版）

此圖為第八章最重要的整體類別圖，呈現 PineNose 整個資訊系統的主要類別與關係。  
內容包含使用者相關類別、掃描與結果類別、農民端批次類別、系統與模型類別、App 與介面類別，以及照片品種辨識補充類別。

中文版適合放在報告中讓老師快速理解整體系統結構。  
圖中可以看出 Consumer 與 Farmer 繼承 User，ScanRecord 組合 SensorData、FeatureVector 與 RipenessResult，Batch 組合 BatchScanRecord 與 Report，而 App、FlaskTestInterface、PhotoRecognitionAPI 則作為 boundary 類別與系統互動。

![8-1 Ch08 整體資訊系統類別圖_CH](./8-1%20Ch08%20整體資訊系統類別圖_CH.png)

---

## 6. 8-1 Overall Information System Class Diagram（English Version）

此圖為整體資訊系統類別圖的英文版。  
英文版的優點是比較容易對應未來程式設計中的 class name、attribute name 與 method name，也符合物件導向設計中常見的 UML 命名方式。

如果報告需要同時兼顧可讀性與程式設計對應，建議中文版放入正文，英文版可放入附錄或 GitHub 文件中。

![8-1 Ch08 整體資訊系統類別圖_EN](./8-1%20Ch08%20整體資訊系統類別圖_EN.png)

---

## 7. 8-2 整體資訊系統類別總覽圖

此圖是整體系統類別圖的簡化總覽版本。  
相較於 8-1 的完整類別圖，8-2 更適合用來快速說明系統架構，讓閱讀者先掌握 PineNose 的主要模組，再進一步閱讀後面的細部分圖。

此圖通常包含下列主要區塊：

- 使用者相關：User、Consumer、Farmer
- 掃描與結果相關：ScanRecord、SensorData、FeatureVector、RipenessResult
- 農民端批次相關：Batch、BatchScanRecord、Report
- 系統與模型相關：SensorModule、CalibrationModule、AirBaseline、InferenceEngine、MachineLearningModel
- App 與介面相關：ConsumerApp、FarmerApp、FlaskTestInterface
- 照片品種辨識補充：PhotoRecognitionAPI、VarietyResult

此圖的重點不是呈現所有細節，而是讓老師或組員能先看懂整個資訊系統由哪些大類別組成，以及各大模組之間如何互相連接。

![8-2 整體資訊系統類別總覽圖](./8-2%20整體資訊系統類別總覽圖.png)

---

## 8. 8-3 使用者、掃描紀錄與成熟度結果類別圖

此圖補充消費端與單顆鳳梨掃描相關的類別細節。  
主要類別包含 User、Consumer、ConsumerApp、ScanRecord、SensorData、SensorWindow、FeatureVector、RipenessResult、HistoryManager、KnowledgeContent 與 LanguageSetting。

此圖對應第七章中的以下活動圖：

- UC-01 消費者開始掃描鳳梨
- UC-02 消費者查看成熟度結果
- UC-03 消費者查看歷史紀錄
- UC-04 消費者切換語言
- UC-05 消費者查看鳳梨知識內容

此圖重點在於說明：  
消費者透過 ConsumerApp 操作系統，掃描過程會產生 ScanRecord，而 ScanRecord 會組合 SensorWindow、FeatureVector 與 RipenessResult。HistoryManager 則負責歷史紀錄的新增、讀取、排序與刪除。

![8-3 使用者&掃描紀錄&成熟度結果類別圖](./8-3%20使用者%26掃描紀錄%26成熟度結果類別圖.png)

---

## 9. 8-4 農民端批次、掃描與報表類別圖

此圖補充農民端批次功能的類別結構。  
主要類別包含 Farmer、FarmerApp、Batch、BatchScanRecord、SamplingRule、WeatherRecord、BatchSummary、BatchHistoryManager、Report 與 ReportGenerator。

此圖對應第七章中的以下活動圖：

- UC-06 農民建立批次
- UC-07 農民執行批次掃描
- UC-08 農民查看批次結果
- UC-09 農民匯出報表
- UC-10 農民查看批次歷史

此圖重點在於說明：  
Farmer 可建立多個 Batch，每個 Batch 可包含多筆 BatchScanRecord。BatchSummary 負責統計成熟度分布與出貨建議，ReportGenerator 則根據 Batch 與 BatchSummary 產生 PDF、圖表或 CSV 報表。

![8-4 農民端批次&掃描&報表類別圖](./8-4%20農民端批次%26掃描%26報表類別圖.png)

---

## 10. 8-5 系統、感測、校正與推論模型類別圖

此圖補充 PineNose 電子鼻系統的核心技術類別。  
主要類別包含 ArduinoController、RaspberryPiGateway、SensorModule、GasSensor、EnvironmentSensor、SensorData、SensorWindow、CalibrationModule、AirBaseline、FeatureExtractor、FeatureVector、PredictiveModel、MachineLearningModel、ExtraTreesModel、InferenceEngine 與 RipenessResult。

此圖對應第七章中的以下活動圖：

- UC-11 系統執行空氣基線校正
- UC-12 系統進行模型推論
- UC-01 消費者開始掃描鳳梨
- UC-07 農民執行批次掃描

此圖重點在於說明：  
ArduinoController 負責讀取氣體感測器與環境感測器資料，RaspberryPiGateway 透過 Serial 接收資料。CalibrationModule 會產生 AirBaseline，InferenceEngine 則使用 SensorModule、FeatureExtractor、AirBaseline 與 ExtraTreesModel 完成成熟度推論。

![8-5 系統&感測&校正&推論模型類別圖](./8-5%20系統%26感測%26校正%26推論模型類別圖.png)

---

## 11. 8-6 照片品種辨識類別圖

此圖補充照片品種辨識功能的類別結構。  
主要類別包含 ClientInterface、PhotoRecognitionAPI、ImageUpload、PhotoContentChecker、ContentCheckResult、PineappleDetector、DetectionResult、ImageCropper、VarietyClassifier、VarietyResult、ApiResponse 與 DockerBackupService。

此圖對應第七章中的補充活動圖：

- UC-13 補充照片辨識品種流程活動圖

此圖重點在於說明：  
使用者透過 App 或 Flask 整合網頁上傳圖片後，PhotoRecognitionAPI 會先使用 PhotoContentChecker 檢查圖片亮度、對比與有效內容，再使用 YOLOv8n 鳳梨偵測器判斷是否有鳳梨，最後由 EfficientNet 品種分類器輸出金鑽鳳梨、土鳳梨、牛奶鳳梨或西瓜鳳梨等分類結果。DockerBackupService 則代表 VM Docker 備援部署方式。

![8-6 照片品種辨識類別圖](./8-6%20照片品種辨識類別圖.png)

---

## 12. 與第七章活動圖的對應關係

| 第七章活動圖 | 第八章主要對應類別 |
|---|---|
| UC-01 消費者開始掃描鳳梨 | ConsumerApp、SensorModule、SensorData、FeatureVector、InferenceEngine、RipenessResult |
| UC-02 消費者查看成熟度結果 | RipenessResult、ScanRecord、HistoryManager、ConsumerApp |
| UC-03 消費者查看歷史紀錄 | HistoryManager、ScanRecord、ConsumerApp |
| UC-04 消費者切換語言 | LanguageSetting、ConsumerApp、User |
| UC-05 消費者查看鳳梨知識內容 | KnowledgeContent、ConsumerApp |
| UC-06 農民建立批次 | FarmerApp、Batch、SamplingRule、WeatherRecord |
| UC-07 農民執行批次掃描 | FarmerApp、Batch、BatchScanRecord、SensorModule、InferenceEngine |
| UC-08 農民查看批次結果 | Batch、BatchSummary、BatchScanRecord、FarmerApp |
| UC-09 農民匯出報表 | Report、ReportGenerator、BatchSummary |
| UC-10 農民查看批次歷史 | BatchHistoryManager、Batch、FarmerApp |
| UC-11 系統執行空氣基線校正 | CalibrationModule、AirBaseline、SensorModule、RaspberryPiGateway |
| UC-12 系統進行模型推論 | InferenceEngine、FeatureExtractor、ExtraTreesModel、PredictiveModel |
| UC-13 補充照片辨識品種流程 | PhotoRecognitionAPI、ImageUpload、PhotoContentChecker、PineappleDetector、VarietyClassifier、VarietyResult |

---

## 13. 本章類別圖與系統功能對照

| 系統功能 | 對應類別 |
|---|---|
| 消費者單顆掃描 | ConsumerApp、ScanRecord、SensorData、InferenceEngine |
| 成熟度結果顯示 | RipenessResult、ConsumerApp |
| 歷史紀錄查詢 | HistoryManager、ScanRecord |
| 語言切換 | LanguageSetting、ConsumerApp、FarmerApp |
| 農民建立批次 | FarmerApp、Batch、SamplingRule |
| 農民批次掃描 | Batch、BatchScanRecord、InferenceEngine |
| 批次結果統計 | BatchSummary、BatchScanRecord |
| 報表匯出 | Report、ReportGenerator |
| 空氣基線校正 | CalibrationModule、AirBaseline、SensorModule |
| 模型推論 | InferenceEngine、FeatureExtractor、ExtraTreesModel |
| 照片品種辨識 | PhotoRecognitionAPI、PineappleDetector、VarietyClassifier |
| Docker 備援 | DockerBackupService、PhotoRecognitionAPI |

---

---

## 14. 補充說明

本章類別圖呈現系統的靜態結構，與第七章活動圖互相補充。  
第七章活動圖說明「流程如何走」，第八章類別圖說明「系統由哪些類別組成」。  
透過這兩章，可以完整呈現 PineNose 從使用者操作、感測資料收集、模型推論、批次管理、報表匯出，到照片品種辨識的整體系統設計。

本章類別圖也可作為後續程式設計、資料表設計、API 規劃與測試案例設計的基礎文件。
