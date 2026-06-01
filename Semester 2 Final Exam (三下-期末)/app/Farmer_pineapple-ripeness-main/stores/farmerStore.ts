import { create } from 'zustand';
import type { Batch, FarmerSettings, ScanRecord } from '@/types';
import { DEFAULT_API_BASE_URL } from '@/services/api';

/**
 * 農民端 App 的集中式狀態管理。
 *
 * 使用 Zustand 的原因：
 * - 寫法簡單，不需要大量 boilerplate。
 * - 適合本專題展示用的批次、掃描紀錄與設定管理。
 * - 各頁面可以直接讀取同一份資料，不需要層層傳 props。
 */

interface FarmerState {
  /** 所有批次資料。 */
  batches: Batch[];

  /** 目前正在操作的批次 ID。 */
  activeBatchId: string | null;

  /** App 設定，例如 RPi URL、語言與糖度門檻。 */
  settings: FarmerSettings;

  /** 新增一個空批次。 */
  createBatch: (input: Omit<Batch, 'id' | 'createdAt' | 'status' | 'scans'>) => string;

  /** 設定目前操作中的批次。 */
  setActiveBatch: (batchId: string) => void;

  /** 把單筆掃描結果加入指定批次。 */
  addScanToBatch: (batchId: string, scan: Omit<ScanRecord, 'id' | 'batchId' | 'createdAt'>) => void;

  /** 將批次狀態改成完成。 */
  completeBatch: (batchId: string) => void;

  /** 更新 App 設定。 */
  updateSettings: (settings: Partial<FarmerSettings>) => void;
}

/** 建立簡單唯一 ID，避免展示專案額外安裝 uuid 套件。 */
function createId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

/**
 * 預設範例批次。
 *
 * 讓 App 第一次打開時不是空白畫面，也方便老師或評審看到功能入口。
 */
const demoBatch: Batch = {
  id: 'batch-demo-001',
  name: 'A 區金鑽鳳梨採收批次',
  field: 'A-01',
  variety: '金鑽鳳梨',
  usage: 'export',
  targetSamples: 10,
  status: 'testing',
  createdAt: new Date().toISOString(),
  scans: []
};

export const useFarmerStore = create<FarmerState>((set) => ({
  batches: [demoBatch],
  activeBatchId: demoBatch.id,
  settings: {
    apiBaseUrl: DEFAULT_API_BASE_URL,
    language: 'zh',
    exportBrixThreshold: 14,
    domesticBrixThreshold: 12,
    sampleRatio: 0.1
  },

  createBatch: (input) => {
    const id = createId('batch');
    const batch: Batch = {
      ...input,
      id,
      createdAt: new Date().toISOString(),
      status: 'draft',
      scans: []
    };

    set((state) => ({
      batches: [batch, ...state.batches],
      activeBatchId: id
    }));

    return id;
  },

  setActiveBatch: (batchId) => {
    set({ activeBatchId: batchId });
  },

  addScanToBatch: (batchId, scan) => {
    const record: ScanRecord = {
      ...scan,
      id: createId('scan'),
      batchId,
      createdAt: new Date().toISOString()
    };

    set((state) => ({
      batches: state.batches.map((batch) => {
        if (batch.id !== batchId) return batch;

        return {
          ...batch,
          status: 'testing',
          scans: [record, ...batch.scans]
        };
      })
    }));
  },

  completeBatch: (batchId) => {
    set((state) => ({
      batches: state.batches.map((batch) =>
        batch.id === batchId ? { ...batch, status: 'done' } : batch
      )
    }));
  },

  updateSettings: (settings) => {
    set((state) => ({
      settings: {
        ...state.settings,
        ...settings
      }
    }));
  }
}));
