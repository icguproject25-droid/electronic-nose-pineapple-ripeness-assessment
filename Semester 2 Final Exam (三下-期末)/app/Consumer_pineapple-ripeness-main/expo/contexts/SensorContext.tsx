import { useState, useCallback, useEffect, useRef } from 'react';
import createContextHook from '@nkzw/create-context-hook';
import { SensorData, RipenessLevel, processSensorData, ProcessedSensorData } from '@/utils/ripeness';
import { ScanMetadata, apiFetchRipenessMock, RipenessMockResult, apiStartScan, apiGetStatus, RpiScanResult } from '@/services/api';
import { getApiBaseUrl, setApiBaseUrl as persistApiBaseUrl, DEFAULT_API_URL } from '@/services/storage';

export interface StageProbabilities {
  stage0: number;
  stage1: number;
  stage2: number;
  stage3: number;
}

export interface ScanResult {
  id: string;
  timestamp: Date;
  rawData: SensorData;
  processedData: ProcessedSensorData;
  ripeness: RipenessLevel;
  metadata?: ScanMetadata;
  /** 0~1 confidence from server */
  confidence?: number;
  /** 0~100 maturity percent from server */
  maturityPercent?: number;
  /** Suggestion text from server (zh) */
  suggestion?: string;
  /** Server-provided localized ripeness labels */
  ripenessLabelZh?: string;
  ripenessLabelEn?: string;
  /** Per-stage probabilities (0~1) */
  probabilities?: StageProbabilities;
}

function stageToRipeness(stage: number): RipenessLevel {
  switch (stage) {
    case 0: return 'unripe';
    case 1: return 'transition';
    case 2: return 'ripe';
    case 3: return 'overripe';
    default: return 'unripe';
  }
}

function mapMockToSensorData(rpi: RipenessMockResult): SensorData {
  return {
    MQ2_raw: rpi.sensor_summary.MQ2,
    MQ3_raw: rpi.sensor_summary.MQ3,
    MQ9_raw: rpi.sensor_summary.MQ9,
    MQ135_raw: rpi.sensor_summary.MQ135,
    TGS2602_raw: rpi.sensor_summary.TGS2602,
    Temp_C: rpi.sensor_summary.Temp_C,
    Humidity_pct: rpi.sensor_summary.Humidity_pct,
    Pressure_hPa: rpi.sensor_summary.Pressure_hPa,
  };
}

export const [SensorProvider, useSensor] = createContextHook(() => {
  const [currentResult, setCurrentResult] = useState<ScanResult | null>(null);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanMetadata, setScanMetadata] = useState<ScanMetadata>({});
  const [baseUrl, setBaseUrlState] = useState<string>(DEFAULT_API_URL);
  const isMountedRef = useRef<boolean>(true);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const url = await getApiBaseUrl();
      if (!cancelled) setBaseUrlState(url);
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const updateBaseUrl = useCallback(async (url: string): Promise<void> => {
    await persistApiBaseUrl(url);
    setBaseUrlState(url);
  }, []);

  const updateMetadata = useCallback((metadata: Partial<ScanMetadata>) => {
    setScanMetadata(prev => ({ ...prev, ...metadata }));
  }, []);

  const clearMetadata = useCallback(() => {
    setScanMetadata({});
  }, []);

  const startScan = useCallback(async (): Promise<ScanResult> => {
    setIsScanning(true);

    const POLL_INTERVAL_MS = 1500;
    const POLL_TIMEOUT_MS = 120_000;

    const sleep = (ms: number) => new Promise<void>((res) => setTimeout(res, ms));

    try {
      const currentUrl = await getApiBaseUrl();
      console.log('[SensorContext] startScan calling URL:', currentUrl);
      // 1. 觸發 RPi 開始掃描
      await apiStartScan();

      // 2. 使用 async while loop 輪詢，永遠只會有一個 in-flight request
      const startedAt = Date.now();
      let rpiResult: RpiScanResult | null = null;

      while (true) {
        if (Date.now() - startedAt > POLL_TIMEOUT_MS) {
          throw new Error('SCAN_TIMEOUT');
        }

        let status: Awaited<ReturnType<typeof apiGetStatus>> | null = null;
        try {
          status = await apiGetStatus();
          console.log('[SensorContext] poll status:', status.status, status.progress);
        } catch (err) {
          console.log('[SensorContext] apiGetStatus failed:', err);
          status = null;
        }

        if (status) {
          if (status.status === 'done' && status.result) {
            rpiResult = status.result;
            break;
          }
          if (status.status === 'error') {
            throw new Error(status.error ?? '感測失敗');
          }
        }

        await sleep(POLL_INTERVAL_MS);
      }

      if (!rpiResult) {
        throw new Error('SCAN_TIMEOUT');
      }

      // 3. 直接 mapping，不做前端二次計算
      const processedData: ProcessedSensorData = {
        smokeFlammable: rpiResult.sensor_percent.MQ2,
        alcoholLevel: rpiResult.sensor_percent.MQ3,
        carbonMonoxide: rpiResult.sensor_percent.MQ9,
        airQuality: rpiResult.sensor_percent.MQ135,
        odorIntensity: rpiResult.sensor_percent.TGS2602,
        temperature: rpiResult.environment.temperature ?? 25,
        humidity: rpiResult.environment.humidity ?? 65,
        pressure: rpiResult.environment.pressure ?? 1013,
      };

      // rawData 存 sensor_raw（ADC 原始值，供上傳用）
      const rawData: SensorData = {
        MQ2_raw: rpiResult.sensor_raw?.MQ2 ?? rpiResult.sensor_percent.MQ2,
        MQ3_raw: rpiResult.sensor_raw?.MQ3 ?? rpiResult.sensor_percent.MQ3,
        MQ9_raw: rpiResult.sensor_raw?.MQ9 ?? rpiResult.sensor_percent.MQ9,
        MQ135_raw: rpiResult.sensor_raw?.MQ135 ?? rpiResult.sensor_percent.MQ135,
        TGS2602_raw: rpiResult.sensor_raw?.TGS2602 ?? rpiResult.sensor_percent.TGS2602,
        Temp_C: rpiResult.environment.temperature ?? 25,
        Humidity_pct: rpiResult.environment.humidity ?? 65,
        Pressure_hPa: rpiResult.environment.pressure ?? 1013,
      };

      const probabilities: StageProbabilities = {
        stage0: rpiResult.probabilities.stage0 ?? 0,
        stage1: rpiResult.probabilities.stage1 ?? 0,
        stage2: rpiResult.probabilities.stage2 ?? 0,
        stage3: rpiResult.probabilities.stage3 ?? 0,
      };

      const result: ScanResult = {
        id: rpiResult.id || Date.now().toString(),
        timestamp: new Date(),
        rawData,
        processedData,
        ripeness: rpiResult.ripeness,
        metadata: { ...scanMetadata },
        confidence: rpiResult.confidence,
        maturityPercent: rpiResult.maturityPercent ?? rpiResult.percent,
        ripenessLabelZh: rpiResult.ripenessLabelZh ?? rpiResult.label_zh,
        ripenessLabelEn: rpiResult.ripenessLabelEn,
        suggestion:
          rpiResult.suggestion
          ?? (rpiResult.suggestions?.[0])
          ?? rpiResult.display_text,
        probabilities,
      };

      if (isMountedRef.current) {
        setCurrentResult(result);
        setIsScanning(false);
      }
      return result;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      console.error('[SensorContext] startScan error:', msg);
      if (isMountedRef.current) {
        setIsScanning(false);
      }
      // NO_AIR_BASE 和其他錯誤都直接拋出，不 fallback 假資料
      throw e instanceof Error ? e : new Error(msg);
    }
  }, [scanMetadata]);

  const submitFeedback = useCallback(async (resultId: string, correctRipeness: RipenessLevel) => {
    console.log('Feedback submitted:', { resultId, correctRipeness });
    console.log('Raw data for ML training:', currentResult?.rawData);
  }, [currentResult]);

  const clearResult = useCallback(() => {
    setCurrentResult(null);
    clearMetadata();
  }, [clearMetadata]);

  return {
    currentResult,
    isScanning,
    scanMetadata,
    startScan,
    submitFeedback,
    clearResult,
    updateMetadata,
    clearMetadata,
    baseUrl,
    updateBaseUrl,
  };
});
