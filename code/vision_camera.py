"""Picamera2/OpenCV 공통 카메라. Pi 5에서는 물리 CAM/DISP0을 찾아 선택합니다."""
from pathlib import Path
import time


def _dt_text(path):
    try:
        return path.read_bytes().decode('utf-8').rstrip('\0')
    except OSError:
        return ''


def cam0_index(camera_infos, base=Path('/sys/firmware/devicetree/base')):
    """소프트웨어 카메라 번호 0과 물리 CAM0이 항상 같지는 않습니다."""
    if not _dt_text(base/'model').startswith('Raspberry Pi 5'):
        raise RuntimeError('CAM0 자동 선택은 Raspberry Pi 5용입니다. --camera-index를 명시하세요.')
    parent = ''
    for relative in ('__symbols__/i2c_csi_dsi0', 'aliases/i2c10'):
        value = _dt_text(base/relative)
        if value.startswith('/'):
            parent = value.rstrip('/')
            break
    matches = []
    for item in camera_infos:
        camera_id = str(item.get('Id', ''))
        if camera_id.startswith('/base/'):
            camera_id = camera_id[len('/base'):]
        if parent and camera_id.startswith(parent+'/'):
            matches.append(int(item['Num']))
    if len(matches) != 1:
        raise RuntimeError('물리 CAM/DISP0 카메라를 하나로 확인하지 못했습니다. 카메라 설정을 확인하세요.')
    return matches[0]


class CameraFrames:
    def __init__(self, source='picamera2', camera_index=None):
        self.picam = self.cap = None
        if source == 'picamera2':
            from picamera2 import Picamera2
            from libcamera import controls
            index = cam0_index(Picamera2.global_camera_info()) if camera_index is None else camera_index
            self.picam = Picamera2(index)
            try:
                configuration = self.picam.create_video_configuration(
                    main={'size': (640, 480), 'format': 'RGB888'}, buffer_count=4)
                self.picam.configure(configuration)
                if 'AfMode' in self.picam.camera_controls:
                    self.picam.set_controls({'AfMode': controls.AfModeEnum.Continuous})
                self.picam.start()
                time.sleep(0.5)
            except BaseException:
                self.picam.close()
                self.picam = None
                raise
            print('CAM/DISP0 software camera index:', index, flush=True)
        else:
            import cv2
            value = int(source) if str(source).isdecimal() else source
            self.cap = cv2.VideoCapture(value)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            if not self.cap.isOpened():
                self.cap.release()
                raise RuntimeError('USB 카메라 또는 영상 파일을 열지 못했습니다.')

    def read(self):
        if self.picam is not None:
            # Picamera2 RGB888의 메모리 배열은 OpenCV에서 사용할 BGR 순서입니다.
            return True, self.picam.capture_array('main')
        return self.cap.read()

    def close(self):
        if self.picam is not None:
            self.picam.stop()
            self.picam.close()
        if self.cap is not None:
            self.cap.release()
