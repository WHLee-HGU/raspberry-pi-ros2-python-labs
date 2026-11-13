# 라즈베리파이 Python·ROS2 교육 예제

## 새 추가 실습: MediaPipe 전신과 YOLO 위치·LED 5개

기존 교육 폴더에 손·얼굴·전신 랜드마크 예제와 YOLO → ROS2 → LED 5개 가우시안 PWM 예제를 추가합니다. 기존 다른 예제와 가상환경을 유지합니다.

실행 중인 실습을 종료하고 **Docker 밖 Pi OS 터미널**에서 다음 두 줄을 실행합니다(`sudo` 없이).

```bash
curl -fL https://raw.githubusercontent.com/WHLee-HGU/raspberry-pi-ros2-python-labs/main/add_vision_ros_examples.sh -o ~/add_vision_ros_examples.sh
bash ~/add_vision_ros_examples.sh
```

MediaPipe 예제는 `~/pi_basics_6h/vision/mediapipe_landmarks.py`, 새 ROS2 예제는 `~/pi_basics_6h/ros2_yolo_position/`에 설치됩니다. 필요한 MediaPipe 모델도 준비합니다.

**[추가 예제의 실행 명령·배선·코드 설명](ADDONS_README.md)**

이번 두 예제만 추가하려면 위 명령을 사용합니다. 아래 `reset_course_v2.sh`는 기존 수업 코드를 전체 초기화하는 별도 작업입니다.

---

## 두 번째 교육용 개정판: 버튼, PWM, 초음파 과제, 가위바위보

이 버전은 이미 배포한 수업용 SD카드의 코드를 초기화하고 새 예제로 바꿉니다.
수업용 OS·패키지·Docker 이미지가 준비된 Raspberry Pi OS Bookworm 64비트가 필요합니다.
새 OS에 필요한 모든 패키지를 설치하는 스크립트는 아닙니다.

## 다운로드와 초기화: 두 줄

모든 실습을 Ctrl+C로 종료하고 Docker 밖 **파이 OS의 student 터미널**에서 실행합니다.
다음 명령에는 sudo를 붙이지 않습니다.

```bash
cd ~ && curl -fL https://raw.githubusercontent.com/WHLee-HGU/raspberry-pi-ros2-python-labs/main/reset_course_v2.sh -o reset_course_v2.sh
bash ~/reset_course_v2.sh
```

다운로드한 압축 파일의 SHA256과 포함 파일의 해시를 확인한 다음 설치합니다.
**기존 `~/pi_basics_6h`의 코드·학생 수정본·데이터·그 밖의 수업 파일은
`~/pi_basics_6h_backups/날짜-식별자/`로 옮겨 보관**합니다.
그 후 새 수업 코드로 교체하므로 이전 실습의 JSON이나 수정된 Python 파일이 섞이지 않습니다.
반복 실행하면 그때의 상태가 다시 백업됩니다. 수업 중 불필요하게 반복하지 않습니다.

`.venv`, `.venv-base`, `.venv-mp`, `.venv-yolo`는 같은 절대 경로에 보존합니다.
`models`도 보존하며, 동봉한 공식 Gesture Recognizer 모델과 출처 파일만 검증·추가합니다.
기존 YOLO NCNN 및 Hand Landmarker 모델은 그대로 사용합니다.
OS, Wi-Fi, 계정, 카메라 설정, 설치된 Python 패키지는 변경하지 않습니다.
기존 패키지나 가상환경 자체가 수정된 경우 아래 점검 후 교사가 별도로 복구해야 합니다.

실행 중인 호스트 Python 실습이 감지되면 초기화를 중단합니다.
`pi-class` 컨테이너가 실행 중이면 잠시 정상 종료하고 같은 컨테이너를 다시 시작합니다.
이미지, 조 번호와 ROS_DOMAIN_ID는 유지합니다. 프로젝트 루트 폴더도 유지하여 /work 연결을 보존합니다.
Docker 확인 권한이 필요하다고 나오면 `sudo -v`를 먼저 실행한 후 재시도합니다.

초기화 없이 배포 파일과 대상만 확인할 때:

```bash
bash ~/reset_course_v2.sh --check
```

업데이트 후:

```bash
cd ~/pi_basics_6h
bash preflight_v2.sh
python3 labs/button_led.py
```

초기화가 중간에 실패하면 교체한 파일을 되돌립니다. 기존 수정본은 삭제하지 않습니다.
필요한 이전 Python 파일은 백업 폴더에서 열어 확인하거나 다른 이름으로 복사할 수 있습니다.
새 예제와 이름이 같은 파일을 다시 덮어쓰면 그 파일은 새 기준 상태에서 벗어납니다.

## 인터넷 없는 파이

다른 PC에서 이 저장소의 `course_v2.zip`과 `course_v2.sha256`을 받아 USB로 파이에 복사합니다.
`cd`로 두 파일이 있는 폴더에 들어가 다음을 실행합니다.

```bash
sha256sum --check course_v2.sha256
course_tmp=$(mktemp -d) && python3 -m zipfile -e course_v2.zip "$course_tmp" && python3 "$course_tmp/reset_course_v2.py"
```

압축 파일은 기존 수업 폴더에 직접 풀지 않습니다. 설치기가 먼저 백업하도록 임시 폴더를 사용합니다.

## 예제 실행

기본 예제는 `cd ~/pi_basics_6h` 후 실행합니다.

| 실습 | 명령 |
|---|---|
| 버튼을 누르는 동안 LED 켜기 | `python3 labs/button_led.py` |
| 100Hz 소프트웨어 PWM 밝기 실습 | `python3 labs/pwm_led.py` |
| 초음파 거리 출력 | `python3 labs/distance_read.py` |
| 학생 거리-PWM 과제 | `python3 labs/distance_pwm_assignment.py` |
| 교사용 완성 코드 | `python3 labs/distance_pwm_solution.py` |
| MediaPipe 가위바위보와 세 LED | `.venv-mp/bin/python vision/rps_led.py` |

기본 실습은 `--mock --duration 5`를 붙이면 GPIO 없이 확인할 수 있습니다.
가위바위보는 `python3 vision/rps_led.py --mock --duration 5`로 모의 실행할 수 있습니다.
모의 실행은 실제 카메라 인식이나 배선의 성공을 의미하지 않습니다.

ROS 연동은 서로 다른 세 터미널에서 각각 `cd ~/pi_basics_6h/ros2_python_labs` 후:

```bash
bash run_lab.sh io-rps
```
```bash
bash run_lab.sh rps-pub
```
```bash
bash run_lab.sh rps-sub
```

배선·카메라 없이 ROS 흐름을 시험할 때 첫 명령에만 `--mock`을 붙입니다.
직접 실행과 ROS 실습은 한 번에 하나만 실행합니다. 종료는 각 터미널에서 Ctrl+C입니다.

## 기본 배선

버튼 BCM27(물리13)과 GND, 첫 LED BCM17(물리11), PWM LED BCM18(물리12).
초음파 TRIG=BCM23(물리16), ECHO=BCM24(물리18)이며 ECHO 5V는 1kΩ/2kΩ 분압을 거칩니다.
가위 빨강 BCM6(물리31), 바위 파랑 BCM13(물리33), 보 노랑 BCM19(물리35).
각 LED에 330Ω 직렬 저항과 공통 GND를 사용합니다. 노랑은 별도 LED 한 개입니다.
전원을 분리한 상태에서 배선합니다. PWM은 GPIOZero/lgpio의 소프트웨어 PWM 100Hz입니다.

공식 MediaPipe `Victory`, `Closed_Fist`, `Open_Palm` 결과를 가위·바위·보로 매핑합니다.
신뢰도0.6, 연속3프레임 확인을 적용하며 미확인·손 없음·두 손·오래된 결과는 모두 꺼집니다.
코드 설명과 전체 배선은 설치된 `README.md`, `docs/`, `가위바위보_실행과_코드설명.txt`에 있습니다.

## 참고

- [GPIOZero Button](https://gpiozero.readthedocs.io/en/stable/api_input.html#button)
- [GPIOZero PWMLED](https://gpiozero.readthedocs.io/en/stable/api_output.html#pwmled)
- [MediaPipe Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer/python)
- [ROS2 Humble Python 예제](https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html)

이전 1차 교육용 파일과 `install_remote.sh`도 유지됩니다. 두 번째 교육은 위 `reset_course_v2.sh`를 사용합니다.
