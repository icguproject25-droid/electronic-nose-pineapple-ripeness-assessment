import { Stack, router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { AppButton } from "@/components/AppButton";
import { Theme } from "@/constants/theme";

export default function ModalScreen() {
  return (
    <View style={styles.container}>
      <Stack.Screen options={{ title: "Info" }} />
      <Text style={styles.title}>Farmer Console</Text>
      <Text style={styles.text}>Use this app to run batch scans and manage grading data.</Text>
      <AppButton label="Close" onPress={() => router.back()} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, justifyContent: "center", backgroundColor: Theme.colors.background, gap: 10 },
  title: { fontSize: 24, fontWeight: "800", color: Theme.colors.primaryDark },
  text: { color: Theme.colors.muted, marginBottom: 10 },
});
