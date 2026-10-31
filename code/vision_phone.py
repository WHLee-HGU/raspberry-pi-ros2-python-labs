"""호스트 .venv-yolo: 스마트폰 감지를 PHONE/CLEAR/UNKNOWN으로 전달합니다."""
import argparse
import math
from pathlib import Path
import time
from common import write_sample
from vision_policy import StablePhone


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default='picamera2')
    parser.add_argument('--camera-index', type=int)
    parser.add_argument('--model', type=Path, default=Path(__file__).resolve().parents[2]/'models/yolo11n_ncnn_model')
    parser.add_argument('--imgsz', type=int, default=320)
    parser.add_argument('--conf', type=float, default=.5)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--duration', type=float, default=0)
    parser.add_argument('--mock', action='store_true')
    parser.add_argument('--mock-state', choices=['CYCLE', 'PHONE', 'CLEAR', 'UNKNOWN'], default='CYCLE')
    args = parser.parse_args()
    if not 0 < args.conf <= 1:
        parser.error('--conf는 0보다 크고 1 이하입니다.')
    if not math.isfinite(args.duration) or args.duration < 0:
        parser.error('--duration은 0 이상인 유한한 초 값입니다.')
    if args.camera_index is not None and args.camera_index < 0:
        parser.error('--camera-index는 0 이상입니다.')
    if args.imgsz < 32:
        parser.error('--imgsz는 32 이상입니다.')
    write_sample('phone', {'state': 'UNKNOWN'})
    start = time.monotonic()
    previous = None
    camera = None
    processed = 0
    try:
        if not args.mock:
            if not args.model.exists():
                raise RuntimeError('준비된 YOLO 모델이 없습니다: '+str(args.model))
            import cv2
            from ultralytics import YOLO
            from vision_camera import CameraFrames
            model = YOLO(str(args.model), task='detect')
            names = model.names
            entries = names.items() if isinstance(names, dict) else enumerate(names)
            phone_ids = [int(index) for index, label in entries if str(label).replace('_', ' ').strip().casefold() == 'cell phone']
            if not phone_ids:
                raise RuntimeError('이 모델에 cell phone 클래스가 없습니다. 수업용 COCO 모델을 사용하세요.')
            camera = CameraFrames(args.source, args.camera_index)
        stable = StablePhone(frames=2, clear_seconds=.5)
        start = time.monotonic()
        while args.duration <= 0 or time.monotonic()-start < args.duration:
            if args.mock:
                raw = args.mock_state
                if raw == 'CYCLE':
                    raw = ['PHONE', 'CLEAR', 'UNKNOWN'][int((time.monotonic()-start)/2) % 3]
                present = True if raw == 'PHONE' else False if raw == 'CLEAR' else None
                confidence = 1.0 if present else 0.0
                source_time = time.time()
                frame = None
            else:
                ok, frame = camera.read()
                source_time = time.time()
                if not ok:
                    raise RuntimeError('카메라 프레임을 받지 못했습니다.')
                result = model.predict(frame, imgsz=args.imgsz, conf=args.conf,
                                       classes=phone_ids, device='cpu', verbose=False, save=False)[0]
                confidences = result.boxes.conf.tolist() if result.boxes is not None else []
                confidence = max(confidences, default=0.0)
                present = confidence >= args.conf
            processed += 1
            state = stable.update(present, time.monotonic())
            write_sample('phone', {'state': state, 'phone_confidence': confidence}, source_time=source_time)
            if state != previous:
                print(('MOCK ' if args.mock else '')+'phone='+state, flush=True)
                previous = state
            if not args.mock and not args.headless:
                display = result.plot()
                cv2.putText(display, f'{state} confidence={confidence:.2f}', (10, 35), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 255, 0), 2)
                cv2.imshow('Phone detector - Q to quit', display)
                if cv2.waitKey(1) & 0xff == ord('q'):
                    break
            if args.mock:
                time.sleep(.1)
    except KeyboardInterrupt:
        pass
    finally:
        write_sample('phone', {'state': 'UNKNOWN'})
        if camera is not None:
            camera.close()
        if not args.mock and not args.headless:
            import cv2
            cv2.destroyAllWindows()
        print(f'processed_frames={processed} mock={args.mock}', flush=True)


if __name__ == '__main__':
    main()
