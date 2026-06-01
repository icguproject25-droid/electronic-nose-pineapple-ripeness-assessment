import { ScrollView, StyleSheet, Text, View, Pressable } from 'react-native';
import { router } from 'expo-router';
import { Theme } from '@/constants/theme';
import { StatCard } from '@/components/StatCard';
import { BatchCard } from '@/components/BatchCard';
import { useFarmerStore } from '@/stores/farmerStore';

/**
 * 農民端首頁。
 *
 * 這一頁是農民進入 App 後看到的第一個畫面，負責提供：
 * - 今日 / 目前批次的統計摘要。
 * - 快速操作入口，例如開始掃描、建立批次、查看報告。
 * - 最近批次列表。
 */
export default function HomeScreen() {
  const batches = useFarmerStore((state) => state.batches);
  const setActiveBatch = useFarmerStore((state) => state.setActiveBatch);

  /** 所有批次的掃描總數。 */
  const totalScans = batches.reduce((sum, batch) => sum + batch.scans.length, 0);

  /** 異常隔離數，用於提醒農民是否需要挑出問題果。 */
  const abnormalCount = batches.reduce(
    (sum, batch) => sum + batch.scans.filter((scan) => scan.anomalyFlag === 'isolate').length,
    0
  );

  /** 尚未完成的批次數。 */
  const activeBatchCount = batches.filter((batch) => batch.status !== 'done').length;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>鳳梨農民端檢測</Text>
      <Text style={styles.subtitle}>批次掃描、成熟度統計與報表管理</Text>

      <View style={styles.statsRow}>
        <StatCard label="總掃描" value={totalScans} helper="目前紀錄" />
        <StatCard label="異常" value={abnormalCount} helper="需隔離" />
        <StatCard label="批次" value={activeBatchCount} helper="進行中" />
      </View>

      <View style={styles.actions}>
        <Pressable style={styles.primaryButton} onPress={() => router.push('/batch-scan')}>
          <Text style={styles.primaryButtonText}>開始掃描</Text>
        </Pressable>
        <Pressable style={styles.secondaryButton} onPress={() => router.push('/batch-create')}>
          <Text style={styles.secondaryButtonText}>新建批次</Text>
        </Pressable>
      </View>

      <View style={styles.menuGrid}>
        <Pressable style={styles.menuItem} onPress={() => router.push('/batches')}>
          <Text style={styles.menuTitle}>批次管理</Text>
          <Text style={styles.menuText}>查看全部批次</Text>
        </Pressable>
        <Pressable style={styles.menuItem} onPress={() => router.push('/reports')}>
          <Text style={styles.menuTitle}>報告列表</Text>
          <Text style={styles.menuText}>查看完成批次</Text>
        </Pressable>
        <Pressable style={styles.menuItem} onPress={() => router.push('/settings')}>
          <Text style={styles.menuTitle}>設定</Text>
          <Text style={styles.menuText}>後端 URL</Text>
        </Pressable>
      </View>

      <Text style={styles.sectionTitle}>最近批次</Text>
      {batches.slice(0, 4).map((batch) => (
        <BatchCard
          key={batch.id}
          batch={batch}
          onPress={() => {
            setActiveBatch(batch.id);
            router.push('/batch-summary');
          }}
        />
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Theme.colors.background
  },
  content: {
    padding: Theme.spacing.xl,
    paddingBottom: Theme.spacing.xxl
  },
  title: {
    color: Theme.colors.primaryDark,
    fontSize: Theme.fontSize.xl,
    fontWeight: '900'
  },
  subtitle: {
    color: Theme.colors.muted,
    fontSize: Theme.fontSize.md,
    marginTop: Theme.spacing.sm,
    marginBottom: Theme.spacing.lg
  },
  statsRow: {
    flexDirection: 'row',
    gap: Theme.spacing.md,
    marginBottom: Theme.spacing.lg
  },
  actions: {
    flexDirection: 'row',
    gap: Theme.spacing.md,
    marginBottom: Theme.spacing.lg
  },
  primaryButton: {
    flex: 1,
    backgroundColor: Theme.colors.primary,
    padding: Theme.spacing.lg,
    borderRadius: Theme.radius.lg,
    alignItems: 'center'
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: Theme.fontSize.md
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: Theme.colors.warningSoft,
    padding: Theme.spacing.lg,
    borderRadius: Theme.radius.lg,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Theme.colors.accent
  },
  secondaryButtonText: {
    color: Theme.colors.warning,
    fontWeight: '800',
    fontSize: Theme.fontSize.md
  },
  menuGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Theme.spacing.md,
    marginBottom: Theme.spacing.xl
  },
  menuItem: {
    flexGrow: 1,
    flexBasis: '30%',
    backgroundColor: Theme.colors.card,
    padding: Theme.spacing.lg,
    borderRadius: Theme.radius.lg,
    borderWidth: 1,
    borderColor: Theme.colors.border
  },
  menuTitle: {
    color: Theme.colors.text,
    fontWeight: '800',
    marginBottom: Theme.spacing.xs
  },
  menuText: {
    color: Theme.colors.muted,
    fontSize: Theme.fontSize.sm
  },
  sectionTitle: {
    color: Theme.colors.text,
    fontSize: Theme.fontSize.lg,
    fontWeight: '800',
    marginBottom: Theme.spacing.md
  }
});
