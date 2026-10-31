"""호스트 .venv-mp: 손 영상을 판정해 ROS publisher가 읽을 작은 JSON을 기록합니다."""
import argparse
import math
from pathlib import Path
import time
from common import write_sample
from vision_policy import classify_gesture, StableGesture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default='picamera2')
    parser.add_argument('--camera-index', type=int)
    parser.add_argument('--model', type=Path, default=Path(__file__).resolve().parents[2]/'models/gesture_recognizer.task')
    parser.add_argument('--min-score', type=float, default=.6)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--duration', type=float, default=0, help='0이면 계속 실행')
    parser.add_argument('--mock', action='store_true', help='카메라 대신 명시적인 모의 상태 사용')
    parser.add_argument('--mock-state', choices=['CYCLE', 'FIST', 'OPEN', 'UNKNOWN'], default='CYCLE')
    args = parser.parse_args()
    if not math.isfinite(args.duration) or args.duration < 0:
        parser.error('--duration은 0 이상인 유한한 초 값입니다.')
    if args.camera_index is not None and args.camera_index < 0:
        parser.error('--camera-index는 0 이상입니다.')
    if not 0 < args.min_score <= 1:
        parser.error('--min-score는 0보다 크고 1 이하입니다.')
    write_sample('hand', {'gesture': 'UNKNOWN'})
    start = time.monotonic()
    previous = None
    camera = detector = None
    processed = 0
    try:
        if not args.mock:
            if not args.model.is_file():
                raise RuntimeError('준비된 gesture_recognizer.task 모델이 없습니다: '+str(args.model))
            import cv2
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            from vision_camera import CameraFrames
            options = vision.GestureRecognizerOptions(
                base_options=python.BaseOptions(model_asset_path=str(args.model)),
                running_mode=vision.RunningMode.VIDEO, num_hands=2)
            detector = vision.GestureRecognizer.create_from_options(options)
            camera = CameraFrames(args.source, args.camera_index)
        stable = StableGesture(frames=3)
        last_ms = -1
        start = time.monotonic()  # 모델 로딩 시간과 실제 실행 시간을 구분합니다.
        while args.duration <= 0 or time.monotonic()-start < args.duration:
            if args.mock:
                raw = args.mock_state
                if raw == 'CYCLE':
                    raw = ['FIST', 'OPEN', 'UNKNOWN'][int((time.monotonic()-start)/2) % 3]
                source_time = time.time()
                frame = None
                hands = 1 if raw != 'UNKNOWN' else 0
            else:
                ok, frame = camera.read()
                source_time = time.time()  # 추론 전에 기록해 처리 지연도 검사합니다.
                if not ok:
                    raise RuntimeError('카메라 프레임을 받지 못했습니다.')
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                last_ms = max(last_ms+1, time.monotonic_ns()//1_000_000)
                result = detector.recognize_for_video(
                    mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), last_ms)
                hands = len(result.hand_landmarks)
                raw = classify_gesture(result.gestures, hands, args.min_score)
            processed += 1
            gesture = stable.update(raw)
            write_sample('hand', {'gesture': gesture, 'raw': raw, 'hands': hands}, source_time=source_time)
            if gesture != previous:
                print(('MOCK ' if args.mock else '')+'hand='+gesture, flush=True)
                previous = gesture
            if not args.mock and not args.headless:
                cv2.putText(frame, f'{gesture} hands={hands}', (10, 35), cv2.FONT_HERSHEY_SIMPLEX, .8, (0, 255, 0), 2)
                cv2.imshow('Hand gesture - Q to quit', frame)
                if cv2.waitKey(1) & 0xff == ord('q'):
                    break
            if args.mock:
                time.sleep(.1)
    except KeyboardInterrupt:
        pass
    finally:
        write_sample('hand', {'gesture': 'UNKNOWN'})
        if camera is not None:
            camera.close()
        if detector is not None:
            detector.close()
        if not args.mock and not args.headless:
            import cv2
            cv2.destroyAllWindows()
        print(f'processed_frames={processed} mock={args.mock}', flush=True)


if __name__ == '__main__':
    main()
