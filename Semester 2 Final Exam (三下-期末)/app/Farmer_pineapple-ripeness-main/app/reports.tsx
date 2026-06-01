import { ScrollView, StyleSheet, Text } from 'react-native';
import { Theme } from '@/constants/theme';
import { BatchCard } from '@/components/BatchCard';
import { useFarmerStore } from '@/stores/farmerStore';

/**
 * 報告列表頁。
 *
 * 功能：
 * - 顯示已完成或已有掃描紀錄的批次。
 * - 在展示版中，報告以批次卡片呈現。
 * - 若未來要匯出 PDF / CSV，可在這個頁面加入按鈕與 expo-file-system 寫檔流程。
 */
export default function ReportsScreen() {
  const batches = useFarmerStore((state) => state.batches);
  const reportBatches = batches.filter((batch) => batch.status === 'done' || batch.scans.length > 0);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>報告列表</Text>
      <Text style={styles.subtitle}>顯示已完成或已有掃描紀錄的批次。</Text>

      {reportBatches.length === 0 ? (
        <Text style={styles.empty}>目前尚無可顯示的批次報告。</Text>
      ) : (
        reportBatches.map((batch) => <BatchCard key={batch.id} batch={batch} />)
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background },
  content: { padding: Theme.spacing.xl, paddingBottom: Theme.spacing.xxl },
  title: { color: Theme.colors.primaryDark, fontSize: Theme.fontSize.xl, fontWeight: '900' },
  subtitle: { color: Theme.colors.muted, marginTop: Theme.spacing.sm, marginBottom: Theme.spacing.lg },
  empty: { color: Theme.colors.muted, backgroundColor: Theme.colors.card, padding: Theme.spacing.lg, borderRadius: Theme.radius.lg }
});
