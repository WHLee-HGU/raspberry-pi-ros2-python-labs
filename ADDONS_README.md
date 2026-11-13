# 추가 실습: MediaPipe 손·얼굴·전신과 YOLO 위치 → ROS2 → LED 5개

기존 교육용 SD 카드에 새 예제를 **추가**합니다. 기존 `~/pi_basics_6h` 폴더의 다른 예제와 학생 작업물은 유지합니다. OS, Wi-Fi, 카메라 설정, Python 패키지, ROS2 컨테이너를 다시 설치하지 않습니다.

## 다운로드와 추가 설치: 두 줄

실행 중인 카메라·LED·ROS 실습을 `Ctrl+C`로 종료한 뒤, **Docker 밖 Raspberry Pi OS의 student 터미널**에서 입력합니다. `sudo`를 붙이지 않습니다.

```bash
curl -fL https://raw.githubusercontent.com/WHLee-HGU/raspberry-pi-ros2-python-labs/main/add_vision_ros_examples.sh -o ~/add_vision_ros_examples.sh
bash ~/add_vision_ros_examples.sh
```

다운로드한 코드의 해시를 검증한 뒤 아래 위치에 파일을 넣습니다.

```text
~/pi_basics_6h/
├── vision/mediapipe_landmarks.py
├── docs/MediaPipe_손_얼굴_전신_실행안내.txt
└── ros2_yolo_position/
    ├── run.sh
    ├── vision_position.py
    ├── position_publisher.py
    ├── position_listener.py
    ├── position_policy.py
    ├── led5_output.py
    └── README_실행과배선.txt  (그 밖의 실행 보조 파일도 함께 설치)
```

이전에 같은 새 예제 파일을 수정했다면 변경된 파일만 별도 백업하고 배포본으로 갱신합니다. 다른 예제, 가상환경, 기존 모델은 유지합니다. 기본 설치는 필요한 MediaPipe 공식 모델을 미리 준비하며, 없는 모델을 처음 받을 때 인터넷이 필요합니다. YOLO는 기존 `.venv-yolo`와 `models/yolo11n_ncnn_model`을 사용합니다.

`reset_course_v2.sh`는 전체 수업 코드 초기화용입니다. **이번 추가 설치에는 위 `add_vision_ros_examples.sh`만 사용하세요.** 나중에 전체 초기화를 하면 추가 예제도 초기화 대상이므로 그 후 위 두 줄을 다시 실행합니다.

## MediaPipe 전신·손·얼굴 실행

```bash
cd ~/pi_basics_6h
.venv-mp/bin/python vision/mediapipe_landmarks.py --mode pose
```

`pose`를 바꿔 다른 모드를 선택합니다.

| 옵션 | 표시되는 내용 |
|---|---|
| `--mode hands` | 손의 점과 연결선 |
| `--mode face` | 얼굴 랜드마크와 윤곽선 |
| `--mode pose` | 전신 관절과 뼈대 |
| `--mode all` | 손·얼굴·전신을 함께 표시 |

카메라 영상 안에 머리부터 발끝까지 들어오게 하면 전신을 관찰하기 좋습니다. `all`은 세 모델을 실행하므로 단일 모드보다 느릴 수 있습니다. 창에서 `Q` 또는 터미널에서 `Ctrl+C`로 종료합니다. 사진이나 영상을 저장하지 않습니다.

## YOLO 위치 → ROS2 → LED 5개 실행

Pi OS 터미널 3개를 열고 **각각** 다음 폴더로 이동합니다.

```bash
cd ~/pi_basics_6h/ros2_yolo_position
```

터미널 1: 카메라·YOLO·LED 입출력

```bash
bash run.sh io --target "cell phone"
```

터미널 2: ROS2 publisher

```bash
bash run.sh pub
```

터미널 3: ROS2 listener와 밝기 계산

```bash
bash run.sh sub
```

스마트폰을 좌우로 움직이면 중심 픽셀 좌표, 정규화 좌표, `[---------------1---------------]` 막대와 5개 PWM 값이 출력됩니다. 물체에 가까운 LED가 가장 밝고 양옆으로 갈수록 어두워집니다. 물체 미검출 또는 오래된 입력에서는 LED를 끕니다.

LED를 아직 배선하지 않았다면 터미널 1만 다음 중 하나로 바꿉니다.

```bash
bash run.sh io --mock
```

위 명령은 카메라와 GPIO 없이 모의 위치를 만듭니다. 실제 카메라로 인식하되 GPIO는 사용하지 않으려면:

```bash
bash run.sh io --mock-leds --target "cell phone"
```

인식 대상은 `--target bottle`, `--target cup` 등 기존 모델의 클래스 이름으로 바꿀 수 있습니다. 같은 종류가 여러 개면 가장 높은 신뢰도의 물체 하나를 선택하며 개체의 신원을 추적하는 기능은 없습니다.

## LED 배선과 밝기

배선을 바꾸기 전에 정상 종료하고 USB-C 전원을 분리합니다. 왼쪽부터 같은 색의 LED 5개를 놓습니다.

| LED 위치 | BCM GPIO | 물리 핀 |
|---|---:|---:|
| 1, 왼쪽 끝 | 5 | 29 |
| 2 | 6 | 31 |
| 3, 가운데 | 13 | 33 |
| 4 | 19 | 35 |
| 5, 오른쪽 끝 | 26 | 37 |

각각 `GPIO → 330Ω 저항 → LED 긴 다리(+)`, 짧은 다리(-)는 공통 GND로 연결합니다. GND는 물리 39번 또는 6번입니다. LED마다 저항을 하나씩 사용합니다. 이전 LED 프로그램은 종료합니다.

이번 예제는 gpiozero/lgpio의 **100Hz 소프트웨어 PWM**을 사용합니다. LED 기준 위치는 `[0, 0.25, 0.5, 0.75, 1]`이며 밝기는 다음 식으로 계산합니다.

```python
brightness = math.exp(-0.5 * ((x - led_center) / sigma) ** 2)
```

기본 `sigma=0.18`에서 중앙 물체의 밝기는 약 `[0.02, 0.38, 1.00, 0.38, 0.02]`입니다. `bash run.sh sub --sigma 0.25`로 퍼짐을 넓힐 수 있습니다. 기본 0.12초 평활화를 끄려면 `--smooth-seconds 0`을 사용합니다.

## 설치 옵션과 확인

설치 대상과 변경 예정 파일만 확인:

```bash
bash ~/add_vision_ros_examples.sh --check
```

지금은 코드만 추가하고 모델 다운로드를 나중에 할 때:

```bash
bash ~/add_vision_ros_examples.sh --skip-models
cd ~/pi_basics_6h
.venv-mp/bin/python vision/mediapipe_landmarks.py --mode all --prepare-models
```

설치 후 모델 다운로드만 실패했다면 마지막 명령을 다시 실행하면 됩니다. 새 OS 또는 가상환경이 없는 카드에 패키지를 설치해 주는 스크립트는 아닙니다.

카메라가 안 열리면 먼저 기존 미리보기 프로그램을 종료하고 `rpicam-hello --list-cameras`를 확인합니다. `--camera-index 0`의 번호는 소프트웨어 목록 번호이며 CAM/DISP0·CAM/DISP1 물리 포트 번호와는 다릅니다.

기존 실습과 함께 자세한 설명을 볼 위치:

- `~/pi_basics_6h/docs/MediaPipe_손_얼굴_전신_실행안내.txt`
- `~/pi_basics_6h/ros2_yolo_position/README_실행과배선.txt`
