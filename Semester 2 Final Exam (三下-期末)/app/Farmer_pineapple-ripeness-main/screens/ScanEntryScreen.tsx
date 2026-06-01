import { router } from "expo-router";
import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { AppButton } from "@/components/AppButton";
import { Theme } from "@/constants/theme";
import { useAppStore } from "@/store/app-store";

/**
 * 掃描入口頁。
 *
 * 此頁面會優先找到進行中的批次，讓農民可以快速開始掃描；
 * 如果沒有批次，則導向建立批次頁。
 */
export default function ScanEntryScreen() {
  const { batches, tx } = useAppStore();
  const latestTesting = batches.find((item) => item.status === "testing") ?? batches[0];

  return (
    <View style={styles.container} testID="scan-entry-screen">
      <View style={styles.card}>
        <Text style={styles.title}>{latestTesting ? latestTesting.name : tx("currentBatch")}</Text>
        <Text style={styles.subtitle}>{latestTesting ? `目標掃描 ${latestTesting.target_samples} 顆` : "請先建立批次"}</Text>
        <AppButton
          label={tx("startScan")}
          onPress={() => {
            if (latestTesting) {
              router.push(`/batches/${latestTesting.batch_id}/scan` as never);
              return;
            }
            router.push("/batches/create");
          }}
          style={styles.primaryButton}
          testID="scan-entry-start"
        />
        <AppButton label={tx("newBatch")} onPress={() => router.push("/batches/create")} variant="secondary" style={styles.secondaryButton} testID="scan-entry-create" />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background, padding: 18, justifyContent: "center" },
  card: { backgroundColor: Theme.colors.card, borderRadius: 28, borderWidth: 1, borderColor: Theme.colors.border, padding: 22, gap: 16 },
  title: { fontSize: 30, fontWeight: "800", color: Theme.colors.primaryDark, textAlign: "center" },
  subtitle: { fontSize: 17, fontWeight: "700", color: Theme.colors.muted, textAlign: "center" },
  primaryButton: { minHeight: 74, borderRadius: 22 },
  secondaryButton: { minHeight: 64, borderRadius: 20 },
});
