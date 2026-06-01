import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import React, { useEffect } from "react";
import { GestureHandlerRootView } from "react-native-gesture-handler";

import { AppProvider, useAppStore } from "@/store/app-store";

SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient();

function RootLayoutNav() {
  const { isAuthenticated } = useAppStore();

  return (
    <Stack screenOptions={{ headerBackTitle: "Back" }}>
      {!isAuthenticated ? <Stack.Screen name="login" options={{ headerShown: false }} /> : null}
      <Stack.Screen name="(tabs)" options={{ headerShown: isAuthenticated }} />
      <Stack.Screen name="batches/create" options={{ presentation: "card", title: "建立批次" }} />
      <Stack.Screen name="batches/[batchId]/index" options={{ presentation: "card", title: "批次詳情" }} />
      <Stack.Screen name="batches/[batchId]/scan" options={{ presentation: "card", title: "批次掃描" }} />
      <Stack.Screen name="batches/[batchId]/summary" options={{ presentation: "card", title: "批次摘要" }} />
      <Stack.Screen name="modal" options={{ presentation: "modal", title: "Info" }} />
    </Stack>
  );
}

export default function RootLayout() {
  useEffect(() => {
    SplashScreen.hideAsync();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <AppProvider>
        <GestureHandlerRootView style={{ flex: 1 }}>
          <RootLayoutNav />
        </GestureHandlerRootView>
      </AppProvider>
    </QueryClientProvider>
  );
}
