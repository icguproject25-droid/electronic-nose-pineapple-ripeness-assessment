# UML 文件

本資料夾放置「水果（鳳梨）電子鼻非破壞性熟度檢測系統」之 UML 與使用案例相關文件。
## Project Link
* GitHub Repository / UML Documents:
[  [electronic-nose-pineapple-ripeness-assessment](https://github.com/icguproject25-droid/electronic-nose-pineapple-ripeness-assessment/tree/main/UML)](https://github.com/icguproject25-droid/electronic-nose-pineapple-ripeness-assessment/tree/main/UML)

## 文件結構

| 章節 | 內容 | 資料夾 |
|---|---|---|
| 第四章 | 詞彙表 | [04-glossary](./04-glossary/) |
| 第五章 | 使用案例圖 | [05-use-case-diagrams](./05-use-case-diagrams/) |
| 第六章 | 使用案例描述與情節 | [06-use-case-scenarios](./06-use-case-scenarios/) |
| 第七章 | 活動圖 | [07-activity-diagrams](./07-activity-diagrams/) |
| 第八章 | 類別圖 | [08-class-diagram](./08-class-diagram/)|

## 第四章說明

第四章內容位於：

`04-glossary/`

此資料夾包含本系統開發過程中所使用之專有名詞、技術名詞與系統術語。

詞彙表內容涵蓋電子鼻系統、VOC 感測器、鳳梨成熟度分級、Air Baseline 校正、機器學習模型、批次管理功能、照片品種辨識功能與系統部署相關技術，用以統一後續文件中的名詞定義與說明。

## 第五章說明

第五章內容位於：

`05-use-case-diagrams/`

此資料夾包含消費端 App、農民端 App、系統端功能與照片品種辨識補充功能之 UML 使用案例圖（Use Case Diagram）。

使用案例圖用於描述各角色與系統功能之互動關係，並呈現系統所提供之主要功能範圍，包含消費者成熟度檢測流程、農民批次管理功能、系統校正與模型推論功能，以及照片品種辨識功能。

## 第六章說明

第六章內容位於：

`06-use-case-scenarios/`

此資料夾包含消費端 App、農民端 App 與系統端功能之使用案例描述，每一個使用案例皆包含正常情節與例外情節。

## 第七章說明

第七章內容位於：

`07-activity-diagrams/`

此資料夾包含消費端 App、農民端 App、系統端功能與照片品種辨識補充功能之活動圖。  
活動圖依據第六章使用案例描述與情節繪製，每一張活動圖皆包含主要流程與例外流程，用來呈現使用者操作、系統處理、判斷條件與錯誤處理。

## 第八章說明

第八章內容位於：

`08-class-diagram/`

此資料夾包含 PineNose 整體資訊系統類別圖，以及依功能拆分的細部類別圖。  
類別圖描述系統中的主要類別、屬性、操作與類別關係，範圍包含使用者、掃描結果、農民批次、報表、感測模組、校正模組、模型推論、App 介面與照片品種辨識功能。
