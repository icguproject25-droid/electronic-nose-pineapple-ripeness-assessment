import React from "react";
import { ScrollView, ScrollViewProps } from "react-native";

/**
 * DemoScrollView
 *
 * 這個元件保留 Farmer_pineapple/expo 的命名與使用方式，
 * 目前功能是包裝 React Native ScrollView。
 * 後續若要加入展示模式提示條、浮水印或 Demo 標籤，可以集中在此元件處理。
 */
export function DemoScrollView(props: ScrollViewProps) {
  return <ScrollView {...props} />;
}
