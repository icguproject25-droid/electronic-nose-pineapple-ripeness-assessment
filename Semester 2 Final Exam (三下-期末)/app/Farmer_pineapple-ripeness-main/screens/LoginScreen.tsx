import { router } from "expo-router";
import React, { useState } from "react";
import { Alert, StyleSheet, Text, TextInput, View } from "react-native";

import { AppButton } from "@/components/AppButton";
import { Theme } from "@/constants/theme";
import { useAppStore } from "@/store/app-store";

/**
 * 登入畫面。
 *
 * 此畫面依照 Tinazhen/Farmer_pineapple/expo 的登入流程設計：
 * - 預設 PIN 為 1234。
 * - 也可以直接進入 Demo 模式，方便展示農民端流程。
 */
export default function LoginScreen() {
  const [pin, setPin] = useState("");
  const { login, enterDemo, tx } = useAppStore();

  function onLogin() {
    const ok = login(pin);
    if (!ok) {
      Alert.alert(tx("loginTitle"), tx("invalidPin"));
      return;
    }
    router.replace("/");
  }

  function onDemo() {
    enterDemo();
    router.replace("/");
  }

  return (
    <View style={styles.container} testID="login-screen">
      <Text style={styles.title}>{tx("appName")}</Text>
      <Text style={styles.subtitle}>{tx("loginTitle")}</Text>
      <TextInput
        testID="pin-input"
        style={styles.input}
        value={pin}
        onChangeText={setPin}
        placeholder={tx("pinPlaceholder")}
        keyboardType="numeric"
        secureTextEntry
        maxLength={4}
      />
      <View style={styles.actions}>
        <AppButton label={tx("enter")} onPress={onLogin} testID="login-btn" />
        <AppButton label={tx("demoMode")} onPress={onDemo} variant="secondary" testID="demo-btn" />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background, padding: 20, justifyContent: "center", gap: 16 },
  title: { fontSize: 28, fontWeight: "900", color: Theme.colors.primaryDark },
  subtitle: { fontSize: 16, color: Theme.colors.muted, fontWeight: "700" },
  input: { height: 56, backgroundColor: Theme.colors.card, borderWidth: 1, borderColor: Theme.colors.border, borderRadius: 16, paddingHorizontal: 16, fontSize: 20, letterSpacing: 8 },
  actions: { gap: 10 },
});
