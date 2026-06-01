export type I18nKey =
  | "appName"
  | "loginTitle"
  | "pinPlaceholder"
  | "enter"
  | "demoMode"
  | "invalidPin"
  | "home"
  | "batches"
  | "scan"
  | "reports"
  | "settings"
  | "currentBatch"
  | "todayStats"
  | "startScan"
  | "newBatch"
  | "recentBatches"
  | "noData"
  | "summary"
  | "doneBatches"
  | "testingBatches";

export type Language = "zh" | "en";

export const dictionary: Record<Language, Record<I18nKey, string>> = {
  zh: {
    appName: "Pineapple E-Nose Farmer",
    loginTitle: "農民端批次檢測系統",
    pinPlaceholder: "請輸入 1234",
    enter: "登入",
    demoMode: "Demo 模式",
    invalidPin: "PIN 錯誤，請輸入 1234。",
    home: "首頁",
    batches: "批次",
    scan: "掃描",
    reports: "報告",
    settings: "設定",
    currentBatch: "目前批次",
    todayStats: "今日檢測概況",
    startScan: "開始掃描",
    newBatch: "建立批次",
    recentBatches: "最近批次",
    noData: "目前沒有資料",
    summary: "摘要",
    doneBatches: "完成",
    testingBatches: "檢測中",
  },
  en: {
    appName: "Pineapple E-Nose Farmer",
    loginTitle: "Farmer Batch Detection System",
    pinPlaceholder: "Enter 1234",
    enter: "Login",
    demoMode: "Demo Mode",
    invalidPin: "Invalid PIN. Please enter 1234.",
    home: "Home",
    batches: "Batches",
    scan: "Scan",
    reports: "Reports",
    settings: "Settings",
    currentBatch: "Current Batch",
    todayStats: "Today Overview",
    startScan: "Start Scan",
    newBatch: "New Batch",
    recentBatches: "Recent Batches",
    noData: "No data",
    summary: "Summary",
    doneBatches: "Done",
    testingBatches: "Testing",
  },
};

export function t(language: Language, key: I18nKey): string {
  return dictionary[language][key] ?? key;
}
