import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Modal, Pressable, TextInput, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Search, Clock, Globe, Upload, Leaf, BookOpen, ChevronRight, Settings as SettingsIcon, Camera as CameraIcon, Network, X, Check, Wifi } from 'lucide-react-native';
import { useLanguage } from '@/contexts/LanguageContext';
import { useUploadQueue } from '@/contexts/UploadQueueContext';
import { useHistory } from '@/contexts/HistoryContext';
import { useCalibration } from '@/contexts/CalibrationContext';
import { PineappleIcon } from '@/components/PineappleIcon';
import {
  getApiBaseUrl,
  setApiBaseUrl,
  getVarietyApiBaseUrl,
  setVarietyApiBaseUrl,
  DEFAULT_API_URL,
  DEFAULT_VARIETY_API_URL,
} from '@/services/storage';

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

export default function MenuScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { t, resetLanguage, language } = useLanguage();
  const { queueCount } = useUploadQueue();
  const { records } = useHistory();
  const { isCalibrating } = useCalibration();
  const isZh = language !== 'en';

  const [ipModalVisible, setIpModalVisible] = useState<boolean>(false);
  const [apiUrl, setApiUrl] = useState<string>(DEFAULT_API_URL);
  const [apiUrlInput, setApiUrlInput] = useState<string>(DEFAULT_API_URL);
  const [varietyApiUrl, setVarietyApiUrl] = useState<string>(DEFAULT_VARIETY_API_URL);
  const [varietyApiUrlInput, setVarietyApiUrlInput] = useState<string>(DEFAULT_VARIETY_API_URL);

  useEffect(() => {
    (async () => {
      try {
        const saved = await getApiBaseUrl();
        setApiUrl(saved);
        setApiUrlInput(saved);
        const savedVariety = await getVarietyApiBaseUrl();
        setVarietyApiUrl(savedVariety);
        setVarietyApiUrlInput(savedVariety);
      } catch (e) {
        console.log('[Menu] load api url failed', e);
      }
    })();
  }, []);

  const openIpModal = async () => {
    try {
      const saved = await getApiBaseUrl();
      const savedVariety = await getVarietyApiBaseUrl();
      setApiUrl(saved);
      setApiUrlInput(saved);

      
      setVarietyApiUrl(savedVariety);
      setVarietyApiUrlInput(savedVariety);

    } catch {}
    setIpModalVisible(true);
  };

  const handleApplyIp = async () => {
    const trimmed = apiUrlInput.trim();
    const trimmedVariety = varietyApiUrlInput.trim();
    if (!trimmed || !/^https?:\/\//i.test(trimmed)) {
      Alert.alert(isZh ? '網址無效' : 'Invalid URL', isZh ? '請輸入以 http:// 或 https:// 開頭的網址。' : 'Enter a URL starting with http:// or https://');
      return;
    }
    
    if (!trimmedVariety || !/^https?:\/\//i.test(trimmedVariety)) {
      Alert.alert(isZh ? '網址無效' : 'Invalid URL', isZh ? '請輸入以 http:// 或 https:// 開頭的網址。' : 'Enter a URL starting with http:// or https://');
      return;
    }
    try {

      console.log('Sensor API:', trimmed);
      console.log('Variety API:', trimmedVariety);

  
      await setApiBaseUrl(trimmed);
      await setVarietyApiBaseUrl(trimmedVariety);

      const saved = await getApiBaseUrl();
      const savedVariety = await getVarietyApiBaseUrl();

      setApiUrl(saved);
      setApiUrlInput(saved);

      setVarietyApiUrl(savedVariety);
      setVarietyApiUrlInput(savedVariety);

      setIpModalVisible(false);
      Alert.alert(isZh ? '已套用' : 'Applied', `${saved}\n${savedVariety}`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      Alert.alert(isZh ? '錯誤' : 'Error', msg);
    }
  };

  const handleResetIp = () => {
    setApiUrlInput(DEFAULT_API_URL);
    setVarietyApiUrlInput(DEFAULT_VARIETY_API_URL);
  };

  const handleStartScan = () => {
    if (isCalibrating) {
      Alert.alert(
        isZh ? '校正基準數據中' : 'Calibrating baseline',
        isZh
          ? '目前正在校正基準數據，請等待校正完成後再開始感測鳳梨。'
          : 'Baseline calibration is in progress. Please start sensing after calibration is complete.'
      );
      return;
    }

    router.push('/instruction' as any);
  };

  const handleLanguageChange = async () => {
    await resetLanguage();
    router.replace('/');
  };

  const handlePendingUploads = () => {
    router.push('/pending-uploads' as any);
  };

  const handleHistory = () => {
    router.push('/history' as any);
  };

  const handleVarieties = () => {
    router.push('/varieties' as any);
  };

  const handleTrivia = () => {
    router.push('/trivia' as any);
  };

  const handleSettings = () => {
    router.push('/settings' as any);
  };

  const handleVarietyRecognition = () => {
    router.push('/variety-recognition' as any);
  };

  return (
    <View style={styles.container}>
      <View style={[styles.headerWrap, { height: insets.top + 140 }]} pointerEvents="box-none">
        <LinearGradient
          colors={[Palette.yellow, Palette.orange]}
          style={styles.headerGradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <View style={styles.headerPattern} pointerEvents="none">
            {Array.from({ length: 18 }).map((_, i) => {
              const row = Math.floor(i / 6);
              const col = i % 6;
              return (
                <View
                  key={i}
                  style={[
                    styles.patternDot,
                    {
                      top: 20 + row * 44,
                      left: 10 + col * 60 + (row % 2 === 0 ? 0 : 30),
                    },
                  ]}
                />
              );
            })}
          </View>
        </LinearGradient>
        <TouchableOpacity
          onPress={openIpModal}
          activeOpacity={0.85}
          style={[styles.ipBtn, { top: insets.top + 12 }]}
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
          testID="btn-open-ip"
        >
          <Network size={16} color={Palette.white} strokeWidth={2.4} />
          <Text style={styles.ipBtnText} numberOfLines={1}>
            {isZh ? '伺服器' : 'Server'}
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[
          styles.scrollContent,
          { paddingTop: insets.top + 80, paddingBottom: insets.bottom + 24 },
        ]}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.heroCard}>
          <View style={styles.illustrationWrap}>
            <PineappleIcon size={96} />
          </View>
          <Text style={styles.appTitle}>{t('appName')}</Text>
          <View style={styles.titleUnderline} />
        </View>

        <TouchableOpacity
          style={[styles.mainButton, isCalibrating && styles.mainButtonDisabled]}
          onPress={handleStartScan}
          activeOpacity={isCalibrating ? 1 : 0.9}
          testID="btn-start-scan"
        >
          <LinearGradient
            colors={[Palette.yellow, Palette.orange]}
            style={styles.mainButtonGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            pointerEvents="none"
          >
            <View style={styles.scanIconCircle}>
              <Search size={22} color={Palette.white} strokeWidth={2.6} />
            </View>
            <Text style={styles.mainButtonText}>
              {isCalibrating
                ? isZh
                  ? '校正基準數據中'
                  : 'Calibrating baseline'
                : t('startScan')}
            </Text>
          </LinearGradient>
        </TouchableOpacity>

        <View style={styles.menuList}>
          <MenuCard
            icon={<Leaf size={22} color={Palette.olive} strokeWidth={1.8} />}
            label={t('varietiesTitle')}
            onPress={handleVarieties}
            testID="btn-varieties"
          />

          <MenuCard
            icon={<BookOpen size={22} color={Palette.olive} strokeWidth={1.8} />}
            label={t('triviaTitle')}
            onPress={handleTrivia}
            testID="btn-trivia"
          />

          <MenuCard
            icon={<Clock size={22} color={Palette.olive} strokeWidth={1.8} />}
            label={t('history')}
            onPress={handleHistory}
            badge={records.length > 0 ? records.length : undefined}
            testID="btn-history"
          />

          <MenuCard
            icon={<CameraIcon size={22} color={Palette.olive} strokeWidth={1.8} />}
            label={t('varietyImageRecognition')}
            onPress={handleVarietyRecognition}
            testID="btn-variety-recognition"
          />

          <MenuCard
            icon={<SettingsIcon size={22} color={Palette.olive} strokeWidth={1.8} />}
            label={t('settings')}
            onPress={handleSettings}
            testID="btn-settings"
          />

          {queueCount > 0 && (
            <MenuCard
              icon={<Upload size={22} color={Palette.orange} strokeWidth={1.8} />}
              label={t('pendingUploads')}
              onPress={handlePendingUploads}
              badge={queueCount}
              badgeColor={Palette.orange}
              testID="btn-pending-uploads"
            />
          )}
        </View>

        <View style={styles.currentIpRow}>
          <Wifi size={12} color={Palette.textMuted} strokeWidth={2} />
          <Text style={styles.currentIpText} numberOfLines={1}>
            {isZh ? '目前伺服器' : 'Server'}: {apiUrl}
          </Text>
        </View>

        <View style={styles.footer}>
          <TouchableOpacity
            style={styles.languagePill}
            onPress={handleLanguageChange}
            activeOpacity={0.75}
            testID="btn-change-language"
          >
            <Globe size={16} color={Palette.olive} strokeWidth={2} />
            <Text style={styles.languagePillText}>{t('language')}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>

      <Modal
        visible={ipModalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setIpModalVisible(false)}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.modalBackdrop}
        >
          <Pressable style={styles.modalBackdropFill} onPress={() => setIpModalVisible(false)}>
            <Pressable style={styles.modalCard} onPress={(e) => e.stopPropagation()}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>
                  {isZh ? '伺服器位址' : 'Server URL'}
                </Text>
                <TouchableOpacity
                  onPress={() => setIpModalVisible(false)}
                  style={styles.modalClose}
                  hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                  testID="btn-close-ip"
                >
                  <X size={18} color={Palette.textMuted} strokeWidth={2.2} />
                </TouchableOpacity>
              </View>
              <Text style={styles.modalLabel}>
                {isZh ? '感測 API 位址' : 'Sensor API URL'}
              </Text>

              <View style={styles.modalInputWrap}>
                <Network size={16} color={Palette.olive} strokeWidth={2} />
                <TextInput
                  style={styles.modalInput}
                  value={apiUrlInput}
                  onChangeText={setApiUrlInput}
                  placeholder="http://192.168.43.251:5000"
                  placeholderTextColor={Palette.textMuted}
                  autoCapitalize="none"
                  autoCorrect={false}
                  keyboardType="url"
                  testID="input-ip"
                />
              </View>

              <Text style={styles.modalLabel}>
                {isZh ? '品種辨識 API 位址' : 'Variety API URL'}
              </Text>

              <View style={styles.modalInputWrap}>
                <CameraIcon size={16} color={Palette.olive} strokeWidth={2} />
                <TextInput
                  style={styles.modalInput}
                  value={varietyApiUrlInput}
                  onChangeText={setVarietyApiUrlInput}
                  placeholder="http://192.168.43.90:5001"
                  placeholderTextColor={Palette.textMuted}
                  autoCapitalize="none"
                  autoCorrect={false}
                  keyboardType="url"
                  testID="input-variety-ip"
                />
              </View>

              <Text style={styles.modalHint}>
                {isZh
                  ? '感測 API 用於成熟度判斷；品種辨識 API 用於照片品種辨識。'
                  : 'Sensor API is for ripeness sensing; Variety API is for image variety recognition.'}
              </Text>

              <TouchableOpacity
                onPress={handleResetIp}
                activeOpacity={0.7}
                style={styles.resetBtn}
                testID="btn-reset-ip"
              >
                <Text style={styles.resetBtnText}>
                  {isZh ? `重設為預設 (${DEFAULT_API_URL})` : `Reset default (${DEFAULT_API_URL})`}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.modalApplyBtn}
                onPress={handleApplyIp}
                activeOpacity={0.9}
                testID="btn-apply-ip"
              >
                <LinearGradient
                  colors={[Palette.yellow, Palette.orange]}
                  style={styles.modalApplyGradient}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                >
                  <Check size={16} color={Palette.white} strokeWidth={2.6} />
                  <Text style={styles.modalApplyText}>
                    {isZh ? '套用' : 'Apply'}
                  </Text>
                </LinearGradient>
              </TouchableOpacity>
            </Pressable>
          </Pressable>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

interface MenuCardProps {
  icon: React.ReactNode;
  label: string;
  onPress: () => void;
  badge?: number;
  badgeColor?: string;
  testID?: string;
}

function MenuCard({ icon, label, onPress, badge, badgeColor, testID }: MenuCardProps) {
  return (
    <TouchableOpacity
      style={styles.menuCard}
      onPress={onPress}
      activeOpacity={0.8}
      testID={testID}
    >
      <View style={styles.menuIcon}>{icon}</View>
      <Text style={styles.menuLabel}>{label}</Text>
      {typeof badge === 'number' && (
        <View style={[styles.menuBadge, badgeColor ? { backgroundColor: badgeColor } : null]}>
          <Text style={styles.menuBadgeText}>{badge}</Text>
        </View>
      )}
      <ChevronRight size={18} color={Palette.textMuted} strokeWidth={2} />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Palette.cream,
  },
  headerWrap: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    overflow: 'visible',
  },
  headerGradient: {
    flex: 1,
    borderBottomLeftRadius: 36,
    borderBottomRightRadius: 36,
  },
  headerPattern: {
    ...StyleSheet.absoluteFillObject,
  },
  patternDot: {
    position: 'absolute',
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.25)',
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
  },
  heroCard: {
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 28,
  },
  illustrationWrap: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: Palette.white,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 6,
  },
  appTitle: {
    marginTop: 18,
    fontSize: 22,
    fontWeight: '700' as const,
    color: Palette.oliveDark,
    letterSpacing: 0.3,
    textAlign: 'center',
  },
  titleUnderline: {
    marginTop: 10,
    width: 36,
    height: 3,
    borderRadius: 2,
    backgroundColor: Palette.yellow,
  },
  mainButton: {
    borderRadius: 28,
    overflow: 'hidden',
    shadowColor: Palette.orange,
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.25,
    shadowRadius: 18,
    elevation: 8,
    marginBottom: 28,
  },
  mainButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
    paddingHorizontal: 24,
    gap: 14,
  },
  scanIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.25)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  mainButtonText: {
    fontSize: 18,
    fontWeight: '800' as const,
    color: Palette.white,
    letterSpacing: 0.5,
  },
  menuList: {
    gap: 12,
  },
  menuCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Palette.white,
    borderRadius: 24,
    paddingVertical: 18,
    paddingHorizontal: 18,
    gap: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
  },
  menuIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Palette.creamSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuLabel: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600' as const,
    color: Palette.oliveDark,
  },
  menuBadge: {
    minWidth: 24,
    height: 24,
    paddingHorizontal: 8,
    borderRadius: 12,
    backgroundColor: Palette.olive,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuBadgeText: {
    fontSize: 12,
    fontWeight: '700' as const,
    color: Palette.white,
  },
  ipBtn: {
    position: 'absolute',
    right: 18,
    zIndex: 100,
    elevation: 100,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(63,79,34,0.35)',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.35)',
  },
  ipBtnText: {
    color: Palette.white,
    fontSize: 13,
    fontWeight: '700' as const,
    letterSpacing: 0.3,
  },
  currentIpRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 6,
    marginTop: 16,
  },
  currentIpText: {
    flex: 1,
    fontSize: 11,
    color: Palette.textMuted,
    fontWeight: '600' as const,
  },
  modalBackdrop: {
    flex: 1,
  },
  modalBackdropFill: {
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
  resetBtn: {
    alignSelf: 'flex-start',
    paddingVertical: 6,
    marginBottom: 12,
  },
  resetBtnText: {
    fontSize: 12,
    color: Palette.olive,
    fontWeight: '700' as const,
    textDecorationLine: 'underline',
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
  footer: {
    alignItems: 'center',
    marginTop: 36,
    marginBottom: 8,
  },
  languagePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 22,
    backgroundColor: 'rgba(85,107,47,0.08)',
    borderWidth: 1,
    borderColor: Palette.border,
  },
  languagePillText: {
    fontSize: 13,
    fontWeight: '600' as const,
    color: Palette.olive,
  },
  modalLabel: {
    fontSize: 13,
    fontWeight: '700' as const,
    color: Palette.oliveDark,
    marginTop: 12,
    marginBottom: 6,
  },

  mainButtonDisabled: { opacity: 0.55, },
});
