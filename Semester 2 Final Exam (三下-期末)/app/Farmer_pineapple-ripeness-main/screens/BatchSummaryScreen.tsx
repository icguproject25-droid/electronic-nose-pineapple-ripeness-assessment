import { router, Stack, useLocalSearchParams } from "expo-router";
import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { AppButton } from "@/components/AppButton";
import { Theme } from "@/constants/theme";
import { useAppStore } from "@/store/app-store";

/**
 * 批次摘要頁。
 *
 * 此頁面對應 Tinazhen/Farmer_pineapple/expo 的批次總結流程，
 * 會依照目前批次的 samples 計算成熟度分布、平均糖度與異常數。
 */
export default function BatchSummaryScreen() {
  const { batchId } = useLocalSearchParams<{ batchId: string }>();
  const { batches, samples, updateBatchStatus } = useAppStore();
  const batch = batches.find((item) => item.batch_id === batchId);

  if (!batch) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>找不到批次</Text>
        <AppButton label="返回批次列表" onPress={() => router.replace("/(tabs)/batches")} />
      </View>
    );
  }

  const batchSamples = samples.filter((sample) => sample.batch_id === batch.batch_id);
  const unripe = batchSamples.filter((sample) => sample.ripeness === "unripe").length;
  const ripe = batchSamples.filter((sample) => sample.ripeness === "ripe").length;
  const overripe = batchSamples.filter((sample) => sample.ripeness === "overripe").length;
  const isolate = batchSamples.filter((sample) => sample.anomaly_flag === "isolate").length;
  const avgBrix = batchSamples.length ? (batchSamples.reduce((sum, sample) => sum + sample.tss_brix, 0) / batchSamples.length).toFixed(1) : "0.0";

  return (
    <View style={styles.container} testID="batch-summary-screen">
      <Stack.Screen options={{ title: "批次摘要" }} />
      <View style={styles.card}>
        <Text style={styles.title}>{batch.name}</Text>
        <Text style={styles.meta}>區域：{batch.block}</Text>
        <Text style={styles.meta}>收成數量：{batch.harvest_count}</Text>
        <Text style={styles.meta}>掃描數：{batchSamples.length}/{batch.target_samples}</Text>
      </View>

      <View style={styles.grid}>
        <SummaryBox label="未熟" value={unripe} />
        <SummaryBox label="成熟" value={ripe} />
        <SummaryBox label="過熟" value={overripe} />
        <SummaryBox label="異常" value={isolate} />
        <SummaryBox label="平均糖度" value={avgBrix} suffix="Brix" />
      </View>

      <AppButton
        label="標記為完成"
        onPress={() => {
          updateBatchStatus(batch.batch_id, "done");
          router.replace("/(tabs)/reports");
        }}
      />
      <AppButton label="繼續掃描" variant="secondary" onPress={() => router.push(`/batches/${batch.batch_id}/scan` as never)} />
    </View>
  );
}

function SummaryBox({ label, value, suffix }: { label: string; value: string | number; suffix?: string }) {
  return (
    <View style={styles.box}>
      <Text style={styles.boxValue}>{value}</Text>
      <Text style={styles.boxLabel}>{label}{suffix ? ` / ${suffix}` : ""}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background, padding: 18, gap: 14 },
  card: { backgroundColor: Theme.colors.card, borderRadius: 24, borderWidth: 1, borderColor: Theme.colors.border, padding: 18, gap: 8 },
  title: { fontSize: 28, fontWeight: "900", color: Theme.colors.primaryDark },
  meta: { fontSize: 16, color: Theme.colors.muted, fontWeight: "700" },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 12 },
  box: { flexGrow: 1, flexBasis: "45%", backgroundColor: Theme.colors.card, borderRadius: 20, borderWidth: 1, borderColor: Theme.colors.border, padding: 18, gap: 8 },
  boxValue: { fontSize: 34, fontWeight: "900", color: Theme.colors.primary },
  boxLabel: { fontSize: 14, fontWeight: "800", color: Theme.colors.muted },
});
