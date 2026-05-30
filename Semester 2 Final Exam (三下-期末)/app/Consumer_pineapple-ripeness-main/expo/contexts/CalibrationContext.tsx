import createContextHook from '@nkzw/create-context-hook';
import { useCallback, useEffect, useRef, useState } from 'react';
import { apiStartCalibration, apiGetStatus } from '@/services/api';

const CALIBRATION_DURATION = 30;

export const [CalibrationProvider, useCalibration] = createContextHook(() => {
  const [isCalibrating, setIsCalibrating] = useState<boolean>(false);
  const [secondsLeft, setSecondsLeft] = useState<number>(CALIBRATION_DURATION);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const finish = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setIsCalibrating(false);
    setSecondsLeft(CALIBRATION_DURATION);
  }, []);

  const start = useCallback(async () => {
    if (intervalRef.current) return;

    let rpiAvailable = true;
    try {
      await apiStartCalibration();
    } catch (error) {
      rpiAvailable = false;
      console.warn(
        '[Calibration] 無法連線至樹莓派，改用本地倒數模式:',
        error instanceof Error ? error.message : String(error)
      );
    }

    console.log('[Calibration] Start', rpiAvailable ? '(RPi)' : '(local fallback)');
    setIsCalibrating(true);
    setSecondsLeft(CALIBRATION_DURATION);

    intervalRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          console.log('[Calibration] Finished');
          setIsCalibrating(false);
          return CALIBRATION_DURATION;
        }
        return prev - 1;
      });
    }, 1000);

    if (rpiAvailable) {
      pollRef.current = setInterval(async () => {
        try {
          const status = await apiGetStatus();
          if (status.status === 'done') {
            console.log('[Calibration] Done from RPi');
            finish();
          } else if (status.status === 'error') {
            console.error('[Calibration] RPi error:', status.error);
            finish();
          }
        } catch {
          /* 短暫網路中斷，繼續輪詢 */
        }
      }, 2000);
    }
  }, [finish]);

  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    isCalibrating,
    secondsLeft,
    duration: CALIBRATION_DURATION,
    start,
  };
});
