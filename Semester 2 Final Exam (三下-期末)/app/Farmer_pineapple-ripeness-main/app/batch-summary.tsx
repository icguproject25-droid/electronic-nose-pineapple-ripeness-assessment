import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { Theme } from '@/constants/theme';
import { StatCard } from '@/components/StatCard';
import { useFarmerStore } from '@/stores/farmerStore';

/**
 * 批次摘要頁。
 *
 * 功能：
 * - 顯示目前 active batch 的掃描統計。
 * - 計算未熟、成熟、過熟與異常隔離數量。
 * - 提供完成批次按鈕，完成後可在 Reports 頁查看。
 */
export default function BatchSummaryScreen() {
  const batches = useFarmerStore((state) => state.batches);
  const activeBatchId = useFarmerStore((state) => state.activeBatchId);
  const completeBatch = useFarmerStore((state) => state.completeBatch);

  const batch = batches.find((item) => item.id === activeBatchId) ?? batches[0];

  if (!batch) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.title}>尚無批次</Text>
        <Pressable style={styles.button} onPress={() => router.push('/batch-create')}>
          <Text style={styles.buttonText}>建立批次</Text>
        </Pressable>
      </View>
    );
  }

  const unripe = batch.scans.filter((scan) => scan.ripeness === 'unripe').length;
  const ripe = batch.scans.filter((scan) => scan.ripeness === 'ripe').length;
  const overripe = batch.scans.filter((scan) => scan.ripeness === 'overripe').length;
  const isolate = batch.scans.filter((scan) => scan.anomalyFlag === 'isolate').length;
  const averageBrix = batch.scans.length
    ? (batch.scans.reduce((sum, scan) => sum + scan.tssBrix, 0) / batch.scans.length).toFixed(1)
    : '0.0';

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>批次摘要</Text>
      <Text style={styles.subtitle}>{batch.name}</Text>

      <View style={styles.infoBox}>
        <Text style={styles.info}>田區：{batch.field}</Text>
        <Text style={styles.info}>品種：{batch.variety}</Text>
        <Text style={styles.info}>狀態：{batch.status}</Text>
      </View>

      <View style={styles.statsRow}>
        <StatCard label="已掃描" value={batch.scans.length} helper={`目標 ${batch.targetSamples}`} />
        <StatCard label="平均糖度" value={averageBrix} helper="Brix" />
      </View>

      <View style={styles.statsRow}>
        <StatCard label="未熟" value={unripe} />
        <StatCard label="成熟" value={ripe} />
        <StatCard label="過熟" value={overripe} />
      </View>

      <View style={styles.statsRow}>
        <StatCard label="需隔離" value={isolate} helper="異常旗標" />
      </View>

      <Pressable style={styles.button} onPress={() => router.push('/batch-scan')}>
        <Text style={styles.buttonText}>繼續掃描</Text>
      </Pressable>

      <Pressable
        style={styles.secondaryButton}
        onPress={() => {
          completeBatch(batch.id);
          router.push('/reports');
        }}
      >
        <Text style={styles.secondaryButtonText}>完成批次並查看報告</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background },
  content: { padding: Theme.spacing.xl, paddingBottom: Theme.spacing.xxl },
  emptyContainer: { flex: 1, padding: Theme.spacing.xl, justifyContent: 'center', backgroundColor: Theme.colors.background },
  title: { color: Theme.colors.primaryDark, fontSize: Theme.fontSize.xl, fontWeight: '900' },
  subtitle: { color: Theme.colors.muted, marginTop: Theme.spacing.sm, marginBottom: Theme.spacing.lg },
  infoBox: { backgroundColor: Theme.colors.card, borderRadius: Theme.radius.lg, padding: Theme.spacing.lg, borderWidth: 1, borderColor: Theme.colors.border, marginBottom: Theme.spacing.lg },
  info: { color: Theme.colors.text, marginBottom: Theme.spacing.xs },
  statsRow: { flexDirection: 'row', gap: Theme.spacing.md, marginBottom: Theme.spacing.md },
  button: { backgroundColor: Theme.colors.primary, borderRadius: Theme.radius.lg, padding: Theme.spacing.lg, alignItems: 'center', marginTop: Theme.spacing.md },
  buttonText: { color: '#FFFFFF', fontWeight: '900', fontSize: Theme.fontSize.md },
  secondaryButton: { backgroundColor: Theme.colors.warningSoft, borderColor: Theme.colors.accent, borderWidth: 1, borderRadius: Theme.radius.lg, padding: Theme.spacing.lg, alignItems: 'center', marginTop: Theme.spacing.md },
  secondaryButtonText: { color: Theme.colors.warning, fontWeight: '900' }
});
