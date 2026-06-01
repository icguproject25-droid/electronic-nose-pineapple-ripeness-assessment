/**
 * 農民端 App 共用型別定義。
 *
 * 這個檔案集中定義批次、掃描紀錄與 API 回傳資料的資料格式，
 * 讓頁面、store、service 之間可以使用同一套型別，降低欄位名稱不一致造成的錯誤。
 */

/** 鳳梨成熟度狀態。 */
export type Ripeness = 'unripe' | 'ripe' | 'overripe';

/** 批次目前處理狀態。 */
export type BatchStatus = 'draft' | 'testing' | 'done';

/** 黑心病風險等級。 */
export type RiskLevel = 'low' | 'med' | 'high';

/** 異常判斷結果。 */
export type AnomalyFlag = 'normal' | 'isolate';

/**
 * 單顆鳳梨掃描結果。
 *
 * scan/start API 或 mock fallback 都會整理成這個格式，
 * 方便批次統計與報表頁直接使用。
 */
export interface ScanRecord {
  id: string;
  batchId: string;
  createdAt: string;
  ripeness: Ripeness;
  tssBrix: number;
  blackheartRisk: RiskLevel;
  anomalyFlag: AnomalyFlag;
  confidence: number;
}

/**
 * 批次資料。
 *
 * 一個批次代表同一田區、同一採收日或同一用途的一組鳳梨檢測紀錄。
 */
export interface Batch {
  id: string;
  name: string;
  field: string;
  variety: string;
  usage: 'export' | 'domestic' | 'processing';
  targetSamples: number;
  status: BatchStatus;
  createdAt: string;
  scans: ScanRecord[];
}

/**
 * RPi / Gateway 的掃描 API 原始回傳格式。
 *
 * 後端目前可能回傳 ripeness、tss_brix、blackheart_risk 等 snake_case 欄位，
 * 前端會在 services/api.ts 轉成 ScanRecord 使用的 camelCase 欄位。
 */
export interface ScanApiResponse {
  ripeness: Ripeness;
  tss_brix?: number;
  blackheart_risk?: RiskLevel;
  anomaly_flag?: AnomalyFlag;
  confidence?: number;
}

/** App 設定狀態。 */
export interface FarmerSettings {
  apiBaseUrl: string;
  language: 'zh' | 'en';
  exportBrixThreshold: number;
  domesticBrixThreshold: number;
  sampleRatio: number;
}
