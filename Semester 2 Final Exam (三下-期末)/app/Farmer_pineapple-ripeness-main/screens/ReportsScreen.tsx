import React from "react";
import { FlatList, StyleSheet, Text, View } from "react-native";

import { Theme } from "@/constants/theme";
import { useAppStore } from "@/store/app-store";

export default function ReportsScreen() {
  const { batches, samples, tx } = useAppStore();
  const reportBatches = batches.filter((batch) => batch.status === "done" || samples.some((sample) => sample.batch_id === batch.batch_id));

  return (
    <View style={styles.container} testID="reports-screen">
      <Text style={styles.title}>{tx("reports")}</Text>
      <FlatList
        data={reportBatches}
        keyExtractor={(item) => item.batch_id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={<Text style={styles.empty}>{tx("noData")}</Text>}
        renderItem={({ item }) => {
          const count = samples.filter((sample) => sample.batch_id === item.batch_id).length;
          return (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>{item.name}</Text>
              <Text style={styles.meta}>日期：{item.date}</Text>
              <Text style={styles.meta}>區域：{item.block}</Text>
              <Text style={styles.meta}>掃描數：{count}/{item.target_samples}</Text>
              <Text style={styles.meta}>狀態：{item.status}</Text>
            </View>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background, padding: 18, gap: 14 },
  title: { fontSize: 30, fontWeight: "900", color: Theme.colors.primaryDark },
  list: { gap: 12, paddingBottom: 90 },
  card: { backgroundColor: Theme.colors.card, borderRadius: 22, borderWidth: 1, borderColor: Theme.colors.border, padding: 16, gap: 6 },
  cardTitle: { fontSize: 20, fontWeight: "900", color: Theme.colors.text },
  meta: { fontSize: 15, fontWeight: "700", color: Theme.colors.muted },
  empty: { textAlign: "center", color: Theme.colors.muted, fontWeight: "700", paddingTop: 40 },
});
