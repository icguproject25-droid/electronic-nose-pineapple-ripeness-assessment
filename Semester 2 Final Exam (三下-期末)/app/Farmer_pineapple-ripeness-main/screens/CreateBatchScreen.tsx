import { router, Stack } from "expo-router";
import React, { useMemo, useState } from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";

import { AppButton } from "@/components/AppButton";
import { DemoScrollView } from "@/components/DemoScrollView";
import { Theme } from "@/constants/theme";
import { useAppStore } from "@/store/app-store";
import { clamp, formatDate } from "@/utils/helpers";

export default function CreateBatchScreen() {
  const { createBatch, settings } = useAppStore();
  const today = useMemo(() => formatDate(new Date().toISOString()), []);
  const [area, setArea] = useState("A區");
  const [harvestCount, setHarvestCount] = useState("100");
  const [note, setNote] = useState("");

  const harvestValue = Number(harvestCount) || 0;
  const suggestedSamples = harvestValue <= 0 ? 0 : clamp(Math.ceil(harvestValue * settings.thresholds.samplingRatio), settings.thresholds.minSamples, settings.thresholds.maxSamples);

  function onCreate() {
    const created = createBatch({
      name: `${today} ${area}`,
      date: today,
      block: area,
      cultivar: "",
      harvest_count: harvestValue,
      purpose: "unknown",
      target_samples: suggestedSamples,
      note,
    });
    router.replace(`/batches/${created.batch_id}/scan` as never);
  }

  return (
    <DemoScrollView style={styles.container} contentContainerStyle={styles.content} testID="create-batch-screen">
      <Stack.Screen options={{ title: "建立今日批次" }} />
      <View style={styles.card}>
        <Text style={styles.title}>建立今日批次</Text>
        <Field label="日期" value={today} editable={false} />
        <Field label="農地區域" value={area} onChangeText={setArea} />
        <Field label="收成數量" value={harvestCount} onChangeText={setHarvestCount} keyboardType="numeric" />
        <View style={styles.suggestionCard}>
          <Text style={styles.suggestionLabel}>建議抽樣檢測數量</Text>
          <Text style={styles.suggestionValue}>{suggestedSamples}</Text>
          <Text style={styles.suggestionHint}>依設定抽樣比例自動計算</Text>
        </View>
        <Field label="批次備註" value={note} onChangeText={setNote} multiline />
      </View>
      <AppButton label="建立並開始掃描" onPress={onCreate} style={styles.submitButton} testID="create-scan-btn" />
    </DemoScrollView>
  );
}

function Field(props: { label: string; value: string; onChangeText?: (value: string) => void; editable?: boolean; keyboardType?: "default" | "numeric"; multiline?: boolean }) {
  return (
    <View style={styles.fieldWrap}>
      <Text style={styles.label}>{props.label}</Text>
      <TextInput style={[styles.input, props.multiline && styles.noteInput]} value={props.value} onChangeText={props.onChangeText} editable={props.editable !== false} keyboardType={props.keyboardType ?? "default"} multiline={props.multiline} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background },
  content: { padding: 18, gap: 18, paddingBottom: 90 },
  card: { backgroundColor: Theme.colors.card, borderRadius: 28, borderWidth: 1, borderColor: Theme.colors.border, padding: 18, gap: 18 },
  title: { fontSize: 30, fontWeight: "900", color: Theme.colors.primaryDark },
  fieldWrap: { gap: 10 },
  label: { fontSize: 18, fontWeight: "800", color: Theme.colors.text },
  input: { minHeight: 60, borderRadius: 18, backgroundColor: "#F4F8F0", borderWidth: 1, borderColor: Theme.colors.border, paddingHorizontal: 16, fontSize: 20, fontWeight: "800", color: Theme.colors.text },
  noteInput: { minHeight: 100, paddingVertical: 14, textAlignVertical: "top" },
  suggestionCard: { borderRadius: 24, backgroundColor: Theme.colors.successSoft, padding: 18, alignItems: "center", gap: 8 },
  suggestionLabel: { fontSize: 18, fontWeight: "700", color: Theme.colors.muted, textAlign: "center" },
  suggestionValue: { fontSize: 42, lineHeight: 48, fontWeight: "900", color: Theme.colors.primary },
  suggestionHint: { fontSize: 13, fontWeight: "600", color: Theme.colors.muted, textAlign: "center" },
  submitButton: { minHeight: 78, borderRadius: 24 },
});
