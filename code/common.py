"""교사용 공통 도우미: 호스트와 ROS2 컨테이너 사이의 작은 JSON 파일 전달.

센서·카메라 라이브러리는 호스트에서, rclpy는 컨테이너에서 실행한다.
data 폴더는 같은 프로젝트의 공유 폴더이며 영상 원본을 저장하지 않는다.
"""
from pathlib import Path
import json
import math
import os
import re
import signal
import tempfile
import time

DATA_DIR = Path(os.environ.get(
    "ROS2_LABS_DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")))


def _path(kind, name):
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,47}", name):
        raise ValueError("데이터 이름은 영문 소문자·숫자·밑줄을 사용합니다.")
    return DATA_DIR / f"{name}.{kind}.json"


def _write(kind, name, payload, source_time=None):
    if not isinstance(payload, dict):
        raise TypeError("payload는 dict여야 합니다.")
    captured = time.time() if source_time is None else float(source_time)
    if not math.isfinite(captured):
        raise ValueError("측정 시각은 유한한 숫자여야 합니다.")
    record = {"version": 1, "kind": kind, "name": name,
              "timestamp_s": captured, "payload": payload}
    encoded = json.dumps(record, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(encoded) > 65536:
        raise ValueError("이 예제는 64KB 이하의 결과값만 전달합니다.")
    target = _path(kind, name)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".sample-", dir=DATA_DIR)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
        os.chmod(temporary, 0o644)
        os.replace(temporary, target)  # 쓰는 중인 파일을 다른 프로그램이 읽지 않게 한다.
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return record


def _read(kind, name, max_age):
    if not math.isfinite(max_age) or max_age <= 0:
        raise ValueError("max_age는 0보다 큰 초 단위 숫자입니다.")
    try:
        path = _path(kind, name)
        if path.stat().st_size > 65536:
            return None
        record = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(record, dict) or record.get("version") != 1 or record.get("kind") != kind
                or record.get("name") != name or not isinstance(record.get("payload"), dict)):
            return None
        captured = record["timestamp_s"]
        if isinstance(captured, bool) or not isinstance(captured, (int, float)):
            return None
        age = time.time() - captured
        if not math.isfinite(age) or not 0 <= age <= max_age:
            return None
        return record
    except (OSError, ValueError, KeyError, TypeError):
        return None


def write_sample(name, payload, *, source_time=None):
    return _write("sample", name, payload, source_time)


def read_sample(name, max_age=1.0):
    return _read("sample", name, max_age)


def write_command(name, payload, *, source_time=None):
    return _write("command", name, payload, source_time)


def read_command(name, max_age=1.0):
    return _read("command", name, max_age)


def unit_value(value):
    """LED 밝기로 사용할 수 있는 유한한 0~1 숫자만 허용한다."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) and 0 <= value <= 1 else None


def brightness_for_distance(distance_m, near_m=0.10, far_m=0.80):
    """가까우면 밝게, 멀면 어둡게. 잘못된 값은 LED를 끈다."""
    if isinstance(distance_m, bool) or not isinstance(distance_m, (int, float)):
        return 0.0
    if not math.isfinite(distance_m) or not 0.02 <= distance_m <= 2.0:
        return 0.0
    return max(0.0, min(1.0, (far_m - distance_m) / (far_m - near_m)))


def handle_termination():
    """터미널 종료 요청 때도 finally에서 GPIO를 정리한다."""
    def stop(_signal, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)

