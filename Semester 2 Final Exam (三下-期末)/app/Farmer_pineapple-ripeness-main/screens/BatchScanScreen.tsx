import { router, Stack, useLocalSearchParams } from "expo-router";
import React, { useState } from "react";
import { ActivityIndicator, Alert, StyleSheet, Text, View } from "react-native";

import { AppButton } from "@/components/AppButton";
import { Theme } from "@/constants/theme";
import { useAppStore } from "@/store/app-store";
import { Sample } from "@/types/models";
import { createId } from "@/utils/helpers";

export default function BatchScanScreen() {
  const { batchId } = useLocalSearchParams<{ batchId: string }>();
  const { batches, samples, addSample } = useAppStore();
  const [scanning, setScanning] = useState(false);
  const batch = batches.find((item) => item.batch_id === batchId);

  async function onScan() {
    if (!batch) return;
    setScanning(true);
    try {
      const choices: Sample["ripeness"][] = ["unripe", "ripe", "overripe"];
      const risks: Sample["blackheart_risk"][] = ["low", "med", "high"];
      const ripeness = choices[Math.floor(Math.random() * choices.length)];
      const sample: Sample = {
        sample_id: createId("sample"),
        batch_id: batch.batch_id,
        created_at: new Date().toISOString(),
        ripeness,
        tss_brix: Number((12 + Math.random() * 5).toFixed(1)),
        blackheart_risk: risks[Math.floor(Math.random() * risks.length)],
        anomaly_flag: Math.random() > 0.86 ? "isolate" : "normal",
        confidence: Number((0.72 + Math.random() * 0.22).toFixed(2)),
      };
      addSample(sample);
      Alert.alert("掃描完成", `成熟度：${sample.ripeness}\n糖度：${sample.tss_brix} Brix`);
    } finally {
      setScanning(false);
    }
  }

  if (!batch) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>找不到批次</Text>
      </View>
    );
  }

  const scanned = samples.filter((sample) => sample.batch_id === batch.batch_id).length;

  return (
    <View style={styles.container} testID="batch-scan-screen">
      <Stack.Screen options={{ title: "批次掃描" }} />
      <View style={styles.card}>
        <Text style={styles.title}>{batch.name}</Text>
        <Text style={styles.meta}>掃描進度：{scanned}/{batch.target_samples}</Text>
        <Text style={styles.meta}>後端可接 RPi /scan/start；目前保留展示用 mock 結果。</Text>
      </View>
      <AppButton label={scanning ? "掃描中..." : "開始 30 秒掃描"} onPress={onScan} style={styles.scanButton} testID="scan-btn" />
      {scanning ? <ActivityIndicator color={Theme.colors.primary} /> : null}
      <AppButton label="查看批次摘要" variant="secondary" onPress={() => router.push(`/batches/${batch.batch_id}/summary` as never)} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background, padding: 18, gap: 14 },
  card: { backgroundColor: Theme.colors.card, borderRadius: 24, borderWidth: 1, borderColor: Theme.colors.border, padding: 18, gap: 10 },
  title: { fontSize: 28, fontWeight: "900", color: Theme.colors.primaryDark },
  meta: { fontSize: 16, color: Theme.colors.muted, fontWeight: "700" },
  scanButton: { minHeight: 76, borderRadius: 24 },
});
