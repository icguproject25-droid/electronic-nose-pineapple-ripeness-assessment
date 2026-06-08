# 第四章 詞彙表（Glossary）

本章整理本系統開發過程中所使用之專有名詞、技術名詞與系統術語，以利後續文件閱讀與系統維護。

| 詞彙                                     | 定義／解釋                                     | 備註                  |
| -------------------------------------- | ----------------------------------------- | ------------------- |
| 電子鼻（Electronic Nose）                   | 模擬人類嗅覺系統，透過多組氣體感測器分析氣味特徵的技術。              | 本系統核心技術             |
| VOC（Volatile Organic Compounds）        | 揮發性有機化合物，水果成熟時會釋放不同種類與濃度的 VOC。            | 成熟度判斷依據             |
| 鳳梨成熟度辨識                                | 透過感測器蒐集 VOC 資料並利用機器學習模型判斷鳳梨成熟階段。          | 系統主要功能              |
| Stage 0                                | 未熟（Unripe）階段。                             | 四階段成熟度之一            |
| Stage 1                                | 初熟（Early Ripe）階段。                         | 四階段成熟度之一            |
| Stage 2                                | 成熟（Ripe）階段。                               | 最佳食用狀態              |
| Stage 3                                | 過熟（Overripe）階段。                           | 建議盡快食用              |
| Air Baseline                           | 空氣基線值，於無鳳梨環境下建立的感測器參考值。                   | 校正依據                |
| Calibration                            | 校正程序，用於建立空氣基準值。                           | 掃描前執行               |
| Guard Baseline                         | 基準線保護機制，避免空氣樣本被誤判為成熟鳳梨。                   | 後處理機制               |
| Override                               | 模型推論後的覆寫規則，用於修正特定成熟度判斷。                   | 後處理機制               |
| Arduino Mega 2560                      | 負責讀取感測器資料並傳送至 Raspberry Pi 的微控制器。         | 感測層核心設備             |
| Raspberry Pi 3                         | 負責執行資料處理、模型推論與 API 服務的單板電腦。               | 運算層核心設備             |
| Serial Port                            | Arduino 與 Raspberry Pi 之間的序列通訊介面。         | USB Serial          |
| MQ2                                    | 氣體感測器，可偵測可燃性氣體與煙霧。                        | 感測器之一               |
| MQ3                                    | 氣體感測器，對酒精類氣體較敏感。                          | 感測器之一               |
| MQ9                                    | 氣體感測器，可偵測一氧化碳與可燃氣體。                       | 感測器之一               |
| MQ135                                  | 氣體感測器，可偵測空氣品質與氨氣。                         | 感測器之一               |
| TGS2602                                | 高靈敏度 VOC 感測器。                             | 重要特徵來源              |
| BME280                                 | 溫度、濕度與氣壓感測器。                              | 環境監測                |
| Feature Engineering                    | 特徵工程，將原始感測資料轉換為模型可使用的特徵。                  | 機器學習流程              |
| Feature Vector                         | 特徵向量，由多項特徵組成的輸入資料。                        | 模型輸入                |
| Deployment Feature                     | 部署特徵，實際系統推論使用的特徵集合。                       | 模型輸入資料              |
| ExtraTrees                             | Extremely Randomized Trees，部署端使用的成熟度分類模型。 | Student Model       |
| CatBoost                               | 訓練階段使用的機器學習模型。                            | Teacher Model       |
| Teacher Model                          | 知識蒸餾流程中的教師模型。                             | CatBoost            |
| Student Model                          | 知識蒸餾後實際部署的模型。                             | ExtraTrees          |
| Knowledge Distillation                 | 知識蒸餾技術，將 Teacher 模型知識轉移至 Student 模型。      | 模型壓縮方法              |
| Pseudo Labeling                        | 偽標籤技術，以模型預測結果擴增訓練資料。                      | 提升資料量               |
| Inference                              | 推論程序，利用訓練完成之模型產生預測結果。                     | 模型執行階段              |
| Confidence                             | 信心值，表示模型對預測結果的可信程度。                       | 百分比表示               |
| Probability Distribution               | 機率分布，模型對各成熟度階段的預測機率。                      | Stage 0～3           |
| API（Application Programming Interface） | 應用程式介面，用於系統模組間資料交換。                       | 前後端溝通               |
| Flask                                  | Python Web Framework，用於建立 API 與後端服務。      | 後端框架                |
| React Native                           | 用於開發跨平台手機 App 的框架。                        | App 開發技術            |
| Expo                                   | React Native 開發與部署平台。                     | App 開發工具            |
| History Record                         | 歷史紀錄，儲存過往檢測結果。                            | App 功能              |
| Batch                                  | 批次資料，農民端管理多顆鳳梨的集合。                        | 農民功能                |
| Batch Scan                             | 批次掃描，連續檢測多顆鳳梨。                            | 農民功能                |
| Batch Result                           | 批次結果，統計整批鳳梨之成熟度分布。                        | 農民功能                |
| Report                                 | 報表，批次分析結果之輸出文件。                           | PDF 或統計圖表           |
| YOLOv8n                                | 物件偵測模型，用於判斷照片中是否存在鳳梨。                     | 品種辨識前處理             |
| EfficientNet-B0                        | 影像分類模型，用於鳳梨品種辨識。                          | 品種辨識模型              |
| 品種辨識                                   | 透過照片分析辨識鳳梨品種。                             | 附加功能                |
| 金鑽鳳梨                                   | 鳳梨品種之一。                                   | 品種分類                |
| 土鳳梨                                    | 鳳梨品種之一。                                   | 品種分類                |
| 牛奶鳳梨                                   | 鳳梨品種之一。                                   | 品種分類                |
| 西瓜鳳梨                                   | 鳳梨品種之一。                                   | 品種分類                |
| Docker                                 | 容器化技術，用於建立一致的執行環境。                        | 備援部署                |
| Docker Container                       | Docker 執行中的應用程式實例。                        | VM 備援服務             |
| VM（Virtual Machine）                    | 虛擬機器環境，用於部署 Docker 備援服務。                  | 學校 VM               |
| Local Storage                          | App 本地儲存機制，用於保存歷史紀錄。                      | 目前採用                |
| Database                               | 資料庫，用於未來儲存使用者、批次與檢測資料。                    | 預留擴充                |
| User                                   | 系統使用者。                                    | 消費者或農民              |
| Device                                 | 感測設備資訊。                                   | Raspberry Pi 與感測器系統 |
| Detection Record                       | 單次成熟度檢測紀錄。                                | 未來資料庫欄位             |
| Variety Detection                      | 品種辨識紀錄。                                   | 未來資料庫欄位             |

---

**詞彙表維護原則：**

1. 若新增感測器、模型或系統功能，應同步更新本詞彙表。
2. 名稱以系統實際實作版本為準。
3. 詞彙表作為後續使用案例、活動圖與類別圖之共同參考依據。
