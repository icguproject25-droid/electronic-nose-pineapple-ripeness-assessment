import React from "react";
import { Pressable, StyleSheet, Text, ViewStyle } from "react-native";
import { Theme } from "@/constants/theme";

interface AppButtonProps {
  label: string;
  onPress: () => void;
  variant?: "primary" | "secondary";
  style?: ViewStyle;
  testID?: string;
}

/**
 * 共用按鈕元件。
 *
 * 此元件參考 Tinazhen/Farmer_pineapple/expo 的按鈕使用方式，
 * 將主要按鈕與次要按鈕統一成同一個元件，讓首頁、登入、批次建立、掃描頁可以重複使用。
 */
export function AppButton({ label, onPress, variant = "primary", style, testID }: AppButtonProps) {
  const isPrimary = variant === "primary";

  return (
    <Pressable
      testID={testID}
      onPress={onPress}
      style={({ pressed }) => [styles.button, isPrimary ? styles.primary : styles.secondary, pressed && styles.pressed, style]}
    >
      <Text style={[styles.label, isPrimary ? styles.primaryText : styles.secondaryText]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 56,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 18,
    paddingVertical: 12,
  },
  primary: {
    backgroundColor: Theme.colors.primary,
  },
  secondary: {
    backgroundColor: Theme.colors.successSoft,
    borderWidth: 1,
    borderColor: Theme.colors.border,
  },
  pressed: {
    opacity: 0.72,
  },
  label: {
    fontSize: 16,
    fontWeight: "900",
  },
  primaryText: {
    color: "#FFFFFF",
  },
  secondaryText: {
    color: Theme.colors.primaryDark,
  },
});
