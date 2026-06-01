import type { AnomalyFlag, RiskLevel, Ripeness, ScanApiResponse } from '@/types';

/**
 * 農民端 App 與 Raspberry Pi / Gateway 溝通的 API 封裝。
 *
 * 設計重點：
 * 1. 頁面不直接使用 fetch，統一由這個檔案處理 API 呼叫。
 * 2. 後端離線時可以回傳 mock 結果，方便比賽或簡報現場展示完整流程。
 * 3. 將後端 snake_case 欄位轉成前端容易使用的資料格式。
 */

/** 預設後端位置；實際使用時可在 Settings 頁改成 RPi IP。 */
export const DEFAULT_API_BASE_URL = 'http://172.20.10.2:5000';

/**
 * 檢查後端是否在線。
 *
 * @param apiBaseUrl 使用者設定的 RPi 或 Gateway URL。
 * @returns true 代表 /ping 有成功回應，false 代表連線失敗。
 */
export async function pingServer(apiBaseUrl: string): Promise<boolean> {
  try {
    const response = await fetch(`${apiBaseUrl}/ping`, { method: 'GET' });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * 呼叫後端觸發一次 30 秒電子鼻掃描。
 *
 * @param apiBaseUrl 使用者設定的 RPi 或 Gateway URL。
 * @param enableMockFallback 後端失敗時是否使用本機 mock 資料。
 * @returns 掃描結果。
 */
export async function startScan(
  apiBaseUrl: string,
  enableMockFallback = true
): Promise<Required<ScanApiResponse>> {
  try {
    const response = await fetch(`${apiBaseUrl}/scan/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Scan API failed with status ${response.status}`);
    }

    const data = (await response.json()) as ScanApiResponse;
    return normalizeScanResponse(data);
  } catch (error) {
    if (!enableMockFallback) {
      throw error;
    }

    return createMockScanResponse();
  }
}

/**
 * 將後端回傳結果補齊預設值。
 *
 * 有些後端只回傳成熟度與信心值，農民端仍需要糖度、黑心病風險與異常旗標，
 * 因此這裡用安全預設值補足欄位，避免 UI 因 undefined 當掉。
 */
function normalizeScanResponse(data: ScanApiResponse): Required<ScanApiResponse> {
  return {
    ripeness: data.ripeness ?? 'ripe',
    tss_brix: data.tss_brix ?? 14.5,
    blackheart_risk: data.blackheart_risk ?? 'low',
    anomaly_flag: data.anomaly_flag ?? 'normal',
    confidence: data.confidence ?? 0.82
  };
}

/**
 * 建立展示用 mock 掃描結果。
 *
 * 這個結果不是模型真實推論，只用於後端未啟動時讓 App 流程可以完整展示。
 */
function createMockScanResponse(): Required<ScanApiResponse> {
  const ripenessPool: Ripeness[] = ['unripe', 'ripe', 'overripe'];
  const riskPool: RiskLevel[] = ['low', 'med', 'high'];
  const anomalyPool: AnomalyFlag[] = ['normal', 'normal', 'normal', 'isolate'];

  const ripeness = pickOne(ripenessPool);
  const risk = pickOne(riskPool);
  const anomaly = pickOne(anomalyPool);

  return {
    ripeness,
    tss_brix: Number((12 + Math.random() * 5).toFixed(1)),
    blackheart_risk: risk,
    anomaly_flag: anomaly,
    confidence: Number((0.72 + Math.random() * 0.22).toFixed(2))
  };
}

/** 從陣列中隨機取出一個值。 */
function pickOne<T>(items: T[]): T {
  return items[Math.floor(Math.random() * items.length)];
}
