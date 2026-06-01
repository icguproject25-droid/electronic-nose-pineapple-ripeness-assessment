/**
 * 農民端 App 的全域視覺設定。
 *
 * 專案目的：
 * - 統一顏色、間距、圓角與字級，避免每個頁面自行寫死樣式。
 * - 後續若要改成比賽簡報指定色系，只需要調整這個檔案。
 *
 * 注意：
 * - React Native 不支援一般 CSS class，因此這裡以物件常數方式集中管理。
 * - 顏色以田間、鳳梨與農業情境為主，使用綠色與暖色系。
 */
export const Theme = {
  colors: {
    background: '#F7FAF2',
    card: '#FFFFFF',
    primary: '#2E7D32',
    primaryDark: '#1B5E20',
    accent: '#F9A825',
    danger: '#C62828',
    warning: '#EF6C00',
    text: '#1F2933',
    muted: '#6B7280',
    border: '#DDE7D6',
    successSoft: '#E8F5E9',
    warningSoft: '#FFF8E1',
    dangerSoft: '#FFEBEE'
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
    xxl: 32
  },
  radius: {
    sm: 8,
    md: 14,
    lg: 20
  },
  fontSize: {
    sm: 13,
    md: 16,
    lg: 20,
    xl: 26
  }
} as const;
