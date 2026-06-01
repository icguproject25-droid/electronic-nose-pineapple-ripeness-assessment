import { useState } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import { Theme } from '@/constants/theme';
import { useFarmerStore } from '@/stores/farmerStore';
import type { Batch } from '@/types';

/**
 * 建立批次頁。
 *
 * 功能：
 * - 讓農民建立一個新的採樣批次。
 * - 建立後會自動將新批次設為 active batch，方便下一步直接掃描。
 *
 * 注意：
 * - 這裡使用本機 Zustand store 儲存批次，適合專題展示。
 * - 若未來要做正式產品，可在 createBatch 後同步 POST 到後端資料庫。
 */
export default function BatchCreateScreen() {
  const createBatch = useFarmerStore((state) => state.createBatch);

  const [name, setName] = useState('');
  const [field, setField] = useState('A-01');
  const [variety, setVariety] = useState('金鑽鳳梨');
  const [usage, setUsage] = useState<Batch['usage']>('export');
  const [targetSamples, setTargetSamples] = useState('10');

  /** 表單送出：檢查必填後建立批次。 */
  function handleSubmit() {
    const parsedTarget = Number(targetSamples);

    if (!name.trim()) {
      Alert.alert('缺少批次名稱', '請輸入批次名稱後再建立。');
      return;
    }

    if (!Number.isFinite(parsedTarget) || parsedTarget <= 0) {
      Alert.alert('採樣目標錯誤', '採樣目標數必須是大於 0 的數字。');
      return;
    }

    createBatch({
      name: name.trim(),
      field: field.trim() || '未指定',
      variety: variety.trim() || '未指定',
      usage,
      targetSamples: parsedTarget
    });

    router.replace('/batch-scan');
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>建立新批次</Text>
      <Text style={styles.subtitle}>建立批次後即可開始逐顆掃描鳳梨。</Text>

      <LabeledInput label="批次名稱" value={name} onChangeText={setName} placeholder="例如：A 區 6/1 採收批次" />
      <LabeledInput label="田區" value={field} onChangeText={setField} placeholder="例如：A-01" />
      <LabeledInput label="品種" value={variety} onChangeText={setVariety} placeholder="例如：金鑽鳳梨" />
      <LabeledInput label="採樣目標數" value={targetSamples} onChangeText={setTargetSamples} keyboardType="number-pad" />

      <Text style={styles.label}>用途</Text>
      <View style={styles.optionRow}>
        <UsageButton label="外銷" active={usage === 'export'} onPress={() => setUsage('export')} />
        <UsageButton label="內銷" active={usage === 'domestic'} onPress={() => setUsage('domestic')} />
        <UsageButton label="加工" active={usage === 'processing'} onPress={() => setUsage('processing')} />
      </View>

      <Pressable style={styles.button} onPress={handleSubmit}>
        <Text style={styles.buttonText}>建立並開始掃描</Text>
      </Pressable>
    </ScrollView>
  );
}

interface LabeledInputProps {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder?: string;
  keyboardType?: 'default' | 'number-pad';
}

/** 共用輸入框，避免每個欄位重複樣式。 */
function LabeledInput({ label, value, onChangeText, placeholder, keyboardType = 'default' }: LabeledInputProps) {
  return (
    <View style={styles.inputGroup}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        keyboardType={keyboardType}
        style={styles.input}
      />
    </View>
  );
}

interface UsageButtonProps {
  label: string;
  active: boolean;
  onPress: () => void;
}

/** 用途切換按鈕。 */
function UsageButton({ label, active, onPress }: UsageButtonProps) {
  return (
    <Pressable onPress={onPress} style={[styles.usageButton, active && styles.usageButtonActive]}>
      <Text style={[styles.usageButtonText, active && styles.usageButtonTextActive]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background },
  content: { padding: Theme.spacing.xl, paddingBottom: Theme.spacing.xxl },
  title: { color: Theme.colors.primaryDark, fontSize: Theme.fontSize.xl, fontWeight: '900' },
  subtitle: { color: Theme.colors.muted, marginTop: Theme.spacing.sm, marginBottom: Theme.spacing.lg },
  inputGroup: { marginBottom: Theme.spacing.lg },
  label: { color: Theme.colors.text, fontWeight: '800', marginBottom: Theme.spacing.sm },
  input: {
    backgroundColor: Theme.colors.card,
    borderColor: Theme.colors.border,
    borderWidth: 1,
    borderRadius: Theme.radius.md,
    padding: Theme.spacing.lg,
    fontSize: Theme.fontSize.md
  },
  optionRow: { flexDirection: 'row', gap: Theme.spacing.md, marginBottom: Theme.spacing.xl },
  usageButton: {
    flex: 1,
    padding: Theme.spacing.md,
    alignItems: 'center',
    borderRadius: Theme.radius.md,
    backgroundColor: Theme.colors.card,
    borderWidth: 1,
    borderColor: Theme.colors.border
  },
  usageButtonActive: { backgroundColor: Theme.colors.successSoft, borderColor: Theme.colors.primary },
  usageButtonText: { color: Theme.colors.muted, fontWeight: '700' },
  usageButtonTextActive: { color: Theme.colors.primaryDark },
  button: { backgroundColor: Theme.colors.primary, borderRadius: Theme.radius.lg, padding: Theme.spacing.lg, alignItems: 'center' },
  buttonText: { color: '#FFFFFF', fontWeight: '900', fontSize: Theme.fontSize.md }
});
