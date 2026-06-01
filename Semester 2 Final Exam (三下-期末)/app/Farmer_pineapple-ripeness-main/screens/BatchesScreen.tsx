import { router, Stack } from "expo-router";
import React, { useMemo, useState } from "react";
import { FlatList, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { AppButton } from "@/components/AppButton";
import { Theme } from "@/constants/theme";
import { useAppStore } from "@/store/app-store";

/**
 * 批次管理畫面。
 *
 * 這個畫面沿用 Farmer_pineapple/expo 的列表邏輯：
 * - 可搜尋批次名稱。
 * - 可建立新批次。
 * - 未完成批次點擊後進入掃描頁。
 * - 已完成批次點擊後進入摘要頁。
 */
export default function BatchesScreen() {
  const { batches, samples, tx } = useAppStore();
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    return batches.filter((batch) => batch.name.toLowerCase().includes(query.toLowerCase()));
  }, [batches, query]);

  return (
    <View style={styles.container} testID="batches-screen">
      <Stack.Screen options={{ title: tx("batches") }} />
      <TextInput style={styles.searchInput} placeholder="搜尋批次" value={query} onChangeText={setQuery} testID="search-input" />
      <AppButton label={tx("newBatch")} onPress={() => router.push("/batches/create")} style={styles.createButton} testID="create-batch-btn" />
      <FlatList
        testID="batch-list"
        data={filtered}
        keyExtractor={(item) => item.batch_id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={<Text style={styles.empty}>{tx("noData")}</Text>}
        renderItem={({ item }) => {
          const scanned = samples.filter((sample) => sample.batch_id === item.batch_id).length;
          const destination = item.status === "done" ? `/batches/${item.batch_id}/summary` : `/batches/${item.batch_id}/scan`;
          return (
            <Pressable style={styles.itemCard} onPress={() => router.push(destination as never)} testID={`batch-item-${item.batch_id}`}>
              <View style={styles.itemTextWrap}>
                <Text style={styles.itemTitle}>{item.name}</Text>
                <Text style={styles.itemMeta}>{item.block} · {scanned}/{item.target_samples}</Text>
              </View>
              <Text style={styles.itemAction}>{item.status === "done" ? tx("summary") : tx("startScan")}</Text>
            </Pressable>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background, padding: 18, gap: 14 },
  searchInput: { height: 58, backgroundColor: Theme.colors.card, borderWidth: 1, borderColor: Theme.colors.border, borderRadius: 18, paddingHorizontal: 16, fontSize: 18, fontWeight: "700", color: Theme.colors.text },
  createButton: { minHeight: 66, borderRadius: 20 },
  list: { gap: 12, paddingBottom: 90 },
  itemCard: { flexDirection: "row", alignItems: "center", gap: 12, backgroundColor: Theme.colors.card, borderWidth: 1, borderColor: Theme.colors.border, borderRadius: 22, paddingHorizontal: 16, paddingVertical: 18 },
  itemTextWrap: { flex: 1, gap: 4 },
  itemTitle: { fontSize: 21, fontWeight: "800", color: Theme.colors.text },
  itemMeta: { fontSize: 15, fontWeight: "700", color: Theme.colors.muted },
  itemAction: { fontSize: 15, fontWeight: "800", color: Theme.colors.primary },
  empty: { paddingTop: 30, textAlign: "center", color: Theme.colors.muted, fontSize: 16, fontWeight: "600" },
});
