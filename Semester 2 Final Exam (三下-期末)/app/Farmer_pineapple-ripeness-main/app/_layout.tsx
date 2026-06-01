import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Theme } from '@/constants/theme';

/**
 * Expo Router 根佈局。
 *
 * 這個檔案是整個 App 的入口佈局，功能類似 React Navigation 的 Navigator。
 *
 * 主要工作：
 * 1. 建立 React Query Provider，後續若要把掃描 API 改成 useMutation / useQuery 可直接使用。
 * 2. 設定所有頁面的 Stack 路由。
 * 3. 統一頁面背景色與轉場動畫。
 */
const queryClient = new QueryClient();

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: Theme.colors.background },
          animation: 'slide_from_right'
        }}
      >
        <Stack.Screen name="index" />
        <Stack.Screen name="batches" />
        <Stack.Screen name="batch-create" />
        <Stack.Screen name="batch-scan" />
        <Stack.Screen name="batch-summary" />
        <Stack.Screen name="reports" />
        <Stack.Screen name="settings" />
      </Stack>
    </QueryClientProvider>
  );
}
