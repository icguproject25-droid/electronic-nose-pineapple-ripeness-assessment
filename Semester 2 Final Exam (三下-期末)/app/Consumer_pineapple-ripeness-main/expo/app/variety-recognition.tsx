import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Alert,
  Platform,
  Modal,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ArrowLeft, Camera, ImageIcon, AlertTriangle, CheckCircle2, Server, CalendarDays, ChevronDown, ChevronUp, Settings as SettingsIcon, X } from 'lucide-react-native';
import * as ImagePicker from 'expo-image-picker';
import { useLanguage } from '@/contexts/LanguageContext';
import { getApiBaseUrl, DEFAULT_API_URL } from '@/services/storage';
import { apiPredictVariety } from '@/services/api';

/**
 * Variety detection record matching the planned backend schema.
 * Used as the payload shape for future YOLOv8 + DB integration.
 */
interface VarietyDetectionRecord {
  variety_detection_id: string;
  device_id: string | null;
  user_id: string | null;
  image_path: string;
  pred_class: string;
  pred_zh_name: string;
  confidence: number;
  low_confidence: boolean;
  all_probs_json: string;
  created_at: string;
}

const Palette = {
  cream: '#FFFDD0',
  creamSoft: '#FFF9E0',
  yellow: '#FFC107',
  orange: '#FF9800',
  olive: '#556B2F',
  oliveDark: '#3F4F22',
  white: '#FFFFFF',
  textMuted: '#7A7A6A',
  border: 'rgba(85,107,47,0.12)',
  red: '#D9534F',
  green: '#4CAF50',
};

const LOW_CONFIDENCE_THRESHOLD = 0.6;

interface PredictionItem {
  label: string;
  labelEn?: string;
  score: number;
}

interface PredictionResponse {
  // ===== 舊版 API 欄位 =====
  variety?: string;
  variety_en?: string;
  confidence?: number;
  probabilities?: Record<string, number> | PredictionItem[];

  // ===== 新版 API 欄位 =====
  status?: string;
  message?: string;
  stage?: number;
  filename?: string;

  has_content?: boolean;
  is_pineapple?: boolean;
  low_confidence?: boolean;

  pred_class?: string | null;
  pred_zh_name?: string | null;

  all_probs?: Array<{
    class?: string;
    zh_name?: string;
    probability?: number;
  }>;

  bbox?: number[] | null;
  det_confidence?: number;
  num_boxes?: number;

  content_check?: {
    edge_ratio?: number;
    has_content?: boolean;
    mean_brightness?: number;
    std_brightness?: number;
    message?: string;
  };
}

const VARIETY_NAME_MAP: Record<string, { zh: string; en: string }> = {
  jinzuan: { zh: '金鑽鳳梨', en: 'Jinzuan' },
  local: { zh: '土鳳梨', en: 'Local Pineapple' },
  milk: { zh: '牛奶鳳梨', en: 'Milk Pineapple' },
  watermelon: { zh: '西瓜鳳梨', en: 'Watermelon Pineapple' },
  tainung17: { zh: '金鑽鳳梨', en: 'Tainung No.17' },
  md2: { zh: 'MD2 鳳梨', en: 'MD2' },
  smooth_cayenne: { zh: '開英種鳳梨', en: 'Smooth Cayenne' },
  kaiying: { zh: '開英種鳳梨', en: 'Smooth Cayenne' },
  sugarloaf: { zh: '牛奶鳳梨', en: 'Sugarloaf' },
  perola: { zh: '蘋果鳳梨', en: 'Perola' },
};

function normalizeVarietyName(key: string | null | undefined, lang: 'zh' | 'en'): string {
  if (!key) return lang === 'zh' ? '未偵測到鳳梨' : 'No pineapple detected';

  const k = key.toLowerCase().replace(/[\s_-]+/g, '_');
  const mapped = VARIETY_NAME_MAP[k];

  if (mapped) return lang === 'zh' ? mapped.zh : mapped.en;

  return key;
}

function formatDate(d: Date, lang: 'zh' | 'en'): string {
  const y = d.getFullYear();
  const m = d.getMonth() + 1;
  const day = d.getDate();
  if (lang === 'zh') return `${y}年${m}月${day}日`;
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
}

export default function VarietyRecognitionScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { language } = useLanguage();
  const lang = (language ?? 'zh') as 'zh' | 'en';

  const [imageUri, setImageUri] = useState<string | null>(null);
  const [imageMime, setImageMime] = useState<string>('image/jpeg');
  const [serverUrl, setServerUrl] = useState<string>(DEFAULT_API_URL);
  const [loading, setLoading] = useState<boolean>(false);
  const [topVariety, setTopVariety] = useState<{ zh: string; en: string } | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [probabilities, setProbabilities] = useState<PredictionItem[]>([]);
  const [settingsExpanded, setSettingsExpanded] = useState<boolean>(false);
  const [resultModalVisible, setResultModalVisible] = useState<boolean>(false);
  const [lastRecord, setLastRecord] = useState<VarietyDetectionRecord | null>(null);

  const today = useMemo(() => new Date(), []);

  useEffect(() => {
    (async () => {
      try {
        const saved = await getApiBaseUrl();
        if (saved) setServerUrl(saved);
      } catch (e) {
        console.log('[VarietyRecognition] load server url failed', e);
      }
    })();
  }, []);

  const validateImageAsset = (asset: ImagePicker.ImagePickerAsset): boolean => {
    const mime = asset.mimeType ?? '';
    const uri = asset.uri ?? '';
    const looksLikeImage =
      mime.startsWith('image/') || /\.(jpe?g|png)$/i.test(uri);
    if (!looksLikeImage) {
      Alert.alert(
        lang === 'zh' ? '檔案格式錯誤' : 'Invalid Format',
        lang === 'zh' ? '請選擇 JPEG 或 PNG 圖片。' : 'Please choose a JPEG or PNG image.',
      );
      return false;
    }
    return true;
  };

  const handleTakePhoto = async () => {
    try {
      const perm = await ImagePicker.requestCameraPermissionsAsync();
      if (!perm.granted) {
        Alert.alert(
          lang === 'zh' ? '需要相機權限' : 'Camera Permission Required',
          lang === 'zh' ? '請在設定中允許相機存取。' : 'Please allow camera access in settings.',
        );
        return;
      }
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.85,
        allowsEditing: false,
      });
      if (result.canceled || !result.assets?.[0]) return;
      const asset = result.assets[0];
      if (!validateImageAsset(asset)) return;
      setImageUri(asset.uri);
      setImageMime(asset.mimeType ?? 'image/jpeg');
      setTopVariety(null);
      setConfidence(null);
      setProbabilities([]);
    } catch (e) {
      console.log('[VarietyRecognition] camera error', e);
    }
  };

  const handlePickFromGallery = async () => {
    try {
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) {
        Alert.alert(
          lang === 'zh' ? '需要相簿權限' : 'Library Permission Required',
          lang === 'zh' ? '請在設定中允許相簿存取。' : 'Please allow photo library access.',
        );
        return;
      }
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.85,
        allowsEditing: false,
      });
      if (result.canceled || !result.assets?.[0]) return;
      const asset = result.assets[0];
      if (!validateImageAsset(asset)) return;
      setImageUri(asset.uri);
      setImageMime(asset.mimeType ?? 'image/jpeg');
      setTopVariety(null);
      setConfidence(null);
      setProbabilities([]);
    } catch (e) {
      console.log('[VarietyRecognition] gallery error', e);
    }
  };

  const parsePredictions = (data: PredictionResponse): {
    top: { zh: string; en: string } | null;
    conf: number | null;
    probs: PredictionItem[];
  } => {
    let probs: PredictionItem[] = [];
    if (Array.isArray(data.probabilities)) {
      probs = data.probabilities.map((p) => ({
        label: p.label,
        labelEn: p.labelEn,
        score: typeof p.score === 'number' ? p.score : 0,
      }));
    } else if (data.probabilities && typeof data.probabilities === 'object') {
      probs = Object.entries(data.probabilities).map(([k, v]) => ({
        label: k,
        score: typeof v === 'number' ? v : 0,
      }));
    }
    probs.sort((a, b) => b.score - a.score);

    let top: { zh: string; en: string } | null = null;
    let conf: number | null =
      typeof data.confidence === 'number' ? data.confidence : null;

    if (data.variety) {
      top = {
        zh: data.variety,
        en: data.variety_en ?? normalizeVarietyName(data.variety, 'en'),
      };
    } else if (probs.length > 0) {
      const first = probs[0];
      top = {
        zh: normalizeVarietyName(first.label, 'zh'),
        en: first.labelEn ?? normalizeVarietyName(first.label, 'en'),
      };
      if (conf == null) conf = first.score;
    }

    return { top, conf, probs };
  };

  const handlePredict = async () => {
    if (!imageUri) {
      Alert.alert(
        lang === 'zh' ? '請先選擇影像' : 'Select an Image',
        lang === 'zh' ? '請先拍照或從相簿選擇鳳梨照片。' : 'Please take or pick a pineapple photo first.',
      );
      return;
    }
    const latest = await getApiBaseUrl();
    if (latest) setServerUrl(latest);
    const url = (latest || serverUrl).trim().replace(/\/+$/, '');
    if (!url || !/^https?:\/\//i.test(url)) {
      Alert.alert(
        lang === 'zh' ? '伺服器位址無效' : 'Invalid Server URL',
        lang === 'zh' ? '請在首頁右上方設定伺服器位址。' : 'Please set the server URL from the home top-right.',
      );
      return;
    }
    console.log('[VarietyRecognition] predict using URL:', url);

    setLoading(true);
    setTopVariety(null);
    setConfidence(null);
    setProbabilities([]);
    
    try {
      const data = await apiPredictVariety(imageUri);
      console.log('[VarietyRecognition] raw response:', JSON.stringify(data, null, 2));

      const predClass = data.pred_class ?? '';
      const predZhName =
        data.pred_zh_name ??
        (lang === 'zh' ? '未偵測到鳳梨' : 'No pineapple detected');


      const confValue = typeof data.confidence === 'number' ? data.confidence : 0;

      const isPineapple = data.is_pineapple !== false;
      const message = data.message ?? '';

      const rawProbs = Array.isArray(data.all_probs) ? data.all_probs : [];

      const probs = rawProbs
        .map((p: any) => ({
          label: p.zh_name ?? p.class ?? '',
          labelEn: p.class ?? '',
          score: Number(p.probability ?? p.score ?? 0),
        }))
        .sort((a, b) => b.score - a.score);

      if (!isPineapple || !predClass) {
        setTopVariety({
          zh: predZhName,
          en: 'No pineapple detected',
        });

        setConfidence(0);
        setProbabilities(
          probs.map((p: any) => ({
            label: p.zh_name ?? p.class ?? '',
            labelEn: p.class ?? '',
            score: Number(p.probability ?? 0),
          }))
        );
        setLastRecord({
          variety_detection_id: `variety_${Date.now()}`,
          device_id: null,
          user_id: null,
          image_path: imageUri,
          pred_class: predClass || 'no_pineapple',
          pred_zh_name: predZhName,
          confidence: 0,
          low_confidence: true,
          all_probs_json: JSON.stringify([]),
          created_at: new Date().toISOString(),
        });

        setResultModalVisible(true);
        return;
      }

      setTopVariety({
        zh: predZhName,
        en: normalizeVarietyName(predClass, 'en'),
      });

      setConfidence(confValue);
      setProbabilities(probs);

      const allProbsObj = probs.reduce<Record<string, number>>((acc, p) => {
        acc[p.labelEn || p.label] = p.score;
        return acc;
      }, {});

      const record: VarietyDetectionRecord = {
        variety_detection_id: `variety_${Date.now()}_${Math.random().toString(36).slice(2)}`,
        device_id: null,
        user_id: null,
        image_path: imageUri,
        pred_class: predClass,
        pred_zh_name: predZhName,
        confidence: confValue,
        low_confidence: data.low_confidence ?? confValue < LOW_CONFIDENCE_THRESHOLD,
        all_probs_json: JSON.stringify(allProbsObj),
        created_at: new Date().toISOString(),
      };

      setLastRecord(record);
      console.log('[VarietyRecognition] detection record:', record);
      setResultModalVisible(true);
    }catch (e) {
      console.log('[VarietyRecognition] predict error', e);
      Alert.alert(
        lang === 'zh' ? '連線異常' : 'Connection Error',
        lang === 'zh'
          ? '無法連線到伺服器，請確認 ngrok 網址是否正確、RPI 是否在線。'
          : 'Cannot reach the server. Please check your ngrok URL and that the RPI is online.',
      );
    } finally {
      setLoading(false);
    }
  };

  const isLowConfidence =
    confidence != null && confidence < LOW_CONFIDENCE_THRESHOLD;

  return (
    <View style={styles.container}>
      <View style={[styles.headerWrap, { height: insets.top + 110 }]}>
        <LinearGradient
          colors={[Palette.yellow, Palette.orange]}
          style={styles.headerGradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        />
      </View>

      <View style={[styles.headerRow, { top: insets.top + 12 }]}>
        <TouchableOpacity
          style={styles.backBtn}
          onPress={() => router.back()}
          activeOpacity={0.8}
          testID="btn-back"
        >
          <ArrowLeft size={22} color={Palette.white} strokeWidth={2.4} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>
          {lang === 'zh' ? '品種影像辨識' : 'Variety Image Recognition'}
        </Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[
          styles.scrollContent,
          { paddingTop: insets.top + 90, paddingBottom: insets.bottom + 32 },
        ]}
        showsVerticalScrollIndicator={false}
      >
        {/* Preview */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>
            {lang === 'zh' ? '原始照片' : 'Source Photo'}
          </Text>
          <View style={styles.preview}>
            {imageUri ? (
              <Image source={{ uri: imageUri }} style={styles.previewImage} resizeMode="cover" />
            ) : (
              <View style={styles.previewPlaceholder}>
                <ImageIcon size={36} color={Palette.textMuted} strokeWidth={1.6} />
                <Text style={styles.previewHint}>
                  {lang === 'zh' ? '尚未選擇影像' : 'No image selected'}
                </Text>
              </View>
            )}
          </View>

          <View style={styles.actionRow}>
            <TouchableOpacity
              style={styles.actionBtn}
              onPress={handleTakePhoto}
              activeOpacity={0.85}
              testID="btn-camera"
            >
              <Camera size={18} color={Palette.white} strokeWidth={2.2} />
              <Text style={styles.actionBtnText}>
                {lang === 'zh' ? '拍照辨識' : 'Take Photo'}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionBtn, styles.actionBtnSecondary]}
              onPress={handlePickFromGallery}
              activeOpacity={0.85}
              testID="btn-gallery"
            >
              <ImageIcon size={18} color={Palette.oliveDark} strokeWidth={2.2} />
              <Text style={[styles.actionBtnText, { color: Palette.oliveDark }]}>
                {lang === 'zh' ? '相簿上傳' : 'From Gallery'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Settings (collapsible) */}
        <View style={styles.card}>
          <TouchableOpacity
            style={styles.collapseHeader}
            onPress={() => setSettingsExpanded((v) => !v)}
            activeOpacity={0.7}
            testID="btn-toggle-settings"
          >
            <View style={styles.iconLabelRow}>
              <SettingsIcon size={16} color={Palette.olive} strokeWidth={2} />
              <Text style={styles.collapseTitle}>
                {lang === 'zh' ? '系統設定與資訊' : 'System Settings & Info'}
              </Text>
            </View>
            {settingsExpanded ? (
              <ChevronUp size={18} color={Palette.olive} strokeWidth={2.2} />
            ) : (
              <ChevronDown size={18} color={Palette.olive} strokeWidth={2.2} />
            )}
          </TouchableOpacity>

          {settingsExpanded && (
            <View style={styles.collapseBody}>
              <View style={styles.rowBetween}>
                <View style={styles.iconLabelRow}>
                  <CalendarDays size={16} color={Palette.olive} strokeWidth={2} />
                  <Text style={styles.metaLabel}>
                    {lang === 'zh' ? '今日日期' : 'Today'}
                  </Text>
                </View>
                <Text style={styles.metaValue}>{formatDate(today, lang)}</Text>
              </View>

              <View style={styles.divider} />

              <View style={styles.rowBetween}>
                <View style={styles.iconLabelRow}>
                  <Server size={16} color={Palette.olive} strokeWidth={2} />
                  <Text style={styles.metaLabel}>
                    {lang === 'zh' ? '伺服器位址' : 'Server URL'}
                  </Text>
                </View>
              </View>
              <Text style={[styles.metaValue, { marginTop: 6 }]} numberOfLines={1}>
                {serverUrl}
              </Text>
              <Text style={styles.hintText}>
                {lang === 'zh'
                  ? '請到首頁右上方「伺服器」點選修改。此設定與感測鳳梨功能共用。'
                  : 'Tap the Server button on the home top-right to change it. Shared with the sensor scan feature.'}
              </Text>
            </View>
          )}
        </View>

        {/* Predict button */}
        <TouchableOpacity
          style={styles.predictBtn}
          onPress={handlePredict}
          activeOpacity={0.9}
          disabled={loading}
          testID="btn-predict"
        >
          <LinearGradient
            colors={loading ? ['#BDBDBD', '#9E9E9E'] : [Palette.yellow, Palette.orange]}
            style={styles.predictGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
          >
            {loading ? (
              <ActivityIndicator color={Palette.white} />
            ) : (
              <Text style={styles.predictText}>
                {lang === 'zh' ? '開始辨識' : 'Recognize'}
              </Text>
            )}
          </LinearGradient>
        </TouchableOpacity>

      </ScrollView>

      {/* Result Modal (popup) */}
      <Modal
        visible={resultModalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setResultModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                {lang === 'zh' ? '辨識結果' : 'Recognition Result'}
              </Text>
              <TouchableOpacity
                style={styles.modalCloseBtn}
                onPress={() => setResultModalVisible(false)}
                activeOpacity={0.7}
                testID="btn-close-modal"
              >
                <X size={20} color={Palette.oliveDark} strokeWidth={2.4} />
              </TouchableOpacity>
            </View>

            <ScrollView
              style={{ maxHeight: 520 }}
              contentContainerStyle={{ paddingBottom: 8 }}
              showsVerticalScrollIndicator={false}
            >
              {imageUri && (
                <View style={styles.modalImageWrap}>
                  <Image
                    source={{ uri: imageUri }}
                    style={styles.modalImage}
                    resizeMode="cover"
                  />
                </View>
              )}

              {topVariety && lastRecord && (
                <View style={styles.resultBlock}>
                  <Text style={styles.resultZh}>
                    {lang === 'zh'
                      ? lastRecord.pred_zh_name
                      : normalizeVarietyName(lastRecord.pred_class, 'en')}
                  </Text>

                  <Text style={styles.resultEn}>
                    {lang === 'zh'
                      ? normalizeVarietyName(lastRecord.pred_class, 'en')
                      : lastRecord.pred_zh_name}
                  </Text>
                </View>
              )}

              {lastRecord?.pred_class ? (
                <View style={styles.codePill}>
                  <Text style={styles.codePillText}>
                    {lang === 'zh' ? '類別代碼' : 'Class'}: {lastRecord.pred_class}
                  </Text>
                </View>
              ) : null}

              {confidence != null && (
                <View
                  style={[
                    styles.confidencePill,
                    {
                      backgroundColor: isLowConfidence ? '#FDECEA' : '#E8F5E9',
                      marginTop: 12,
                    },
                  ]}
                >
                  {isLowConfidence ? (
                    <AlertTriangle size={16} color={Palette.red} strokeWidth={2.2} />
                  ) : (
                    <CheckCircle2 size={16} color={Palette.green} strokeWidth={2.2} />
                  )}
                  <Text
                    style={[
                      styles.confidenceText,
                      { color: isLowConfidence ? Palette.red : Palette.green },
                    ]}
                  >
                    {lang === 'zh' ? '信心分數' : 'Confidence'}:{' '}
                    {(confidence * 100).toFixed(1)}%
                  </Text>
                </View>
              )}

              {isLowConfidence && (
                <View style={styles.lowConfBanner}>
                  <AlertTriangle size={16} color={Palette.red} strokeWidth={2.2} />
                  <Text style={styles.lowConfBannerText}>
                    {lang === 'zh'
                      ? '信心度偏低，建議重新拍攝（光線、角度、清晰度）。'
                      : 'Low confidence. Please retake with better lighting and angle.'}
                  </Text>
                </View>
              )}

              {probabilities.length > 0 && (
                <>
                  <Text style={[styles.sectionTitle, { marginTop: 18 }]}>
                    {lang === 'zh' ? '四類機率' : 'Class Probabilities'}
                  </Text>
                  <View style={{ gap: 10 }}>
                    {probabilities.slice(0, 4).map((p, idx) => {
                      const pct = Math.max(0, Math.min(1, p.score)) * 100;
                      const display =
                        lang === 'zh'
                          ? p.label
                          : normalizeVarietyName(p.labelEn ?? p.label, 'en');
                      return (
                        <View key={`${p.label}-${idx}`}>
                          <View style={styles.rowBetween}>
                            <Text style={styles.probLabel}>{display}</Text>
                            <Text style={styles.probValue}>{pct.toFixed(1)}%</Text>
                          </View>
                          <View style={styles.barTrack}>
                            <LinearGradient
                              colors={[Palette.yellow, Palette.orange]}
                              start={{ x: 0, y: 0 }}
                              end={{ x: 1, y: 0 }}
                              style={[styles.barFill, { width: `${pct}%` }]}
                            />
                          </View>
                        </View>
                      );
                    })}
                  </View>
                </>
              )}
            </ScrollView>

            <TouchableOpacity
              style={styles.modalConfirmBtn}
              onPress={() => setResultModalVisible(false)}
              activeOpacity={0.9}
              testID="btn-modal-confirm"
            >
              <LinearGradient
                colors={[Palette.yellow, Palette.orange]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.modalConfirmGradient}
              >
                <Text style={styles.modalConfirmText}>
                  {lang === 'zh' ? '完成' : 'Done'}
                </Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Palette.cream },
  headerWrap: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    overflow: 'hidden',
  },
  headerGradient: {
    flex: 1,
    borderBottomLeftRadius: 28,
    borderBottomRightRadius: 28,
  },
  headerRow: {
    position: 'absolute',
    left: 16,
    right: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    zIndex: 5,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.25)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    color: Palette.white,
    fontSize: 17,
    fontWeight: '800' as const,
    letterSpacing: 0.4,
  },
  scroll: { flex: 1 },
  scrollContent: { paddingHorizontal: 16, gap: 14 },
  card: {
    backgroundColor: Palette.white,
    borderRadius: 20,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700' as const,
    color: Palette.oliveDark,
    marginBottom: 12,
    letterSpacing: 0.3,
  },
  preview: {
    width: '100%',
    aspectRatio: 4 / 3,
    backgroundColor: Palette.creamSoft,
    borderRadius: 14,
    overflow: 'hidden',
    alignItems: 'center',
    justifyContent: 'center',
  },
  previewImage: { width: '100%', height: '100%' },
  previewPlaceholder: { alignItems: 'center', gap: 8 },
  previewHint: { color: Palette.textMuted, fontSize: 13 },
  actionRow: { flexDirection: 'row', gap: 10, marginTop: 12 },
  actionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Palette.olive,
    paddingVertical: 12,
    borderRadius: 14,
  },
  actionBtnSecondary: {
    backgroundColor: Palette.creamSoft,
    borderWidth: 1,
    borderColor: Palette.border,
  },
  actionBtnText: {
    color: Palette.white,
    fontWeight: '700' as const,
    fontSize: 14,
  },
  rowBetween: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  iconLabelRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  metaLabel: {
    fontSize: 13,
    color: Palette.textMuted,
    fontWeight: '600' as const,
  },
  metaValue: {
    fontSize: 14,
    color: Palette.oliveDark,
    fontWeight: '700' as const,
  },
  divider: {
    height: 1,
    backgroundColor: Palette.border,
    marginVertical: 12,
  },
  input: {
    marginTop: 8,
    backgroundColor: Palette.creamSoft,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: Platform.OS === 'ios' ? 12 : 8,
    fontSize: 14,
    color: Palette.oliveDark,
    borderWidth: 1,
    borderColor: Palette.border,
  },
  predictBtn: {
    borderRadius: 24,
    overflow: 'hidden',
    shadowColor: Palette.orange,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 6,
  },
  predictGradient: {
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  predictText: {
    color: Palette.white,
    fontSize: 16,
    fontWeight: '800' as const,
    letterSpacing: 0.6,
  },
  resultBlock: { alignItems: 'center', marginBottom: 12 },
  resultZh: {
    fontSize: 24,
    fontWeight: '800' as const,
    color: Palette.oliveDark,
  },
  resultEn: {
    marginTop: 4,
    fontSize: 14,
    color: Palette.textMuted,
    fontWeight: '600' as const,
  },
  confidencePill: {
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
  },
  confidenceText: { fontSize: 13, fontWeight: '700' as const },
  lowConfHint: {
    marginTop: 10,
    fontSize: 12,
    color: Palette.red,
    textAlign: 'center',
    lineHeight: 18,
  },
  probLabel: {
    fontSize: 13,
    color: Palette.oliveDark,
    fontWeight: '600' as const,
  },
  probValue: {
    fontSize: 13,
    color: Palette.textMuted,
    fontWeight: '700' as const,
  },
  barTrack: {
    marginTop: 4,
    height: 8,
    borderRadius: 4,
    backgroundColor: Palette.creamSoft,
    overflow: 'hidden',
  },
  barFill: { height: '100%', borderRadius: 4 },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  modalCard: {
    width: '100%',
    maxWidth: 440,
    backgroundColor: Palette.white,
    borderRadius: 22,
    padding: 18,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.18,
    shadowRadius: 24,
    elevation: 10,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: '800' as const,
    color: Palette.oliveDark,
    letterSpacing: 0.3,
  },
  modalCloseBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Palette.creamSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalImageWrap: {
    width: '100%',
    aspectRatio: 4 / 3,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: Palette.creamSoft,
    marginBottom: 14,
  },
  modalImage: { width: '100%', height: '100%' },
  codePill: {
    alignSelf: 'center',
    marginTop: 4,
    backgroundColor: Palette.creamSoft,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: Palette.border,
  },
  codePillText: {
    fontSize: 12,
    color: Palette.oliveDark,
    fontWeight: '700' as const,
    letterSpacing: 0.3,
  },
  lowConfBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FFF3CD',
    borderRadius: 12,
    padding: 12,
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#FFCA28',
  },
  lowConfBannerText: {
    flex: 1,
    fontSize: 12.5,
    color: '#856404',
    fontWeight: '600' as const,
    lineHeight: 18,
  },
  modalConfirmBtn: {
    marginTop: 14,
    borderRadius: 18,
    overflow: 'hidden',
  },
  modalConfirmGradient: {
    paddingVertical: 13,
    alignItems: 'center',
  },
  modalConfirmText: {
    color: Palette.white,
    fontWeight: '800' as const,
    fontSize: 15,
    letterSpacing: 0.5,
  },
  collapseHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  collapseTitle: {
    fontSize: 14,
    fontWeight: '700' as const,
    color: Palette.oliveDark,
    letterSpacing: 0.3,
  },
  collapseBody: {
    marginTop: 12,
  },
  hintText: {
    marginTop: 8,
    fontSize: 11.5,
    color: Palette.textMuted,
    lineHeight: 16,
  },
});
