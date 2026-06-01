export type Language = "zh" | "en";
export type BatchStatus = "testing" | "done";
export type BatchPurpose = "export" | "domestic" | "processing" | "unknown";
export type Ripeness = "unripe" | "ripe" | "overripe";
export type RiskLevel = "low" | "med" | "high";
export type AnomalyFlag = "normal" | "isolate";

export interface WeatherSnapshot {
  county: string;
  condition: string;
  rainfall_mm: number;
  recorded_at: string;
}

export interface Batch {
  batch_id: string;
  name: string;
  date: string;
  block: string;
  cultivar: string;
  harvest_count: number;
  purpose: BatchPurpose;
  sampling_plan: string;
  target_samples: number;
  status: BatchStatus;
  created_at: string;
  note?: string;
  batch_photo_uri?: string;
  weather?: WeatherSnapshot;
  synced?: boolean;
}

export interface Sample {
  sample_id: string;
  batch_id: string;
  created_at: string;
  ripeness: Ripeness;
  tss_brix: number;
  blackheart_risk: RiskLevel;
  anomaly_flag: AnomalyFlag;
  confidence: number;
  photo_uri?: string;
}

export interface AppSettings {
  language: Language;
  backendUrl: string;
  thresholds: {
    exportBrix: number;
    domesticBrix: number;
    samplingRatio: number;
    minSamples: number;
    maxSamples: number;
  };
  device: {
    raspberryPiUrl: string;
    sensorDeviceId: string;
    modelVersion: string;
  };
}
