import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Animated,
  Easing,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Stack, useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ChevronLeft, Activity, Settings as SettingsIcon } from 'lucide-react-native';
import { useLanguage } from '@/contexts/LanguageContext';
import { useCalibration } from '@/contexts/CalibrationContext';

const Palette = {
  cream: '#FFFDD0',
  creamSoft: '#FFF9E0',
  yellow: '#FFC107',
  orange: '#FF9800',
  olive: '#556B2F',
  oliveDark: '#3F4F22',
  white: '#FFFFFF',
  textMuted: '#7A7A6A',
  border: 'rgba(85,107,47,0.08)',
};

export default function SettingsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { language } = useLanguage();
  const isZh = language !== 'en';

  const { isCalibrating, secondsLeft, duration, start } = useCalibration();

  const pulseAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (isCalibrating) {
      const loop = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 900,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 0,
            duration: 900,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
        ])
      );
      loop.start();
      return () => {
        loop.stop();
      };
    }
    return undefined;
  }, [isCalibrating, pulseAnim]);

  const handleBack = () => {
    router.replace('/menu' as any);
  };

  const progress = 1 - secondsLeft / duration;
  const pulseScale = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 1.06],
  });

  return (
    <View style={styles.container}>
      <Stack.Screen options={{ headerShown: false }} />

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[
          styles.scrollContent,
          { paddingTop: insets.top + 140, paddingBottom: insets.bottom + 24 },
        ]}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.sectionLabelWrap}>
          <Text style={styles.sectionLabel}>
            {isZh ? '感測器設定' : 'Sensor Settings'}
          </Text>
        </View>

        <View style={styles.card}>
          <Animated.View
            style={[
              styles.cardIconWrap,
              isCalibrating && { transform: [{ scale: pulseScale }] },
            ]}
          >
            <Activity size={22} color={Palette.olive} strokeWidth={2} />
          </Animated.View>
          <View style={styles.cardTextWrap}>
            <Text style={styles.cardTitle}>
              {isZh ? '校正基準數據' : 'Calibrate Baseline'}
            </Text>
            <Text style={styles.cardDesc}>
              {isZh
                ? '校正過程約 30 秒，校正期間可繼續使用其他功能。'
                : 'Calibration takes about 30 seconds. You can keep using other features.'}
            </Text>
          </View>
        </View>

        {isCalibrating && (
          <View style={styles.progressCard}>
            <View style={styles.progressHeader}>
              <Text style={styles.progressLabel}>
                {isZh ? '校正中…' : 'Calibrating…'}
              </Text>
              <Text style={styles.progressSeconds}>{secondsLeft}s</Text>
            </View>
            <View style={styles.progressTrack}>
              <View
                style={[
                  styles.progressFill,
                  { width: `${Math.min(100, Math.max(0, progress * 100))}%` },
                ]}
              />
            </View>
            <Text style={styles.progressHint}>
              {isZh
                ? '完成後將自動恢復，可隨時返回首頁繼續使用其他功能。'
                : 'Will resume automatically. You can navigate back anytime.'}
            </Text>
          </View>
        )}

        <TouchableOpacity
          style={[styles.calibrateButton, isCalibrating && styles.calibrateButtonDisabled]}
          onPress={start}
          activeOpacity={0.9}
          disabled={isCalibrating}
          testID="btn-calibrate"
        >
          <LinearGradient
            colors={
              isCalibrating
                ? ['#B5B5A8', '#9A9A8C']
                : [Palette.yellow, Palette.orange]
            }
            style={styles.calibrateGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
          >
            <Text style={styles.calibrateText}>
              {isCalibrating
                ? isZh
                  ? `校正中… ${secondsLeft}s`
                  : `Calibrating… ${secondsLeft}s`
                : isZh
                ? '開始校正'
                : 'Start Calibration'}
            </Text>
          </LinearGradient>
        </TouchableOpacity>
      </ScrollView>
      </KeyboardAvoidingView>

      <View
        style={[styles.headerWrap, { height: insets.top + 120 }]}
        pointerEvents="box-none"
      >
        <LinearGradient
          colors={[Palette.yellow, Palette.orange]}
          style={styles.headerGradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          pointerEvents="none"
        />
        <View style={[styles.headerRow, { paddingTop: insets.top + 12 }]}>
          <TouchableOpacity
            onPress={handleBack}
            style={styles.backBtn}
            activeOpacity={0.8}
            testID="btn-settings-back"
            hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
          >
            <ChevronLeft size={22} color={Palette.white} strokeWidth={2.4} />
          </TouchableOpacity>
          <View style={styles.headerTitleWrap}>
            <SettingsIcon size={18} color={Palette.white} strokeWidth={2.2} />
            <Text style={styles.headerTitle}>{isZh ? '設定' : 'Settings'}</Text>
          </View>
          <View style={{ width: 40 }} />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Palette.cream,
  },
  flex: {
    flex: 1,
  },
  apiCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Palette.white,
    borderRadius: 20,
    paddingVertical: 10,
    paddingHorizontal: 12,
    gap: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
    marginBottom: 18,
  },
  apiIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Palette.creamSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  apiInput: {
    flex: 1,
    fontSize: 14,
    color: Palette.oliveDark,
    paddingVertical: 8,
    paddingHorizontal: 4,
  },
  apiSaveBtn: {
    backgroundColor: Palette.olive,
    borderRadius: 14,
    paddingVertical: 8,
    paddingHorizontal: 14,
  },
  apiSaveText: {
    fontSize: 13,
    fontWeight: '700' as const,
    color: Palette.white,
    letterSpacing: 0.3,
  },
  collapseHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: Palette.white,
    borderRadius: 16,
    paddingVertical: 12,
    paddingHorizontal: 14,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 1,
  },
  collapseHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  collapseIconWrap: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Palette.creamSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  collapseTitle: {
    fontSize: 13,
    fontWeight: '700' as const,
    color: Palette.oliveDark,
    letterSpacing: 0.3,
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  modalCard: {
    width: '100%',
    maxWidth: 420,
    backgroundColor: Palette.white,
    borderRadius: 24,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.18,
    shadowRadius: 24,
    elevation: 10,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: '800' as const,
    color: Palette.oliveDark,
    letterSpacing: 0.3,
  },
  modalClose: {
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Palette.creamSoft,
  },
  modalHint: {
    fontSize: 12,
    color: Palette.textMuted,
    lineHeight: 17,
    marginBottom: 14,
  },
  segmentWrap: {
    flexDirection: 'row',
    backgroundColor: Palette.creamSoft,
    borderRadius: 14,
    padding: 4,
    gap: 4,
    marginBottom: 14,
  },
  segmentBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    borderRadius: 11,
  },
  segmentBtnActive: {
    backgroundColor: Palette.olive,
  },
  segmentText: {
    fontSize: 13,
    fontWeight: '700' as const,
    color: Palette.olive,
    letterSpacing: 0.3,
  },
  segmentTextActive: {
    color: Palette.white,
  },
  modalInputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: Palette.creamSoft,
    borderRadius: 14,
    paddingHorizontal: 14,
    marginBottom: 10,
  },
  modalInput: {
    flex: 1,
    fontSize: 14,
    color: Palette.oliveDark,
    paddingVertical: 12,
  },
  modalFooterHint: {
    fontSize: 11,
    color: Palette.textMuted,
    lineHeight: 16,
    marginBottom: 16,
  },
  modalApplyBtn: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  modalApplyGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
  },
  modalApplyText: {
    fontSize: 15,
    fontWeight: '800' as const,
    color: Palette.white,
    letterSpacing: 0.4,
  },
  ngrokHint: {
    fontSize: 11,
    color: Palette.textMuted,
    lineHeight: 16,
    paddingHorizontal: 4,
    marginTop: -8,
    marginBottom: 18,
  },
  headerWrap: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    overflow: 'hidden',
  },
  headerGradient: {
    ...StyleSheet.absoluteFillObject,
    borderBottomLeftRadius: 36,
    borderBottomRightRadius: 36,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.22)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitleWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800' as const,
    color: Palette.white,
    letterSpacing: 0.4,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
  },
  sectionLabelWrap: {
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '700' as const,
    color: Palette.textMuted,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Palette.white,
    borderRadius: 20,
    paddingVertical: 16,
    paddingHorizontal: 16,
    gap: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
    marginBottom: 14,
  },
  cardIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Palette.creamSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardTextWrap: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700' as const,
    color: Palette.oliveDark,
    marginBottom: 2,
  },
  cardDesc: {
    fontSize: 12,
    color: Palette.textMuted,
    lineHeight: 18,
  },
  progressCard: {
    backgroundColor: Palette.white,
    borderRadius: 20,
    paddingVertical: 16,
    paddingHorizontal: 18,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
    borderWidth: 1,
    borderColor: 'rgba(255,193,7,0.35)',
  },
  progressHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  progressLabel: {
    fontSize: 14,
    fontWeight: '700' as const,
    color: Palette.oliveDark,
  },
  progressSeconds: {
    fontSize: 18,
    fontWeight: '800' as const,
    color: Palette.orange,
  },
  progressTrack: {
    width: '100%',
    height: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(85,107,47,0.08)',
    overflow: 'hidden',
    marginBottom: 10,
  },
  progressFill: {
    height: '100%',
    backgroundColor: Palette.yellow,
    borderRadius: 4,
  },
  progressHint: {
    fontSize: 11,
    color: Palette.textMuted,
    lineHeight: 16,
  },
  calibrateButton: {
    borderRadius: 24,
    overflow: 'hidden',
    shadowColor: Palette.orange,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.22,
    shadowRadius: 14,
    elevation: 6,
  },
  calibrateButtonDisabled: {
    shadowOpacity: 0.1,
    opacity: 0.85,
  },
  calibrateGradient: {
    paddingVertical: 18,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  calibrateText: {
    fontSize: 16,
    fontWeight: '800' as const,
    color: Palette.white,
    letterSpacing: 0.5,
  },
});
