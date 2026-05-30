import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert, Platform } from 'react-native';
import { ScanRecord } from '@/types/scanRecord';

const HISTORY_STORAGE_KEY = '@pineapple_scan_history';
const API_URL_STORAGE_KEY = '@pineapple_api_url';
const VARIETY_API_URL_STORAGE_KEY = '@pineapple_variety_api_url';
const NGROK_URL_STORAGE_KEY = '@pineapple_ngrok_url';
const DEVICE_ID_STORAGE_KEY = '@pineapple_device_id';
const METADATA_STORAGE_KEY = '@pineapple_last_metadata';
const MAX_RECORDS = 200;

export interface PersistedMetadata {
  fruit_id?: string;
  dist_cm?: number;
  note?: string;
}

function notifyStorageError(message: string) {
  if (Platform.OS !== 'web') {
    try {
      Alert.alert('Storage Error', message);
    } catch {
      // Alert may be unavailable in some contexts; ignore.
    }
  }
}

export async function saveRecord(record: ScanRecord): Promise<void> {
  try {
    const records = await listRecords();
    const newRecords = [record, ...records].slice(0, MAX_RECORDS);
    await AsyncStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(newRecords));
    console.log('[Storage] Saved record:', record.local_id);
  } catch (error) {
    console.error('[Storage] Failed to save record:', error);
    notifyStorageError('Failed to save scan record.');
    throw error;
  }
}

export async function listRecords(): Promise<ScanRecord[]> {
  try {
    const stored = await AsyncStorage.getItem(HISTORY_STORAGE_KEY);
    if (stored) {
      const records = JSON.parse(stored) as ScanRecord[];
      console.log('[Storage] Loaded', records.length, 'records');
      return records;
    }
  } catch (error) {
    console.error('[Storage] Failed to load records:', error);
  }
  return [];
}

export async function updateRecord(local_id: string, patch: Partial<ScanRecord>): Promise<void> {
  try {
    const records = await listRecords();
    const index = records.findIndex(r => r.local_id === local_id);
    if (index !== -1) {
      records[index] = { ...records[index], ...patch };
      await AsyncStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(records));
      console.log('[Storage] Updated record:', local_id, patch);
    } else {
      console.warn('[Storage] Record not found:', local_id);
    }
  } catch (error) {
    console.error('[Storage] Failed to update record:', error);
    notifyStorageError('Failed to update scan record.');
    throw error;
  }
}

export async function getRecord(local_id: string): Promise<ScanRecord | null> {
  try {
    const records = await listRecords();
    return records.find(r => r.local_id === local_id) || null;
  } catch (error) {
    console.error('[Storage] Failed to get record:', error);
    return null;
  }
}

export async function clearAllRecords(): Promise<void> {
  try {
    await AsyncStorage.removeItem(HISTORY_STORAGE_KEY);
    console.log('[Storage] Cleared all records');
  } catch (error) {
    console.error('[Storage] Failed to clear records:', error);
    notifyStorageError('Failed to clear history.');
    throw error;
  }
}

export const DEFAULT_API_URL = 'http://192.168.43.251:5000';

export async function getApiBaseUrl(): Promise<string> {
  try {
    const url = await AsyncStorage.getItem(API_URL_STORAGE_KEY);
    return url || DEFAULT_API_URL;
  } catch {
    return DEFAULT_API_URL;
  }
}

export const DEFAULT_VARIETY_API_URL = 'http://192.168.43.90:5001';

const VARIETY_API_BASE_URL_KEY = 'variety_api_base_url';

export const getVarietyApiBaseUrl = async (): Promise<string> => {
  try {
    const url = await AsyncStorage.getItem(VARIETY_API_URL_STORAGE_KEY);
    return url || DEFAULT_VARIETY_API_URL;
  } catch (error) {
    console.log('[Storage] Failed to get variety API URL:', error);
    return DEFAULT_VARIETY_API_URL;
  }
};

export const setVarietyApiBaseUrl = async (url: string): Promise<void> => {
  const clean = url.trim().replace(/\/+$/, '');
  await AsyncStorage.setItem(VARIETY_API_URL_STORAGE_KEY, clean);
  console.log('[Storage] Saved variety API URL:', clean);
};

export async function setApiBaseUrl(url: string): Promise<void> {
  try {
    const clean = url.trim().replace(/\/+$/, '');
    await AsyncStorage.setItem(API_URL_STORAGE_KEY, clean);
    console.log('[Storage] Saved API URL:', clean);
  } catch (error) {
    console.error('[Storage] Failed to save API URL:', error);
    notifyStorageError('Failed to save API URL.');
    throw error;
  }
}

export async function getNgrokUrl(): Promise<string> {
  try {
    const url = await AsyncStorage.getItem(NGROK_URL_STORAGE_KEY);
    return url || '';
  } catch {
    return '';
  }
}

export async function setNgrokUrl(url: string): Promise<void> {
  try {
    await AsyncStorage.setItem(NGROK_URL_STORAGE_KEY, url);
    console.log('[Storage] Saved ngrok URL:', url);
  } catch (error) {
    console.error('[Storage] Failed to save ngrok URL:', error);
    notifyStorageError('Failed to save ngrok URL.');
    throw error;
  }
}

export async function saveMetadata(metadata: PersistedMetadata): Promise<void> {
  try {
    await AsyncStorage.setItem(METADATA_STORAGE_KEY, JSON.stringify(metadata));
    console.log('[Storage] Saved metadata:', metadata);
  } catch (error) {
    console.error('[Storage] Failed to save metadata:', error);
    notifyStorageError('Failed to save metadata.');
  }
}

export async function getMetadata(): Promise<PersistedMetadata> {
  try {
    const stored = await AsyncStorage.getItem(METADATA_STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored) as PersistedMetadata;
    }
  } catch (error) {
    console.error('[Storage] Failed to load metadata:', error);
  }
  return {};
}

export async function getOrCreateDeviceId(): Promise<string> {
  try {
    let deviceId = await AsyncStorage.getItem(DEVICE_ID_STORAGE_KEY);
    if (!deviceId) {
      deviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      await AsyncStorage.setItem(DEVICE_ID_STORAGE_KEY, deviceId);
      console.log('[Storage] Created new device ID:', deviceId);
    }
    return deviceId;
  } catch {
    return `device_${Date.now()}`;
  }
}
