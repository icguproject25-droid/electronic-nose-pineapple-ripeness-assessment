import { ScrollView, StyleSheet, Text, Pressable } from 'react-native';
import { router } from 'expo-router';
import { Theme } from '@/constants/theme';
import { BatchCard } from '@/components/BatchCard';
import { useFarmerStore } from '@/stores/farmerStore';

/**
 * 批次管理頁。
 *
 * 功能：
 * - 顯示目前 App 中所有建立過的批次。
 * - 點擊批次後設定成 active batch，並進入批次摘要頁。
 * - 提供建立新批次按鈕。
 */
export default function BatchesScreen() {
  const batches = useFarmerStore((state) => state.batches);
  const setActiveBatch = useFarmerStore((state) => state.setActiveBatch);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>批次管理</Text>
      <Text style={styles.subtitle}>選擇批次後可進行掃描、完成批次或查看摘要。</Text>

      <Pressable style={styles.button} onPress={() => router.push('/batch-create')}>
        <Text style={styles.buttonText}>建立新批次</Text>
      </Pressable>

      {batches.map((batch) => (
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
  container: { flex: 1, backgroundColor: Theme.colors.background },
  content: { padding: Theme.spacing.xl, paddingBottom: Theme.spacing.xxl },
  title: { color: Theme.colors.primaryDark, fontSize: Theme.fontSize.xl, fontWeight: '900' },
  subtitle: { color: Theme.colors.muted, marginTop: Theme.spacing.sm, marginBottom: Theme.spacing.lg },
  button: {
    backgroundColor: Theme.colors.primary,
    borderRadius: Theme.radius.lg,
    padding: Theme.spacing.lg,
    alignItems: 'center',
    marginBottom: Theme.spacing.lg
  },
  buttonText: { color: '#FFFFFF', fontWeight: '800', fontSize: Theme.fontSize.md }
});
