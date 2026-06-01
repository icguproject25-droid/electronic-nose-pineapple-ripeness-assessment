import { router, Stack, useLocalSearchParams } from "expo-router";
import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { AppButton } from "@/components/AppButton";
import { Theme } from "@/constants/theme";
import { useAppStore } from "@/store/app-store";

export default function BatchDetailScreen() {
  const { batchId } = useLocalSearchParams<{ batchId: string }>();
  const { batches, samples } = useAppStore();
  const batch = batches.find((item) => item.batch_id === batchId);

  if (!batch) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>找不到批次</Text>
        <AppButton label="返回批次列表" onPress={() => router.replace("/(tabs)/batches")} />
      </View>
    );
  }

  const scanned = samples.filter((sample) => sample.batch_id === batch.batch_id).length;

  return (
    <View style={styles.container}>
      <Stack.Screen options={{ title: batch.name }} />
      <View style={styles.card}>
        <Text style={styles.title}>{batch.name}</Text>
        <Text style={styles.meta}>日期：{batch.date}</Text>
        <Text style={styles.meta}>區域：{batch.block}</Text>
        <Text style={styles.meta}>收成數量：{batch.harvest_count}</Text>
        <Text style={styles.meta}>掃描進度：{scanned}/{batch.target_samples}</Text>
        <Text style={styles.meta}>狀態：{batch.status}</Text>
      </View>
      <AppButton label="開始掃描" onPress={() => router.push(`/batches/${batch.batch_id}/scan` as never)} />
      <AppButton label="查看摘要" variant="secondary" onPress={() => router.push(`/batches/${batch.batch_id}/summary` as never)} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background, padding: 18, gap: 14 },
  card: { backgroundColor: Theme.colors.card, borderRadius: 24, borderWidth: 1, borderColor: Theme.colors.border, padding: 18, gap: 10 },
  title: { fontSize: 26, fontWeight: "900", color: Theme.colors.primaryDark },
  meta: { fontSize: 16, fontWeight: "700", color: Theme.colors.text },
});
