"""기존 교육 폴더에 MediaPipe 특징점·YOLO ROS LED5 예제만 검증하여 추가합니다."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
import zipfile


PREFIX = 'pi_basics_6h/'
SPECIAL = {'vision/mediapipe_landmarks.py', 'docs/MediaPipe_손_얼굴_전신_실행안내.txt'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def allowed_payload(name):
    if not name.startswith(PREFIX):
        return False
    relative = name[len(PREFIX):]
    parts = PurePosixPath(relative).parts
    if not parts or any(p.startswith('.') or p in {'data', 'data_validation', '__pycache__'} for p in parts):
        return False
    return relative in SPECIAL or (len(parts) >= 2 and parts[0] == 'ros2_yolo_position')


def load_package(archive):
    """압축을 그대로 풀지 않고 허용된 파일과 manifest 해시를 모두 확인합니다."""
    with zipfile.ZipFile(archive) as z:
        members = {}
        total = 0
        for info in z.infolist():
            name = info.filename
            path = PurePosixPath(name)
            mode = info.external_attr >> 16
            if (name in members or path.is_absolute() or not path.parts or '..' in path.parts
                    or '\\' in name or ':' in name or '\x00' in name
                    or stat.S_ISLNK(mode) or stat.S_IFMT(mode) not in (0, stat.S_IFREG)):
                raise ValueError('안전하지 않거나 중복된 ZIP 항목: ' + name)
            if path.as_posix() != name:
                raise ValueError('정규화되지 않은 ZIP 경로: ' + name)
            total += info.file_size
            if info.file_size > 8*1024*1024 or total > 32*1024*1024:
                raise ValueError('예제 묶음 크기 제한을 초과했습니다.')
            members[name] = info
        if 'MANIFEST.json' not in members or 'install_vision_ros_addons.py' not in members:
            raise ValueError('설치기 또는 MANIFEST.json이 없습니다.')
        manifest = json.loads(z.read('MANIFEST.json'))
        if not isinstance(manifest, dict) or not manifest:
            raise ValueError('manifest는 파일 이름과 SHA256을 연결하는 객체여야 합니다.')
        if set(members) != set(manifest) | {'MANIFEST.json', 'install_vision_ros_addons.py'}:
            raise ValueError('ZIP의 파일 목록과 manifest가 일치하지 않습니다.')
        payload = {}
        for name, expected in manifest.items():
            if (not isinstance(name, str) or not allowed_payload(name)
                    or not isinstance(expected, str) or len(expected) != 64
                    or any(c not in '0123456789abcdef' for c in expected)):
                raise ValueError('허용되지 않은 예제 파일 또는 해시: ' + str(name))
            data = z.read(name)
            if digest(data) != expected:
                raise ValueError('예제 파일 SHA256 불일치: ' + name)
            payload[name[len(PREFIX):]] = data
        if not SPECIAL <= set(payload) or 'ros2_yolo_position/run.sh' not in payload:
            raise ValueError('두 추가 실습의 필수 파일이 없습니다.')
        return payload


def safe_destination(root, relative):
    path = root
    parts = PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        path = path / part
        if path.is_symlink():
            raise ValueError('추가 예제 경로에 심볼릭 링크가 있습니다: ' + str(path))
        if path.exists() and index < len(parts)-1 and not path.is_dir():
            raise ValueError('폴더여야 하는 경로가 파일입니다: ' + str(path))
    if path.exists() and not path.is_file():
        raise ValueError('파일이어야 하는 경로가 폴더입니다: ' + str(path))
    return path


def write_atomic(destination, data):
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.addon-', dir=destination.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)


def install(archive, target, check=False, skip_models=False):
    target = Path(target).expanduser().absolute()
    if target.is_symlink() or not target.is_dir():
        raise ValueError('기존 교육 폴더를 찾지 못했거나 링크 경로입니다: ' + str(target))
    root = target.resolve()
    payload = load_package(archive)
    destinations = {name: safe_destination(root, name) for name in payload}
    data_dir = root/'ros2_yolo_position/data'
    for path in (data_dir.parent, data_dir):
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError('ROS 공유 데이터 경로가 올바른 폴더가 아닙니다: ' + str(path))
    python = root/'.venv-mp/bin/python'
    if not skip_models and not python.is_file():
        raise ValueError('기존 .venv-mp/bin/python이 없습니다. 준비된 수업 SD를 사용하거나 --skip-models로 코드만 추가하세요.')
    changed = [name for name, data in payload.items()
               if not destinations[name].is_file() or destinations[name].read_bytes() != data]
    overwritten = [name for name in changed if destinations[name].is_file()]
    print('설치 위치:', root, flush=True)
    print(f'검증된 파일 {len(payload)}개 / 추가·변경 {len(changed)}개 / 기존 수정본 백업 {len(overwritten)}개', flush=True)
    if check:
        print('확인만 완료했습니다. 파일·모델을 변경하지 않았습니다.', flush=True)
        return {'changed': len(changed), 'backup': None, 'checked': True}
    backup = None
    if overwritten:
        backup_root = root.parent/(root.name+'_addon_backups')
        if backup_root.is_symlink() or (backup_root.exists() and not backup_root.is_dir()):
            raise ValueError('백업 경로가 올바른 폴더가 아닙니다: ' + str(backup_root))
        backup = backup_root/(datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8])
        backup.mkdir(parents=True, exist_ok=False)
        for name in overwritten:
            saved = backup/name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destinations[name], saved)
        print('변경 전 예제 백업:', backup, flush=True)
    done = []
    try:
        for name in changed:
            # 설치 중에도 경로 조건을 다시 확인합니다.
            destination = safe_destination(root, name)
            write_atomic(destination, payload[name])
            done.append(name)
        data_dir.mkdir(parents=True, exist_ok=True)
    except BaseException:
        for name in reversed(done):
            if name in overwritten:
                write_atomic(destinations[name], (backup/name).read_bytes())
            else:
                destinations[name].unlink(missing_ok=True)
        raise
    print('두 추가 예제의 코드를 설치했습니다. 다른 수업 파일과 가상환경은 유지했습니다.', flush=True)
    if not skip_models:
        try:
            subprocess.run([str(python), str(root/'vision/mediapipe_landmarks.py'),
                            '--mode', 'all', '--prepare-models'], cwd=root, check=True)
        except (OSError, subprocess.CalledProcessError) as error:
            print('코드는 설치됐지만 모델 준비가 끝나지 않았습니다. 인터넷 연결을 확인한 뒤 같은 명령을 다시 실행하세요.', file=sys.stderr)
            raise RuntimeError('MediaPipe 모델 준비 실패') from error
    else:
        print('모델 준비는 생략했습니다(--skip-models).', flush=True)
    print('전신: cd ~/pi_basics_6h && .venv-mp/bin/python vision/mediapipe_landmarks.py --mode pose', flush=True)
    print('YOLO ROS: cd ~/pi_basics_6h/ros2_yolo_position', flush=True)
    return {'changed': len(changed), 'backup': str(backup) if backup else None, 'checked': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=Path(__file__).with_name('vision_ros_addons.zip'))
    parser.add_argument('--target', type=Path, default=Path.home()/'pi_basics_6h')
    parser.add_argument('--check', action='store_true', help='검증과 변경 예정 개수만 확인')
    parser.add_argument('--skip-models', action='store_true', help='모델 다운로드 없이 코드만 추가')
    args = parser.parse_args()
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        parser.error('sudo 없이 평소 사용하는 student 계정으로 실행하세요.')
    try:
        install(args.archive, args.target, args.check, args.skip_models)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, KeyError) as error:
        parser.exit(1, str(error)+'\n')


if __name__ == '__main__':
    main()
