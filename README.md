# 라즈베리파이 Python ROS2 연동 실습

배포된 수업용 SD카드에 Python 예제를 추가하는 자료입니다. 문자열·숫자 통신, 초음파 거리로 LED 밝기 조절, 손동작과 스마트폰 감지에 따른 LED 반응을 실습합니다.

**기존 수업 환경이 준비된 Raspberry Pi OS Bookworm 64비트 SD카드용**입니다. 기존 `~/pi_basics_6h/classroom.sh`, `pi-class` ROS2 Humble Docker 컨테이너, GPIO·카메라 패키지, `.venv-mp`, `.venv-yolo`, YOLO11n NCNN 모델을 사용합니다. 새 OS 전체를 설치하는 도구는 아닙니다.

## 설치 명령 두 줄

인터넷에 연결한 파이의 **일반 사용자 계정**에서 실행합니다. 현재 터미널이 Docker 컨테이너 안이라면 `exit`로 파이 OS 터미널로 먼저 돌아옵니다.

```bash
curl -fL https://raw.githubusercontent.com/WHLee-HGU/raspberry-pi-ros2-python-labs/main/install_remote.sh -o install_ros2_labs.sh
bash install_ros2_labs.sh
```

첫 줄의 다운로드가 성공한 뒤 두 번째 줄을 실행합니다. 실행기는 코드 ZIP을 다운로드하고 SHA256을 확인한 뒤 임시 폴더에 압축을 풀어 설치합니다. 기존 예제를 먼저 덮어쓰지 않도록 했습니다. **설치에는 `sudo`를 붙이지 않습니다.**

설치기는 새 예제와 동봉한 Gesture Recognizer 모델만 복사합니다. `apt`·`pip` 설치나 SD카드 재기록은 하지 않습니다. 기존 파일과 내용이 다르면 `~/pi_basics_6h/ros2_python_labs_backups/`에 원본을 백업합니다. 같은 파일로 다시 설치하면 불필요하게 덮어쓰거나 백업하지 않습니다.

설치 후 확인합니다.

```bash
cd ~/pi_basics_6h/ros2_python_labs
bash run_lab.sh check
```

새 코드는 `~/pi_basics_6h/ros2_python_labs/code/`, 새 모델은 `~/pi_basics_6h/models/gesture_recognizer.task`에 들어갑니다. 모델 파일을 ZIP에 포함했으므로 수업 중에 모델을 다시 다운로드할 필요가 없습니다.

### ZIP을 직접 사용하는 경우

코드 ZIP을 직접 내려받아 설치할 수도 있습니다. 인터넷이 없는 파이에 설치할 때는 ZIP을 다른 PC에서 받아 파이로 복사한 뒤 두 번째 줄을 실행합니다.

```bash
curl -fL https://raw.githubusercontent.com/WHLee-HGU/raspberry-pi-ros2-python-labs/main/ros2_python_labs_code.zip -o ros2_python_labs_code.zip
ros2_lab_tmp=$(mktemp -d) && python3 -m zipfile -e ros2_python_labs_code.zip "$ros2_lab_tmp" && bash "$ros2_lab_tmp/ros2_python_labs/install_on_pi.sh"
```

ZIP도 임시 폴더에 풉니다. 현재 위치가 기존 수업 프로젝트여도 설치기가 원본을 백업한 뒤 파일을 추가하도록 하는 절차입니다.

## 실행 위치와 종료

아래 명령은 모두 **파이 OS의 일반 터미널**에서 실행합니다. 각 터미널에서 먼저 `cd ~/pi_basics_6h/ros2_python_labs`를 실행합니다.

`run_lab.sh`가 필요한 ROS 노드를 기존 컨테이너 안에서 실행해 줍니다. `classroom.sh enter`를 먼저 실행할 필요가 없습니다. Docker 실행 때 관리자 비밀번호를 물으면 해당 파이 계정의 비밀번호를 입력합니다.

종료할 때는 실행 중인 각 터미널에서 `Ctrl+C`를 누릅니다. 센서·카메라와 LED 출력 프로그램을 함께 실행하는 `io-*` 도우미도 이때 정리됩니다.

## 1. 메시지 내용과 타입

문자열을 보내고 받는 예제입니다. 서로 다른 두 터미널에서 각각 실행합니다.

| 터미널 | 명령 |
| --- | --- |
| A: publisher | `bash run_lab.sh text-pub --message '우리 조의 메시지'` |
| B: listener | `bash run_lab.sh text-sub` |

`std_msgs/msg/String`의 `data`에 문자열을 넣습니다. 기본 토픽은 `/edu/text`입니다. 내용은 `--message` 또는 `code/text_publisher.py`의 `message.data`에 넣는 값으로 바꿉니다.

숫자를 보내는 비교 예제도 제공합니다.

| 터미널 | 명령 |
| --- | --- |
| A: publisher | `bash run_lab.sh number-pub --value 42.5` |
| B: listener | `bash run_lab.sh number-sub` |

이 예제는 `std_msgs/msg/Float32`와 `/edu/number`를 사용합니다. 문자열 예제와 숫자 예제를 비교하며 다음 항목을 함께 바꾼다는 점을 확인합니다.

- 양쪽 코드의 메시지 타입 `import`
- `create_publisher()`와 `create_subscription()`의 타입
- 생성하는 메시지 객체와 필드에 넣는 값의 타입

토픽 이름을 바꾸면 publisher와 listener 양쪽에 같은 `--topic`을 지정합니다. 기본 설치 예제인 `demo_nodes_cpp`·`demo_nodes_py`는 수정하지 않고 새 Python 파일을 사용합니다.

## 2. 초음파 거리와 LED PWM

기본 배선은 **BCM 번호**를 사용합니다. 물리 핀 번호와 구분하세요.

| 장치 | BCM 번호 | 보드의 물리 핀 |
| --- | ---: | ---: |
| 밝기 조절 LED | 18 | 12 |
| HC-SR04 TRIG | 23 | 16 |
| HC-SR04 ECHO | 24 | 18 |
| 빨강 LED | 6 | 31 |
| 파랑 LED | 13 | 33 |

LED마다 330Ω 직렬 저항과 공통 GND를 사용합니다. HC-SR04는 5V를 사용하며 **ECHO를 기존 교재의 1kΩ/2kΩ 분압 회로를 거쳐 BCM24에 연결**합니다. 배선은 파이를 정상 종료하고 전원을 분리한 상태에서 합니다.

세 터미널에서 각각 실행합니다.

| 터미널 | 역할 | 명령 |
| --- | --- | --- |
| A | 센서와 LED 도우미 | `bash run_lab.sh io-range` |
| B | 거리 publisher | `bash run_lab.sh range-pub` |
| C | 밝기 listener | `bash run_lab.sh range-sub` |

publisher는 `/edu/range`에 `sensor_msgs/msg/Range`를 보냅니다. `range` 필드의 단위는 **미터**입니다. listener는 10cm 이하에서 최대 밝기, 80cm 이상에서 꺼짐, 사이 구간은 선형 밝기로 변환합니다. 측정 실패·기본 측정 범위 밖의 값·오래된 값은 LED를 끕니다.

기준 거리는 C에서 `bash run_lab.sh range-sub --near-cm 15 --far-cm 60`으로 바꿀 수 있습니다. PWM 핀은 A의 `--pwm-pin`으로 바꿉니다. GPIOZero/lgpio의 소프트웨어 PWM을 사용합니다.

**배선 없이 프로그램 흐름만 확인할 때**는 A를 다음처럼 실행하고, B·C는 위와 같이 실행합니다.

```bash
bash run_lab.sh io-range --mock
```

이때 실제 센서와 GPIO는 열지 않습니다. A의 출력에서 LED에 적용할 예정 값을 확인합니다.

## 3. MediaPipe 손동작과 빨강·파랑 LED

빨강 LED는 BCM6, 파랑 LED는 BCM13입니다. 각 LED에 330Ω 저항을 사용합니다. 카메라는 CAM/DISP0에 연결합니다.

| 터미널 | 역할 | 명령 |
| --- | --- | --- |
| A | 카메라·MediaPipe·LED 도우미 | `bash run_lab.sh io-hand` |
| B | 손동작 publisher | `bash run_lab.sh hand-pub` |
| C | LED listener | `bash run_lab.sh hand-sub` |

공식 MediaPipe Gesture Recognizer 모델의 `Closed_Fist`와 `Open_Palm`을 사용합니다. 신뢰도 0.6 이상으로 같은 결과가 3프레임 이어질 때 확정합니다.

| 상태 | 의미 | 반응 |
| --- | --- | --- |
| `FIST` | 주먹 | 빨강 LED 켜짐 |
| `OPEN` | 펼친 손 | 파랑 LED 켜짐 |
| `UNKNOWN` | 손 없음·여러 손·다른 동작·미확인 | 두 LED 꺼짐 |

카메라나 LED 없이 시험할 때는 A에 `--mock`을 붙입니다. `--mock-state FIST` 또는 `--mock-state OPEN`으로 모의 상태를 고정할 수도 있습니다. 영상 창이 필요 없으면 실제 실행 A에 `--headless`를 붙입니다.

## 4. YOLO 스마트폰 감지 알림등

손동작 실습을 종료한 뒤 같은 LED와 카메라를 사용합니다.

| 터미널 | 역할 | 명령 |
| --- | --- | --- |
| A | 카메라·YOLO·LED 도우미 | `bash run_lab.sh io-phone` |
| B | 감지 상태 publisher | `bash run_lab.sh phone-pub` |
| C | LED listener | `bash run_lab.sh phone-sub` |

기존 YOLO11n NCNN 모델의 `cell phone` 클래스를 신뢰도 0.5 이상으로 찾습니다. 연속 2프레임 검출하면 `PHONE`으로 판단해 빨강 LED를 1Hz로 점멸합니다. 미검출이 2프레임 이상이며 0.5초 이상 이어지면 `CLEAR`로 판단해 파랑 LED를 켭니다. 미확인 상태나 오래된 결과는 두 LED를 끕니다.

`CLEAR`는 최근 프레임에서 스마트폰을 검출하지 않았다는 뜻입니다. 인식 결과는 조명·거리·가림 등에 영향을 받습니다.

배선·카메라 없이 시험할 때 A에 `--mock`을 붙입니다. `--mock-state PHONE` 또는 `--mock-state CLEAR`로 모의 상태를 고정할 수 있습니다. 실제 실행의 검출 신뢰도는 `--conf 0.6`처럼 바꿉니다.

## AI 결과가 ROS 메시지가 되는 과정

Bookworm 호스트에서 센서·카메라·AI를 실행하고, 같은 공유 폴더에 결과와 측정 시각을 기록합니다. 컨테이너의 Python publisher가 이를 읽어 ROS2 토픽으로 보냅니다. listener가 정한 LED 값을 호스트의 출력 도우미가 GPIO에 적용합니다. 카메라 영상 원본은 저장하거나 ROS 메시지로 보내지 않습니다.

손동작 토픽 `/edu/hand_gesture`와 스마트폰 토픽 `/edu/phone_state`는 `std_msgs/msg/String`을 사용합니다. `data`에는 상태와 원본 시각을 담은 JSON 문자열이 들어갑니다.

```json
{"gesture": "FIST", "source_time": 1234567890.0}
```

listener는 잘못된 내용과 오래된 결과를 거르고, 호스트 LED 도우미도 새 명령이 오지 않으면 출력을 끕니다. 파일·메시지의 시각을 임의로 갱신해 오래된 관측값을 새 결과처럼 사용하지 않습니다.

ROS2에 Docker가 반드시 필요한 것은 아닙니다. 이 수업은 Bookworm의 GPIO·카메라 환경을 유지하면서 Ubuntu 기반 ROS2 Humble을 사용하려고 Docker를 선택했습니다. 호스트의 Python 3.11 가상환경과 컨테이너의 Python 3.10·`rclpy` 환경을 구분합니다.

## 검증 범위

준비된 실제 파이의 Docker ROS2 환경에서 문자열·숫자 통신, 모의 거리와 PWM 값, 모의 손동작과 LED 값, 모의 스마트폰 감지와 점멸·입력 중단 시 꺼짐을 확인했습니다. 실제 카메라로 Gesture Recognizer와 YOLO의 프레임 처리도 확인했습니다.

이 검증에서는 실제 초음파·LED 회로를 구동하지 않았고, 주먹·펼친 손·스마트폰을 실제로 제시한 인식 성공 시험도 수행하지 않았습니다. 수업 전에는 사용할 회로와 조명에서 해당 동작을 확인합니다. 모의 입력과 실제 장치 결과를 구분해 기록하세요.

6시간 본 수업은 초음파 ROS2 PWM 연동을 중심으로 진행하고, 두 영상 연동은 선택 실습 또는 교사 시연으로 사용합니다. 세 연동 실습을 모두 본 수업에 추가하는 구성은 아닙니다. PPT 교육자료는 별도로 제공합니다.

## 참고 자료

- [ROS2 공식 Python 예제](https://github.com/ros2/demos/tree/humble/demo_nodes_py)
- [ROS2 메시지 정의](https://github.com/ros2/common_interfaces/tree/humble)
- [Docker 컨테이너 개념](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/)
- [Python 가상환경](https://docs.python.org/3.11/library/venv.html)
- [MediaPipe Gesture Recognizer](https://developers.google.com/edge/mediapipe/solutions/vision/gesture_recognizer/python)
- [YOLO Python 추론](https://docs.ultralytics.com/modes/predict/)

저장소: [WHLee-HGU/raspberry-pi-ros2-python-labs](https://github.com/WHLee-HGU/raspberry-pi-ros2-python-labs)
