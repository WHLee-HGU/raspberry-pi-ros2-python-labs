"""호스트 읽기 전용 점검. GPIO를 열거나 카메라를 사용하지 않는다."""
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[2]
    print('프로젝트:', root)
    missing = False
    for relative in ['classroom.sh', '.venv-mp/bin/python', '.venv-yolo/bin/python',
                     'models/gesture_recognizer.task', 'models/yolo11n_ncnn_model']:
        path = root/relative
        print(('OK ' if path.exists() else 'MISSING ')+relative)
        missing = missing or not path.exists()
    print('호스트 Python:', sys.version.split()[0])
    result = subprocess.run(['sudo','docker','inspect','pi-class','--format',
                             '{{.State.Status}}\n{{range .Config.Env}}{{println .}}{{end}}'],
                            capture_output=True,text=True)
    if result.returncode:
        print('교사가 먼저 기존 classroom.sh start 조번호로 컨테이너를 준비합니다.')
        return 1
    for entry in result.stdout.splitlines():
        if entry in ['running','exited'] or entry.startswith(('ROS_DOMAIN_ID=','ROS_DISTRO=')):
            print(entry)
    print('이 점검은 실제 센서·LED·카메라 인식 결과를 검증하지 않습니다.')
    return 2 if missing else 0


if __name__ == '__main__':
    raise SystemExit(main())
