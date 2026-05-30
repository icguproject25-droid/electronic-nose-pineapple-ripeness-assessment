/**
 * services/api.ts  ← 直接替換掉原本的檔案
 *
 * 這版本對接真實 app_gateway_v2.py
 * 只有 Raspberry Pi 的 API 部分有改動，其他 uploadScanRecord、
 * uploadHistoryRecord 等維持不變。
 */

import Constants from 'expo-constants';
import * as Linking from 'expo-linking';
import { ScanRecord, toUploadPayload } from '@/types/scanRecord';
import { getApiBaseUrl, getOrCreateDeviceId, getVarietyApiBaseUrl } from '@/services/storage';
import { RipenessLevel, SensorData } from '@/utils/ripeness';


// ─────────────────────────────────────────────────────────
// 型別定義（原本的，不動）
// ─────────────────────────────────────────────────────────

export type AnomalyFlag = 'none' | 'spike' | 'drift' | 'saturation';

export interface ScanMetadata {
  fruit_id?: string;
  dist_cm?: number;
  note?: string;
  device_id?: string;
}

export interface ScanRecordPayload {
  timestamp_iso: string;
  fruit_id: string;
  dist_cm: number | null;
  MQ2_raw: number;
  MQ3_raw: number;
  MQ9_raw: number;
  MQ135_raw: number;
  TGS2602_raw: number;
  Temp_C: number;
  Humidity_pct: number;
  Pressure_hPa: number;
  ripeness_pred: RipenessLevel;
  confidence: number;
  anomaly_flag: AnomalyFlag;
  locale: string;
  device_id: string;
  model_version: string;
  app_version: string;
  note: string;
}

export interface FeedbackPayload {
  correct_label: RipenessLevel;
  comment?: string;
}

export interface ScanRecordResponse {
  id: string;
  success: boolean;
  message?: string;
}

export interface UploadResponse {
  ok: boolean;
  id: string;
}

export function getAppVersion(): string {
  try {
    return Constants.expoConfig?.version || '1.0.0';
  } catch {
    return '1.0.0';
  }
}

export function buildScanRecordPayload(
  rawData: SensorData,
  ripeness: RipenessLevel,
  locale: string,
  metadata: ScanMetadata = {}
): ScanRecordPayload {
  return {
    timestamp_iso: new Date().toISOString(),
    fruit_id: metadata.fruit_id || '',
    dist_cm: metadata.dist_cm ?? null,
    MQ2_raw: rawData.MQ2_raw,
    MQ3_raw: rawData.MQ3_raw,
    MQ9_raw: rawData.MQ9_raw,
    MQ135_raw: rawData.MQ135_raw,
    TGS2602_raw: rawData.TGS2602_raw,
    Temp_C: rawData.Temp_C,
    Humidity_pct: rawData.Humidity_pct,
    Pressure_hPa: rawData.Pressure_hPa,
    ripeness_pred: ripeness,
    confidence: 0.7,
    anomaly_flag: 'none',
    locale,
    device_id: '',
    model_version: 'rpi-v2',
    app_version: getAppVersion(),
    note: metadata.note || '',
  };
}

// ─────────────────────────────────────────────────────────
// HTTP 工具
// ─────────────────────────────────────────────────────────

const RPI_HEADERS = {
  'Content-Type': 'application/json',
  'ngrok-skip-browser-warning': 'true',
};

function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeoutMs = 60000
): Promise<Response> {
  return new Promise((resolve, reject) => {
    const ctrl  = new AbortController();
    const timer = setTimeout(() => {
      ctrl.abort();
      reject(new Error(`Request timeout after ${timeoutMs}ms`));
    }, timeoutMs);
    fetch(url, { ...options, signal: ctrl.signal })
      .then((res) => { clearTimeout(timer); resolve(res); })
      .catch((err) => { clearTimeout(timer); reject(err); });
  });
}

// ─────────────────────────────────────────────────────────
// 上傳 / Feedback（原本的，不動）
// ─────────────────────────────────────────────────────────

export async function uploadScanRecord(
  payload: ScanRecordPayload
): Promise<ScanRecordResponse> {
  const apiBaseUrl = await getApiBaseUrl();
  try {
    const response = await fetch(`${apiBaseUrl}/scan_records`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    return { id: data.id || payload.timestamp_iso, success: true };
  } catch (error) {
    console.log('[API] Upload failed:', error);
    throw error;
  }
}

export async function uploadHistoryRecord(
  record: ScanRecord
): Promise<UploadResponse> {
  const apiBaseUrl = await getApiBaseUrl();
  const payload    = toUploadPayload(record);
  try {
    const response = await fetch(`${apiBaseUrl}/scan_records`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    return { ok: true, id: data.id || record.local_id };
  } catch (error) {
    console.log('[API] Upload failed:', error);
    throw error;
  }
}

export async function submitFeedbackToServer(
  recordId: string,
  feedback: FeedbackPayload
): Promise<boolean> {
  const apiBaseUrl = await getApiBaseUrl();
  try {
    const response = await fetch(`${apiBaseUrl}/scan_records/${recordId}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
      body: JSON.stringify(feedback),
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return true;
  } catch (error) {
    console.log('[API] Feedback submission failed:', error);
    throw error;
  }
}

export async function openExportExcel(): Promise<void> {
  const apiBaseUrl = await getApiBaseUrl();
  const exportUrl  = `${apiBaseUrl}/scan_records/export.xlsx`;
  try {
    await fetch(exportUrl, { method: 'GET', headers: { 'ngrok-skip-browser-warning': 'true' } });
  } catch {}
  Linking.openURL(exportUrl);
}

export { getOrCreateDeviceId };

// ─────────────────────────────────────────────────────────
// Raspberry Pi 感測 API
// ─────────────────────────────────────────────────────────

/**
 * 對應 app_gateway_v2.py 的 /status 回傳格式
 * 也對應 SensorContext.tsx 裡的 RpiScanResult
 */
export interface RpiScanResult {
  id: string;
  timestamp: string;
  stage: 0 | 1 | 2 | 3;
  ripeness: 'unripe' | 'transition' | 'ripe' | 'overripe';
  label_zh: string;
  display_text: string;
  percent: number;
  probabilities: {
    stage0: number;
    stage1: number;
    stage2: number;
    stage3: number;
  };
  sensor_percent: {
    MQ2: number;
    MQ3: number;
    MQ9: number;
    MQ135: number;
    TGS2602: number;
  };
  sensor_raw?: {
    MQ2: number;
    MQ3: number;
    MQ9: number;
    MQ135: number;
    TGS2602: number;
  };
  environment: {
    temperature: number | null;
    humidity: number | null;
    pressure: number | null;
  };
  suggestions: string[];
  suggestion: string;
  confidence: number;
  maturityPercent?: number;
  ripenessLabelZh: string;
  ripenessLabelEn: string;
  guard_triggered: boolean;
  override_used: boolean;
}

export interface RpiStatus {
  status: 'idle' | 'calibrating' | 'scanning' | 'done' | 'error';
  progress: number;
  result: RpiScanResult | null;
  error: string | null;
}

export interface RpiHealth {
  status: 'ok';
  air_base_exists: boolean;
  air_calibrated_at: string | null;
  time: string;
}

// ── /health ──────────────────────────────────────────────
export async function apiCheckHealth(): Promise<RpiHealth> {
  const base = await getApiBaseUrl();
  const res  = await fetchWithTimeout(
    `${base}/health`,
    { headers: RPI_HEADERS },
    8000
  );
  if (!res.ok) throw new Error(`Health check failed: HTTP ${res.status}`);
  return res.json();
}

// ── POST /calibrate ───────────────────────────────────────
export async function apiStartCalibration(): Promise<void> {
  const base = await getApiBaseUrl();
  const res  = await fetchWithTimeout(
    `${base}/calibrate`,
    { method: 'POST', headers: RPI_HEADERS },
    10000
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
}

// ── POST /scan ────────────────────────────────────────────
/**
 * 觸發樹莓派開始感測（不等結果）。
 * warmup_sec = 0  → 快速 (30s)
 * warmup_sec = 60 → 標準 (90s)
 * warmup_sec = 180→ 完整 (210s)
 */
export async function apiStartScan(
  warmup_sec = 0
): Promise<{ ok: boolean; scan_id?: string } | void> {
  const base = await getApiBaseUrl();

  const res = await fetchWithTimeout(
    `${base}/scan`,
    {
      method: 'POST',
      headers: {
        ...RPI_HEADERS,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ warmup_sec }),
    },
    120000
  );

  if (res.ok) {
    return await res.json();
  }

  const body = await res.json().catch(() => ({} as { error?: string }));
  const errCode = body.error ?? `HTTP ${res.status}`;

  if (errCode === 'BUSY' || res.status === 409) {
    console.log('[API] /scan BUSY，繼續 poll /status');
    return;
  }

  if (errCode === 'NO_AIR_BASE') throw new Error('NO_AIR_BASE');
  throw new Error(errCode);
}

// ── GET /status ───────────────────────────────────────────
export async function apiGetStatus(): Promise<RpiStatus> {
  const base = await getApiBaseUrl();
  const res  = await fetchWithTimeout(
    `${base}/status`,
    { headers: RPI_HEADERS },
    8000
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ─────────────────────────────────────────────────────────
// Mock ripeness（離線 fallback，不改動）
// ─────────────────────────────────────────────────────────

export interface RipenessMockSensorSummary {
  MQ2: number; MQ3: number; MQ9: number;
  MQ135: number; TGS2602: number;
  TGS2620?: number;
  Temp_C: number; Humidity_pct: number; Pressure_hPa: number;
}

export interface RipenessMockResult {
  status: string;
  stage: 0 | 1 | 2 | 3;
  ripeness: string;
  ripeness_en: string;
  confidence: number;
  maturity_percent: number;
  suggestion: string;
  probabilities: {
    stage_0: number; stage_1: number; stage_2: number; stage_3: number;
  };
  sensor_summary: RipenessMockSensorSummary;
}

function buildOfflineMock(): RipenessMockResult {
  const stages: Array<0 | 1 | 2 | 3> = [0, 1, 2, 3];
  const stage   = stages[Math.floor(Math.random() * stages.length)];
  const labelsZh = ['未熟', '初熟', '完熟', '過熟'];
  const labelsEn = ['Unripe', 'Early ripe', 'Ripe', 'Overripe'];
  const suggestions = [
    '建議再等待 3-5 天',
    '建議再等 1-2 天風味更佳',
    '立即食用，風味最佳',
    '盡快食用，避免過熟',
  ];
  const probs = [0.05, 0.05, 0.05, 0.05];
  probs[stage] = 0.85;
  return {
    status: 'success-offline',
    stage,
    ripeness: labelsZh[stage],
    ripeness_en: labelsEn[stage],
    confidence: 0.85,
    maturity_percent: [20, 50, 85, 95][stage],
    suggestion: suggestions[stage],
    probabilities: {
      stage_0: probs[0], stage_1: probs[1],
      stage_2: probs[2], stage_3: probs[3],
    },
    sensor_summary: {
      MQ2: 271.28, MQ3: 339.0, MQ9: 707.9,
      MQ135: 327.17, TGS2602: 734.0,
      Temp_C: 26.63, Humidity_pct: 46.3, Pressure_hPa: 1013.18,
    },
  };
}

export async function apiFetchRipenessMock(): Promise<RipenessMockResult> {
  const base = await getApiBaseUrl();
  const url  = `${base}/ripeness/mock`;
  try {
    const res = await fetchWithTimeout(url, { method: 'POST', headers: RPI_HEADERS }, 8000);
    if (!res.ok) throw new Error(`POST HTTP ${res.status}`);
    return (await res.json()) as RipenessMockResult;
  } catch {
    try {
      const res = await fetchWithTimeout(
        url,
        { method: 'GET', headers: { 'ngrok-skip-browser-warning': 'true' } },
        8000
      );
      if (!res.ok) throw new Error(`GET HTTP ${res.status}`);
      return (await res.json()) as RipenessMockResult;
    } catch (err) {
      console.warn('[API] 後端不可達，使用離線 mock。原因：', err);
      return buildOfflineMock();
    }
  }
}

// ─────────────────────────────────────────────────────────
// 鳳梨品種辨識 API
// ─────────────────────────────────────────────────────────

export interface VarietyProbability {
  class?: string;
  zh_name?: string;
  probability?: number;
}

export interface VarietyPredictResult {
  status: string;
  filename?: string;

  // 新版 API 可能會是 null
  pred_class: string | null;
  pred_zh_name: string | null;

  confidence: number;
  low_confidence: boolean;
  all_probs: VarietyProbability[];

  // 新版 YOLO 偵測欄位
  message?: string;
  stage?: number;
  has_content?: boolean;
  is_pineapple?: boolean;
  det_confidence?: number;
  bbox?: number[] | null;
  num_boxes?: number;

  content_check?: {
    edge_ratio?: number;
    has_content?: boolean;
    mean_brightness?: number;
    std_brightness?: number;
    message?: string;
  };
}

export async function apiPredictVariety(
  imageUri: string
): Promise<VarietyPredictResult> {
  const varietyBaseUrl = (await getVarietyApiBaseUrl()).replace(/\/+$/, '');

  const formData = new FormData();

  formData.append('image', {
    uri: imageUri,
    name: 'pineapple.jpg',
    type: 'image/jpeg',
  } as any);

  const response = await fetch(`${varietyBaseUrl}/predict`, {
    method: 'POST',
    headers: {
      'ngrok-skip-browser-warning': 'true',
    },
    body: formData,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data?.message ||
      data?.error ||
      `Variety prediction failed (HTTP ${response.status})`
    );
  }

  return data as VarietyPredictResult;
}