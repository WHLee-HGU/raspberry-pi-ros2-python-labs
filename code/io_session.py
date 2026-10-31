"""호스트: 센서/AI와 LED 출력 도우미를 한 터미널에서 함께 실행한다."""
import argparse
import math
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lab', choices=['range', 'hand', 'phone'])
    parser.add_argument('--mock', action='store_true', help='센서/카메라와 GPIO 모두 모의 실행')
    parser.add_argument('--headless', action='store_true', help='AI의 영상 창을 띄우지 않음')
    parser.add_argument('--duration', type=float, default=0, help='0이면 Ctrl+C까지 실행')
    parser.add_argument('--pwm-pin', type=int, default=18, help='BCM 번호. 기본18=물리12번')
    parser.add_argument('--red', type=int, default=6)
    parser.add_argument('--blue', type=int, default=13)
    parser.add_argument('--trigger', type=int, default=23)
    parser.add_argument('--echo', type=int, default=24)
    parser.add_argument('--mock-state', default='CYCLE', help='AI 모의 상태: FIST/OPEN 또는 PHONE/CLEAR')
    parser.add_argument('--conf', type=float, default=0.5, help='YOLO 스마트폰 검출 신뢰도 0~1')
    args = parser.parse_args()
    if not math.isfinite(args.duration) or args.duration < 0:
        parser.error('duration은 0 이상의 초 단위 숫자입니다.')
    if not math.isfinite(args.conf) or not 0 < args.conf <= 1:
        parser.error('conf는 0보다 크고 1 이하인 숫자입니다.')
    if args.lab == 'range' and len({args.pwm_pin, args.trigger, args.echo}) != 3:
        parser.error('PWM LED, TRIG, ECHO의 BCM 번호는 서로 달라야 합니다.')
    code = Path(__file__).resolve().parent
    project = code.parents[1]
    interpreter = Path('/usr/bin/python3')
    source = code/'distance_sensor.py'
    channel = 'distance_led'
    if args.lab != 'range':
        source = code/('vision_hand.py' if args.lab == 'hand' else 'vision_phone.py')
        channel = args.lab+'_led'
        interpreter = (Path(sys.executable) if args.mock else project/
                       ('.venv-mp/bin/python' if args.lab == 'hand' else '.venv-yolo/bin/python'))
    if not interpreter.is_file():
        parser.error('준비된 가상환경 Python을 찾지 못했습니다: '+str(interpreter))
    producer = [str(interpreter), '-u', str(source)]
    if args.lab == 'range':
        producer += ['--trigger', str(args.trigger), '--echo', str(args.echo)]
    if args.lab == 'phone':
        producer += ['--conf', str(args.conf)]
    if args.mock:
        producer += ['--mock']
        if args.lab != 'range':
            producer += ['--mock-state', args.mock_state]
    if args.lab != 'range' and args.headless:
        producer += ['--headless']
    output = ['/usr/bin/python3', '-u', str(code/'led_output.py'), '--channel', channel,
              '--pwm-pin', str(args.pwm_pin), '--red', str(args.red), '--blue', str(args.blue)]
    if args.mock:
        output += ['--mock']
    processes = []
    def stop(_signal, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    try:
        # LED 도우미가 핀을 확보하지 못하면 카메라/센서도 시작하지 않는다.
        processes.append(subprocess.Popen(output, start_new_session=True))
        time.sleep(.25)
        if processes[0].poll() is not None:
            raise RuntimeError('LED 출력 도우미를 시작하지 못했습니다.')
        processes.append(subprocess.Popen(producer, start_new_session=True))
        print('HOST I/O 준비됨. 다른 두 터미널에서 publisher/listener를 실행합니다.', flush=True)
        print('모의 실행' if args.mock else '실제 센서/카메라와 GPIO 실행', flush=True)
        started = time.monotonic()
        while args.duration == 0 or time.monotonic()-started < args.duration:
            for process in processes:
                if process.poll() is not None:
                    raise RuntimeError('도우미가 종료되어 나머지 도우미도 정리합니다.')
            time.sleep(.1)
    except KeyboardInterrupt:
        pass
    finally:
        # 두 도우미를 정리해 Ctrl+C 뒤에 숨은 프로세스가 남지 않게 한다.
        for process in reversed(processes):
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
        for process in reversed(processes):
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait()


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError) as error:
        raise SystemExit(str(error))
