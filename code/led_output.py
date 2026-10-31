"""호스트 Python3: ROS listener가 남긴 밝기 명령을 실제 LED에 적용한다.

PWM BCM18=물리12번, 빨강 BCM6=물리31번, 파랑 BCM13=물리33번.
각 LED에는 직렬 저항을 연결한다. --mock은 GPIO를 열지 않는다.
"""
import argparse
from contextlib import ExitStack
import fcntl
import json
import math
import time
from common import DATA_DIR, handle_termination, read_command, unit_value, write_sample


def command_values(channel, record):
    off = {"brightness": 0.0, "red": 0.0, "blue": 0.0}
    if record is None:
        return off, "stale_or_missing"
    payload = record["payload"]
    keys = ["brightness"] if channel == "distance_led" else ["red", "blue"]
    values = {key: unit_value(payload.get(key)) for key in keys}
    if any(value is None for value in values.values()):
        return off, "invalid_command"
    return dict(off, **values), "fresh"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=["distance_led", "hand_led", "phone_led"], default="distance_led")
    parser.add_argument("--mock", action="store_true", help="핀을 열지 않고 실제 적용 예정값만 기록")
    parser.add_argument("--pwm-pin", "--pin", dest="pwm_pin", type=int, default=18)
    parser.add_argument("--red", type=int, default=6)
    parser.add_argument("--blue", type=int, default=13)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--period", type=float, default=0.05)
    parser.add_argument("--duration", type=float, default=0)
    args = parser.parse_args()
    if any(not 0 <= pin <= 27 for pin in [args.pwm_pin, args.red, args.blue]) or args.red == args.blue:
        parser.error("서로 다른 빨강/파랑 BCM 핀 0~27을 사용합니다.")
    if not (math.isfinite(args.timeout) and args.timeout > 0
            and math.isfinite(args.period) and 0 < args.period <= 1
            and math.isfinite(args.duration) and args.duration >= 0):
        parser.error("timeout과 period는 양수, duration은 0 이상이어야 합니다.")
    handle_termination()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # 모드가 달라도 실제 LED 출력 프로그램은 한 번에 하나만 실행한다.
    with ExitStack() as resources:
        lock = resources.enter_context(open("/tmp/pi-classroom-led-output.lock", "a"))
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("다른 LED 출력 프로그램이 실행 중입니다. 먼저 Ctrl+C로 종료하세요.")
        devices = {}
        if not args.mock:
            from gpiozero import PWMLED
            from gpio_backend import create_header_factory
            factory = create_header_factory()
            resources.callback(factory.close)
            mapping = ({"brightness": args.pwm_pin} if args.channel == "distance_led"
                       else {"red": args.red, "blue": args.blue})
            for name, pin in mapping.items():
                devices[name] = resources.enter_context(PWMLED(pin, initial_value=0, frequency=100, pin_factory=factory))
        last = None
        started = time.monotonic()
        print("MOCK LED output" if args.mock else "GPIO LED output", flush=True)
        try:
            while args.duration == 0 or time.monotonic() - started < args.duration:
                record = read_command(args.channel, max_age=args.timeout)
                values, reason = command_values(args.channel, record)
                for name, device in devices.items():
                    device.value = values[name]
                state = dict(values, channel=args.channel, mock=args.mock, reason=reason)
                write_sample("led_output", state)
                if state != last:
                    print(json.dumps(state, ensure_ascii=False), flush=True)
                    last = state
                time.sleep(args.period)
        except KeyboardInterrupt:
            pass
        finally:
            for device in devices.values():
                device.off()
            write_sample("led_output", {"brightness": 0.0, "red": 0.0, "blue": 0.0,
                                       "channel": args.channel, "mock": args.mock, "reason": "stopped"})


if __name__ == "__main__":
    main()

