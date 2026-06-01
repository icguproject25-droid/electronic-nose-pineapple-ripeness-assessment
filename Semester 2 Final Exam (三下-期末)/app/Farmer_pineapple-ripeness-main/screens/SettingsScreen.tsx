import React, { useState } from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";

import { AppButton } from "@/components/AppButton";
import { Theme } from "@/constants/theme";
import { useAppStore } from "@/store/app-store";

export default function SettingsScreen() {
  const { settings, updateSettings, setLanguage } = useAppStore();
  const [serverUrl, setServerUrl] = useState(settings.device.raspberryPiUrl);
  const [ratio, setRatio] = useState(String(settings.thresholds.samplingRatio));
  const [status, setStatus] = useState("尚未儲存");

  function saveSettings() {
    const nextRatio = Number(ratio) || settings.thresholds.samplingRatio;
    updateSettings({
      backendUrl: serverUrl,
      device: { ...settings.device, raspberryPiUrl: serverUrl },
      thresholds: { ...settings.thresholds, samplingRatio: nextRatio },
    });
    setStatus("設定已儲存");
  }

  return (
    <View style={styles.container} testID="settings-screen">
      <Text style={styles.title}>設定</Text>
      <View style={styles.card}>
        <Text style={styles.label}>Raspberry Pi URL</Text>
        <TextInput value={serverUrl} onChangeText={setServerUrl} style={styles.input} />
        <Text style={styles.label}>抽樣比例</Text>
        <TextInput value={ratio} onChangeText={setRatio} keyboardType="numeric" style={styles.input} />
      </View>
      <AppButton label="儲存設定" onPress={saveSettings} />
      <AppButton label="中文" variant="secondary" onPress={() => setLanguage("zh")} />
      <AppButton label="English" variant="secondary" onPress={() => setLanguage("en")} />
      <Text style={styles.status}>{status}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background, padding: 18, gap: 14 },
  title: { fontSize: 30, fontWeight: "900", color: Theme.colors.primaryDark },
  card: { backgroundColor: Theme.colors.card, borderRadius: 22, borderWidth: 1, borderColor: Theme.colors.border, padding: 16, gap: 12 },
  label: { fontSize: 16, fontWeight: "800", color: Theme.colors.text },
  input: { height: 54, borderRadius: 16, borderWidth: 1, borderColor: Theme.colors.border, backgroundColor: "#F7FAF4", paddingHorizontal: 14, fontSize: 16, fontWeight: "700" },
  status: { color: Theme.colors.muted, fontWeight: "700", textAlign: "center" },
});
