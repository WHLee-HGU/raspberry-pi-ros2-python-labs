"""호스트 Python3: HC-SR04 거리값을 공유 파일에 저장한다.

ECHO(5V)는 기존 교재의 분압 회로를 거쳐 BCM24에 연결한다.
--mock은 실제 핀을 열지 않는 모의 입력이다.
"""
import argparse
from contextlib import ExitStack
import math
import time
from common import handle_termination, write_sample


def read_distance_m(trigger, echo, timeout=0.03):
    if echo.value:
        return None
    trigger.on()
    try:
        time.sleep(0.00001)
    finally:
        trigger.off()
    deadline = time.perf_counter() + timeout
    while not echo.value:
        if time.perf_counter() >= deadline:
            return None
    started = time.perf_counter()
    while echo.value:
        if time.perf_counter() - started >= timeout:
            return None
    distance = (time.perf_counter() - started) * 343.0 / 2
    return distance if 0.02 <= distance <= 2.0 else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--mock-values", default="0.10,0.30,0.80,1.0,invalid",
                        help="모의 거리(m)를 쉼표로 구분. invalid는 측정 실패")
    parser.add_argument("--mock-hold", type=float, default=1.0)
    parser.add_argument("--trigger", type=int, default=23)
    parser.add_argument("--echo", type=int, default=24)
    parser.add_argument("--period", type=float, default=0.10)
    parser.add_argument("--duration", type=float, default=0, help="0이면 Ctrl+C까지 실행")
    args = parser.parse_args()
    if not (math.isfinite(args.period) and args.period >= 0.06
            and math.isfinite(args.mock_hold) and args.mock_hold > 0
            and math.isfinite(args.duration) and args.duration >= 0):
        parser.error("period는 0.06초 이상, mock-hold는 양수, duration은 0 이상입니다.")
    if not 0 <= args.trigger <= 27 or not 0 <= args.echo <= 27 or args.trigger == args.echo:
        parser.error("TRIG/ECHO는 서로 다른 BCM GPIO 0~27을 지정합니다.")
    values = []
    for text in args.mock_values.split(","):
        value = None if text.strip().lower() == "invalid" else float(text)
        if value is not None and not math.isfinite(value):
            parser.error("모의 거리에는 유한한 숫자 또는 invalid를 사용합니다.")
        values.append(value)
    if not values:
        parser.error("모의 거리값이 필요합니다.")
    handle_termination()
    with ExitStack() as resources:
        trigger = echo = None
        if not args.mock:
            from gpiozero import DigitalInputDevice, OutputDevice
            from gpio_backend import create_header_factory
            factory = create_header_factory()
            resources.callback(factory.close)
            trigger = resources.enter_context(OutputDevice(args.trigger, initial_value=False, pin_factory=factory))
            echo = resources.enter_context(DigitalInputDevice(args.echo, pull_up=False, pin_factory=factory))
            time.sleep(0.2)
        started = time.monotonic()
        print("MOCK distance source" if args.mock else "HC-SR04 distance source", flush=True)
        try:
            while args.duration == 0 or time.monotonic() - started < args.duration:
                captured = time.time()
                value = (values[int((time.monotonic() - started) / args.mock_hold) % len(values)]
                         if args.mock else read_distance_m(trigger, echo))
                write_sample("distance", {"distance_m": value, "mock": args.mock}, source_time=captured)
                time.sleep(args.period)
        except KeyboardInterrupt:
            pass
        finally:
            write_sample("distance", {"distance_m": None, "mock": args.mock, "status": "stopped"})


if __name__ == "__main__":
    main()

