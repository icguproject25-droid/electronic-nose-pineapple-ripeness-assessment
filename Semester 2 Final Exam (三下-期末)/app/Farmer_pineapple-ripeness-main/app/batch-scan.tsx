import { useState } from 'react';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { Theme } from '@/constants/theme';
import { startScan } from '@/services/api';
import { useFarmerStore } from '@/stores/farmerStore';

/**
 * 批次掃描頁。
 *
 * 功能：
 * - 使用目前 active batch 作為掃描目標。
 * - 呼叫 RPi `/scan/start` 進行一次電子鼻掃描。
 * - 後端離線時使用 API service 的 mock fallback，確保展示流程不中斷。
 * - 掃描完成後把結果加入批次。
 */
export default function BatchScanScreen() {
  const [isScanning, setIsScanning] = useState(false);

  const batches = useFarmerStore((state) => state.batches);
  const activeBatchId = useFarmerStore((state) => state.activeBatchId);
  const settings = useFarmerStore((state) => state.settings);
  const addScanToBatch = useFarmerStore((state) => state.addScanToBatch);

  const activeBatch = batches.find((batch) => batch.id === activeBatchId) ?? batches[0];

  /**
   * 觸發一次掃描。
   *
   * 流程：
   * 1. 檢查是否有批次。
   * 2. 呼叫 startScan。
   * 3. 將 API 回傳結果整理後加入 store。
   * 4. 顯示成功提示。
   */
  async function handleScan() {
    if (!activeBatch) {
      Alert.alert('尚未建立批次', '請先建立批次再開始掃描。');
      return;
    }

    setIsScanning(true);

    try {
      const result = await startScan(settings.apiBaseUrl, true);

      addScanToBatch(activeBatch.id, {
        ripeness: result.ripeness,
        tssBrix: result.tss_brix,
        blackheartRisk: result.blackheart_risk,
        anomalyFlag: result.anomaly_flag,
        confidence: result.confidence
      });

      Alert.alert('掃描完成', `成熟度：${result.ripeness}\n糖度：${result.tss_brix} Brix`);
    } catch {
      Alert.alert('掃描失敗', '請確認 Raspberry Pi 後端是否啟動。');
    } finally {
      setIsScanning(false);
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>批次掃描</Text>
      <Text style={styles.subtitle}>將鳳梨放入檢測盒後，按下開始掃描。</Text>

      {activeBatch ? (
        <View style={styles.batchBox}>
          <Text style={styles.batchTitle}>{activeBatch.name}</Text>
          <Text style={styles.meta}>田區：{activeBatch.field}</Text>
          <Text style={styles.meta}>已掃描：{activeBatch.scans.length} / {activeBatch.targetSamples}</Text>
        </View>
      ) : (
        <Text style={styles.meta}>目前沒有批次，請先建立批次。</Text>
      )}

      <Pressable disabled={isScanning} style={[styles.scanButton, isScanning && styles.disabled]} onPress={handleScan}>
        {isScanning ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.scanButtonText}>開始 30 秒掃描</Text>}
      </Pressable>

      <Pressable style={styles.secondaryButton} onPress={() => router.push('/batch-summary')}>
        <Text style={styles.secondaryButtonText}>查看批次摘要</Text>
      </Pressable>

      <Text style={styles.note}>目前後端 URL：{settings.apiBaseUrl}</Text>
      <Text style={styles.note}>若後端離線，系統會自動產生展示用 mock 結果。</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background },
  content: { padding: Theme.spacing.xl, paddingBottom: Theme.spacing.xxl },
  title: { color: Theme.colors.primaryDark, fontSize: Theme.fontSize.xl, fontWeight: '900' },
  subtitle: { color: Theme.colors.muted, marginTop: Theme.spacing.sm, marginBottom: Theme.spacing.lg },
  batchBox: {
    backgroundColor: Theme.colors.card,
    borderRadius: Theme.radius.lg,
    padding: Theme.spacing.lg,
    borderWidth: 1,
    borderColor: Theme.colors.border,
    marginBottom: Theme.spacing.xl
  },
  batchTitle: { color: Theme.colors.text, fontSize: Theme.fontSize.lg, fontWeight: '800' },
  meta: { color: Theme.colors.muted, marginTop: Theme.spacing.sm },
  scanButton: {
    backgroundColor: Theme.colors.primary,
    borderRadius: Theme.radius.lg,
    padding: Theme.spacing.xl,
    alignItems: 'center',
    marginBottom: Theme.spacing.md
  },
  disabled: { opacity: 0.6 },
  scanButtonText: { color: '#FFFFFF', fontWeight: '900', fontSize: Theme.fontSize.lg },
  secondaryButton: {
    borderRadius: Theme.radius.lg,
    padding: Theme.spacing.lg,
    alignItems: 'center',
    backgroundColor: Theme.colors.warningSoft,
    borderWidth: 1,
    borderColor: Theme.colors.accent,
    marginBottom: Theme.spacing.xl
  },
  secondaryButtonText: { color: Theme.colors.warning, fontWeight: '800' },
  note: { color: Theme.colors.muted, fontSize: Theme.fontSize.sm, marginTop: Theme.spacing.sm }
});
