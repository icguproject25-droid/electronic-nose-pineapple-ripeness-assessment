import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Easing, Dimensions, BackHandler, Platform, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Colors } from '@/constants/colors';
import { useLanguage } from '@/contexts/LanguageContext';
import { useSensor } from '@/contexts/SensorContext';
import { PineappleIcon } from '@/components/PineappleIcon';
import { PineappleTriviaCard } from '@/components/PineappleTriviaCard';
import { useTrivia } from '@/contexts/TriviaContext';
import * as Speech from 'expo-speech';

const { width } = Dimensions.get('window');
const CIRCLE_SIZE = width * 0.7;

export default function ProcessingScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { t, language } = useLanguage();
  const { startScan } = useSensor();

  const scanFinishedRef = useRef(false);
  const { continueSession, stopSession } = useTrivia();
  const continueSessionRef = useRef(continueSession);
  const stopSessionRef = useRef(stopSession);
  const startScanRef = useRef(startScan);
  continueSessionRef.current = continueSession;
  stopSessionRef.current = stopSession;
  startScanRef.current = startScan;

  const pulseAnim = useRef(new Animated.Value(1)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;
  const bounceAnim = useRef(new Animated.Value(0)).current;
  const glowAnim = useRef(new Animated.Value(0.35)).current;

  useEffect(() => {
    const pulseLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.08,
          duration: 900,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 900,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    );

    const rotateLoop = Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 3400,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    );

    const bounceLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(bounceAnim, {
          toValue: -12,
          duration: 800,
          easing: Easing.out(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.timing(bounceAnim, {
          toValue: 0,
          duration: 800,
          easing: Easing.in(Easing.quad),
          useNativeDriver: true,
        }),
      ])
    );

    const glowLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: 1,
          duration: 1200,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: 0.35,
          duration: 1200,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    );

    const progressLoop = Animated.loop(
      Animated.timing(progressAnim, {
        toValue: 1,
        duration: 2200,
        easing: Easing.linear,
        useNativeDriver: false,
      }),
      { resetBeforeIteration: true }
    );

    pulseLoop.start();
    rotateLoop.start();
    bounceLoop.start();
    glowLoop.start();
    progressLoop.start();

    let isCancelled = false;
    console.log('[Processing] Starting scan');
    continueSessionRef.current();

    startScanRef.current()
      .then(() => {
        if (isCancelled) return;
        console.log('[Processing] Scan complete, navigating to result');
        scanFinishedRef.current = true;
        stopSessionRef.current();

        // 停止目前可能還在播放的語音
        Speech.stop();

        // 播放完成提示
        Speech.speak(
          language === 'zh'
            ? '感測完畢，請確認結果'
            : 'Sensing complete. Please check the result.',
          {
            language: language === 'zh' ? 'zh-TW' : 'en-US',
            pitch: 1,
            rate: 0.95,
          }
        );

        // 等語音開始後再跳到結果頁
        setTimeout(() => {
          if (!isCancelled) {
            router.replace('/result' as any);
          }
        }, 1000);
      })
      .catch((error: unknown) => {
        if (isCancelled) return;
        scanFinishedRef.current = true;
        stopSessionRef.current();
        const msg = error instanceof Error ? error.message : String(error);
        console.log('[Processing] startScan error:', msg);
        if (msg === 'NO_AIR_BASE') {
          Alert.alert(
            t('noAirBaseTitle'),
            t('noAirBaseMessage'),
            [{ text: t('confirm'), onPress: () => router.back() }],
            { cancelable: false }
          );
        } else {
          Alert.alert(
            '感測失敗',
            msg || '請確認樹莓派連線後重試',
            [{ text: '確定', onPress: () => router.back() }],
            { cancelable: false }
          );
        }
      });

    let backSub: { remove: () => void } | null = null;
    if (Platform.OS === 'android') {
      backSub = BackHandler.addEventListener('hardwareBackPress', () => {
        console.log('[Processing] Back press blocked during scan');
        return true;
      });
    }

    return () => {
      isCancelled = true;
      stopSessionRef.current();
      if (backSub) backSub.remove();
      pulseLoop.stop();
      rotateLoop.stop();
      bounceLoop.stop();
      glowLoop.stop();
      progressLoop.stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const rotation = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const progressWidth = progressAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['12%', '100%'],
  });

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#111827', '#18212F', '#253549']}
        style={StyleSheet.absoluteFill}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />

      <View style={[styles.content, { paddingTop: insets.top + 40, paddingBottom: insets.bottom + 40 }]}> 
        <Text style={styles.title}>{t('processing')}</Text>
        <Text style={styles.subtitle}>{t('processingSubtitle')}</Text>

        <View style={styles.animationContainer}>
          <Animated.View style={[styles.glowHalo, { opacity: glowAnim }]} />
          <Animated.View
            style={[
              styles.outerCircle,
              {
                transform: [{ rotate: rotation }],
              },
            ]}
          >
            {Array.from({ length: 12 }).map((_, index) => (
              <View
                key={index}
                style={[
                  styles.dot,
                  {
                    transform: [
                      { rotate: `${index * 30}deg` },
                      { translateY: -CIRCLE_SIZE / 2 + 15 },
                    ],
                    opacity: 0.25 + (index / 12) * 0.7,
                  },
                ]}
              />
            ))}
          </Animated.View>

          <Animated.View
            style={[
              styles.innerCircle,
              {
                transform: [
                  { scale: pulseAnim },
                  { translateY: bounceAnim },
                ],
              },
            ]}
          >
            <LinearGradient
              colors={['#FFFBE8', '#FFE59A']}
              style={styles.innerCircleGradient}
            >
              <PineappleIcon size={90} />
            </LinearGradient>
          </Animated.View>
        </View>

        <View style={styles.triviaCardContainer}>
          <PineappleTriviaCard active={!scanFinishedRef.current} variant="dark" />
        </View>

        <View style={styles.progressCard}>
          <Text style={styles.progressLabel}>{t('aiAnalyzing')}</Text>
          <View style={styles.progressBarBg}>
            <Animated.View style={[styles.progressBarFill, { width: progressWidth }]}>
              <LinearGradient
                colors={['#5DD39E', '#53B3CB']}
                style={StyleSheet.absoluteFill}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
              />
            </Animated.View>
          </View>
        </View>
      </View>


    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: '800' as const,
    color: Colors.white,
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 14,
    lineHeight: 21,
    fontWeight: '500' as const,
    color: 'rgba(255,255,255,0.75)',
    textAlign: 'center',
    maxWidth: 280,
    marginBottom: 34,
  },
  animationContainer: {
    width: CIRCLE_SIZE,
    height: CIRCLE_SIZE,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 34,
  },
  glowHalo: {
    position: 'absolute',
    width: CIRCLE_SIZE * 0.62,
    height: CIRCLE_SIZE * 0.62,
    borderRadius: (CIRCLE_SIZE * 0.62) / 2,
    backgroundColor: 'rgba(83, 179, 203, 0.22)',
  },
  outerCircle: {
    position: 'absolute',
    width: CIRCLE_SIZE,
    height: CIRCLE_SIZE,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dot: {
    position: 'absolute',
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: Colors.white,
  },
  innerCircle: {
    width: CIRCLE_SIZE * 0.6,
    height: CIRCLE_SIZE * 0.6,
    borderRadius: CIRCLE_SIZE * 0.3,
    overflow: 'hidden',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25,
    shadowRadius: 16,
    elevation: 12,
  },
  innerCircleGradient: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressCard: {
    width: '100%',
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 20,
    paddingVertical: 18,
    paddingHorizontal: 18,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  progressLabel: {
    fontSize: 13,
    fontWeight: '700' as const,
    color: 'rgba(255,255,255,0.86)',
    marginBottom: 12,
    textAlign: 'center',
  },
  progressBarBg: {
    height: 10,
    backgroundColor: 'rgba(255,255,255,0.12)',
    borderRadius: 999,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 999,
    overflow: 'hidden',
  },
  triviaCardContainer: {
    width: '100%',
    marginBottom: 16,
  },
});
