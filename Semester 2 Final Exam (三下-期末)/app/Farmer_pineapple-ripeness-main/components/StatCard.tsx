import { View, Text, StyleSheet } from 'react-native';
import { Theme } from '@/constants/theme';

/**
 * 統計卡片元件。
 *
 * 用途：
 * - 首頁顯示今日掃描數、異常數、批次數。
 * - 批次摘要頁顯示成熟 / 未熟 / 過熟數量。
 *
 * 設計成共用元件的原因：
 * - App 內多個頁面都會用到類似卡片。
 * - 只要修改這裡，就能同步調整所有統計卡片外觀。
 */
interface StatCardProps {
  label: string;
  value: string | number;
  helper?: string;
}

export function StatCard({ label, value, helper }: StatCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
      {helper ? <Text style={styles.helper}>{helper}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minWidth: 100,
    backgroundColor: Theme.colors.card,
    borderRadius: Theme.radius.lg,
    padding: Theme.spacing.lg,
    borderWidth: 1,
    borderColor: Theme.colors.border
  },
  label: {
    color: Theme.colors.muted,
    fontSize: Theme.fontSize.sm,
    marginBottom: Theme.spacing.sm
  },
  value: {
    color: Theme.colors.primaryDark,
    fontSize: Theme.fontSize.xl,
    fontWeight: '800'
  },
  helper: {
    color: Theme.colors.muted,
    fontSize: Theme.fontSize.sm,
    marginTop: Theme.spacing.xs
  }
});
