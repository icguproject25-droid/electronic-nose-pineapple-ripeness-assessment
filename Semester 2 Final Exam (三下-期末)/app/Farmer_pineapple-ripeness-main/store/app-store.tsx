import createContextHook from "@nkzw/create-context-hook";
import { useCallback, useMemo, useState } from "react";

import { I18nKey, t } from "@/constants/i18n";
import { AppSettings, Batch, Language, Sample } from "@/types/models";
import { clamp, createId } from "@/utils/helpers";

interface CreateBatchInput {
  name: string;
  date: string;
  block: string;
  cultivar: string;
  harvest_count: number;
  purpose: Batch["purpose"];
  target_samples: number;
  note?: string;
}

const defaultSettings: AppSettings = {
  language: "zh",
  backendUrl: "http://172.20.10.2:5000",
  thresholds: {
    exportBrix: 15,
    domesticBrix: 13,
    samplingRatio: 0.05,
    minSamples: 5,
    maxSamples: 50,
  },
  device: {
    raspberryPiUrl: "http://172.20.10.2:5000",
    sensorDeviceId: "RPi_ENOSE_001",
    modelVersion: "ExtraTrees_v1",
  },
};

export const [AppProvider, useAppStore] = createContextHook(() => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [samples, setSamples] = useState<Sample[]>([]);

  const login = useCallback((pin: string): boolean => {
    const ok = pin === "1234";
    setIsAuthenticated(ok);
    setIsDemoMode(false);
    return ok;
  }, []);

  const enterDemo = useCallback(() => {
    setIsAuthenticated(true);
    setIsDemoMode(true);
  }, []);

  const logout = useCallback(() => {
    setIsAuthenticated(false);
    setIsDemoMode(false);
  }, []);

  const createBatch = useCallback((input: CreateBatchInput): Batch => {
    const batch: Batch = {
      batch_id: createId("batch"),
      name: input.name,
      date: input.date,
      block: input.block,
      cultivar: input.cultivar,
      harvest_count: input.harvest_count,
      purpose: input.purpose,
      sampling_plan: `ratio:${settings.thresholds.samplingRatio}`,
      target_samples: clamp(input.target_samples, settings.thresholds.minSamples, settings.thresholds.maxSamples),
      status: "testing",
      created_at: new Date().toISOString(),
      note: input.note ?? "",
      synced: false,
    };

    setBatches((prev) => [batch, ...prev]);
    return batch;
  }, [settings.thresholds.maxSamples, settings.thresholds.minSamples, settings.thresholds.samplingRatio]);

  const addSample = useCallback((sample: Sample) => {
    setSamples((prev) => [sample, ...prev]);
  }, []);

  const updateBatchStatus = useCallback((batchId: string, status: Batch["status"]) => {
    setBatches((prev) => prev.map((batch) => (batch.batch_id === batchId ? { ...batch, status, synced: false } : batch)));
  }, []);

  const setLanguage = useCallback((language: Language) => {
    setSettings((prev) => ({ ...prev, language }));
  }, []);

  const updateSettings = useCallback((next: Partial<AppSettings>) => {
    setSettings((prev) => ({
      ...prev,
      ...next,
      thresholds: { ...prev.thresholds, ...(next.thresholds ?? {}) },
      device: { ...prev.device, ...(next.device ?? {}) },
    }));
  }, []);

  const unsyncedBatchCount = useMemo(() => batches.filter((item) => item.synced !== true).length, [batches]);
  const tx = useCallback((key: I18nKey): string => t(settings.language, key), [settings.language]);

  return {
    isAuthenticated,
    isDemoMode,
    batches,
    samples,
    settings,
    unsyncedBatchCount,
    login,
    enterDemo,
    logout,
    createBatch,
    addSample,
    updateBatchStatus,
    setLanguage,
    updateSettings,
    tx,
  };
});
