import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Theme } from '@/constants/theme';
import type { Batch } from '@/types';

/**
 * 批次卡片元件。
 *
 * 用途：
 * - 首頁與批次管理頁顯示單一批次摘要。
 * - 使用者點擊卡片後可進入該批次的掃描或摘要流程。
 *
 * 傳入資料：
 * - batch：批次本身的資料。
 * - onPress：點擊卡片後要執行的動作，例如設定 activeBatch 並跳頁。
 */
interface BatchCardProps {
  batch: Batch;
  onPress?: () => void;
}

/** 將批次狀態轉成適合 UI 顯示的中文。 */
function getStatusLabel(status: Batch['status']) {
  if (status === 'draft') return '草稿';
  if (status === 'testing') return '檢測中';
  return '完成';
}

export function BatchCard({ batch, onPress }: BatchCardProps) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.card, pressed && styles.pressed]}>
      <View style={styles.header}>
        <Text style={styles.title}>{batch.name}</Text>
        <Text style={styles.status}>{getStatusLabel(batch.status)}</Text>
      </View>

      <Text style={styles.meta}>田區：{batch.field}｜品種：{batch.variety}</Text>
      <Text style={styles.meta}>目標採樣：{batch.targetSamples} 顆｜已掃描：{batch.scans.length} 顆</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Theme.colors.card,
    borderRadius: Theme.radius.lg,
    padding: Theme.spacing.lg,
    borderWidth: 1,
    borderColor: Theme.colors.border,
    marginBottom: Theme.spacing.md
  },
  pressed: {
    opacity: 0.72
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: Theme.spacing.md,
    marginBottom: Theme.spacing.sm
  },
  title: {
    flex: 1,
    color: Theme.colors.text,
    fontSize: Theme.fontSize.lg,
    fontWeight: '800'
  },
  status: {
    color: Theme.colors.primaryDark,
    backgroundColor: Theme.colors.successSoft,
    paddingHorizontal: Theme.spacing.md,
    paddingVertical: Theme.spacing.xs,
    borderRadius: Theme.radius.sm,
    fontSize: Theme.fontSize.sm,
    fontWeight: '700'
  },
  meta: {
    color: Theme.colors.muted,
    fontSize: Theme.fontSize.sm,
    marginTop: Theme.spacing.xs
  }
});
