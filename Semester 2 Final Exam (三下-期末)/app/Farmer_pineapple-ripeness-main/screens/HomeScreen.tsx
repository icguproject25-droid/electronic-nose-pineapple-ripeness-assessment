import { router } from "expo-router";
import React, { useMemo } from "react";
import { StyleSheet, Text, View } from "react-native";

import { AppButton } from "@/components/AppButton";
import { DemoScrollView } from "@/components/DemoScrollView";
import { Theme } from "@/constants/theme";
import { useAppStore } from "@/store/app-store";

/**
 * 農民端首頁。
 *
 * 此頁面保留 Farmer_pineapple/expo 的核心邏輯：
 * - 今日掃描數
 * - 今日異常數
 * - 進行中批次數
 * - 開始掃描與新建批次入口
 */
export default function HomeScreen() {
  const { batches, samples, tx } = useAppStore();
  const today = new Date().toISOString().slice(0, 10);

  const todayBatchIds = useMemo(() => new Set(batches.filter((batch) => batch.date === today).map((batch) => batch.batch_id)), [batches, today]);
  const todayScanCount = samples.filter((sample) => todayBatchIds.has(sample.batch_id)).length;
  const todayAbnormalCount = samples.filter((sample) => todayBatchIds.has(sample.batch_id) && sample.anomaly_flag === "isolate").length;
  const inProgressBatches = batches.filter((batch) => batch.status === "testing").length;
  const activeBatch = batches.find((batch) => batch.status === "testing") ?? batches[0];

  return (
    <DemoScrollView style={styles.container} contentContainerStyle={styles.content} testID="home-screen">
      <View style={styles.heroCard}>
        <Text style={styles.eyebrow}>{tx("currentBatch")}</Text>
        <Text style={styles.title}>{tx("todayStats")}</Text>
        <Text style={styles.subtitle}>農民端批次掃描與分級決策入口</Text>
        <View style={styles.statsRow}>
          <StatBox value={todayScanCount} label="今日樣本" />
          <StatBox value={todayAbnormalCount} label="今日異常" />
          <StatBox value={inProgressBatches} label="進行中" />
        </View>
      </View>

      <AppButton
        label={tx("startScan")}
        onPress={() => {
          if (activeBatch) router.push(`/batches/${activeBatch.batch_id}/scan`);
          else router.push("/batches/create");
        }}
        style={styles.primaryButton}
        testID="dashboard-start-scan-btn"
      />
      <AppButton label={tx("newBatch")} onPress={() => router.push("/batches/create")} variant="secondary" style={styles.secondaryButton} testID="dashboard-create-batch-btn" />

      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>{tx("recentBatches")}</Text>
        {batches.length === 0 ? <Text style={styles.empty}>{tx("noData")}</Text> : null}
        {batches.slice(0, 4).map((batch) => {
          const scanned = samples.filter((sample) => sample.batch_id === batch.batch_id).length;
          return (
            <View key={batch.batch_id} style={styles.batchRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.batchName}>{batch.name}</Text>
                <Text style={styles.batchMeta}>{batch.block} · {batch.date}</Text>
              </View>
              <Text style={styles.batchProgress}>{scanned}/{batch.target_samples}</Text>
            </View>
          );
        })}
      </View>
    </DemoScrollView>
  );
}

function StatBox({ value, label }: { value: number; label: string }) {
  return (
    <View style={styles.statBox}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background },
  content: { padding: 18, paddingBottom: 120, gap: 16 },
  heroCard: { backgroundColor: Theme.colors.card, borderRadius: 28, borderWidth: 1, borderColor: Theme.colors.border, padding: 20, gap: 14 },
  eyebrow: { fontSize: 13, fontWeight: "800", color: Theme.colors.muted, textTransform: "uppercase", letterSpacing: 1 },
  title: { fontSize: 34, lineHeight: 38, fontWeight: "900", color: Theme.colors.primaryDark },
  subtitle: { fontSize: 16, lineHeight: 22, fontWeight: "600", color: Theme.colors.muted },
  statsRow: { flexDirection: "row", gap: 10 },
  statBox: { flex: 1, borderRadius: 22, backgroundColor: "#F7FAF4", padding: 14, gap: 16 },
  statValue: { fontSize: 34, fontWeight: "900", color: Theme.colors.text },
  statLabel: { fontSize: 14, fontWeight: "700", color: Theme.colors.muted },
  primaryButton: { minHeight: 78, borderRadius: 24 },
  secondaryButton: { minHeight: 68, borderRadius: 22 },
  sectionCard: { backgroundColor: Theme.colors.card, borderRadius: 24, borderWidth: 1, borderColor: Theme.colors.border, padding: 14, gap: 10 },
  sectionTitle: { fontSize: 24, fontWeight: "900", color: Theme.colors.text },
  empty: { textAlign: "center", color: Theme.colors.muted, paddingVertical: 16, fontWeight: "700" },
  batchRow: { flexDirection: "row", alignItems: "center", padding: 14, borderRadius: 18, backgroundColor: "#F7FAF4" },
  batchName: { fontSize: 18, fontWeight: "800", color: Theme.colors.text },
  batchMeta: { fontSize: 14, fontWeight: "600", color: Theme.colors.muted },
  batchProgress: { fontSize: 16, fontWeight: "900", color: Theme.colors.primaryDark },
});
