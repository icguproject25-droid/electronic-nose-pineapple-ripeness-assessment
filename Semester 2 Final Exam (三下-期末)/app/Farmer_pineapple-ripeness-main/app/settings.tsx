import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Theme } from '@/constants/theme';
import { pingServer } from '@/services/api';
import { useFarmerStore } from '@/stores/farmerStore';

/**
 * 設定頁。
 *
 * 功能：
 * - 設定 Raspberry Pi / Gateway API base URL。
 * - 設定外銷與內銷糖度門檻。
 * - 提供 /ping 連線測試，方便確認手機是否能連到 RPi。
 */
export default function SettingsScreen() {
  const settings = useFarmerStore((state) => state.settings);
  const updateSettings = useFarmerStore((state) => state.updateSettings);

  const [apiBaseUrl, setApiBaseUrl] = useState(settings.apiBaseUrl);
  const [exportBrix, setExportBrix] = useState(String(settings.exportBrixThreshold));
  const [domesticBrix, setDomesticBrix] = useState(String(settings.domesticBrixThreshold));
  const [statusText, setStatusText] = useState('尚未測試連線');

  /** 儲存設定到 Zustand store。 */
  function handleSave() {
    updateSettings({
      apiBaseUrl,
      exportBrixThreshold: Number(exportBrix) || settings.exportBrixThreshold,
      domesticBrixThreshold: Number(domesticBrix) || settings.domesticBrixThreshold
    });
    setStatusText('設定已儲存');
  }

  /** 呼叫 /ping 確認後端是否可連線。 */
  async function handlePing() {
    setStatusText('測試連線中...');
    const ok = await pingServer(apiBaseUrl);
    setStatusText(ok ? '連線成功：後端已上線' : '連線失敗：請檢查 IP、Port 或同一 Wi-Fi');
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>設定</Text>
      <Text style={styles.subtitle}>設定農民端 App 與 Raspberry Pi 後端的連線資訊。</Text>

      <View style={styles.inputGroup}>
        <Text style={styles.label}>後端 API Base URL</Text>
        <TextInput value={apiBaseUrl} onChangeText={setApiBaseUrl} autoCapitalize="none" style={styles.input} />
        <Text style={styles.hint}>範例：http://172.20.10.2:5000 或 http://192.168.0.152:5000</Text>
      </View>

      <View style={styles.inputGroup}>
        <Text style={styles.label}>外銷糖度門檻 Brix</Text>
        <TextInput value={exportBrix} onChangeText={setExportBrix} keyboardType="numeric" style={styles.input} />
      </View>

      <View style={styles.inputGroup}>
        <Text style={styles.label}>內銷糖度門檻 Brix</Text>
        <TextInput value={domesticBrix} onChangeText={setDomesticBrix} keyboardType="numeric" style={styles.input} />
      </View>

      <Pressable style={styles.button} onPress={handleSave}>
        <Text style={styles.buttonText}>儲存設定</Text>
      </Pressable>

      <Pressable style={styles.secondaryButton} onPress={handlePing}>
        <Text style={styles.secondaryButtonText}>測試後端連線 /ping</Text>
      </Pressable>

      <Text style={styles.status}>{statusText}</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background },
  content: { padding: Theme.spacing.xl, paddingBottom: Theme.spacing.xxl },
  title: { color: Theme.colors.primaryDark, fontSize: Theme.fontSize.xl, fontWeight: '900' },
  subtitle: { color: Theme.colors.muted, marginTop: Theme.spacing.sm, marginBottom: Theme.spacing.lg },
  inputGroup: { marginBottom: Theme.spacing.lg },
  label: { color: Theme.colors.text, fontWeight: '800', marginBottom: Theme.spacing.sm },
  input: { backgroundColor: Theme.colors.card, borderColor: Theme.colors.border, borderWidth: 1, borderRadius: Theme.radius.md, padding: Theme.spacing.lg, fontSize: Theme.fontSize.md },
  hint: { color: Theme.colors.muted, fontSize: Theme.fontSize.sm, marginTop: Theme.spacing.sm },
  button: { backgroundColor: Theme.colors.primary, borderRadius: Theme.radius.lg, padding: Theme.spacing.lg, alignItems: 'center', marginBottom: Theme.spacing.md },
  buttonText: { color: '#FFFFFF', fontWeight: '900', fontSize: Theme.fontSize.md },
  secondaryButton: { backgroundColor: Theme.colors.warningSoft, borderColor: Theme.colors.accent, borderWidth: 1, borderRadius: Theme.radius.lg, padding: Theme.spacing.lg, alignItems: 'center', marginBottom: Theme.spacing.lg },
  secondaryButtonText: { color: Theme.colors.warning, fontWeight: '900' },
  status: { color: Theme.colors.text, backgroundColor: Theme.colors.card, padding: Theme.spacing.lg, borderRadius: Theme.radius.lg }
});
