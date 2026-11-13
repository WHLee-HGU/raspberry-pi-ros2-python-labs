#!/usr/bin/env bash
# 이미 배포된 Pi OS 수업 폴더에 두 추가 예제만 넣습니다. sudo 없이 실행하세요.
set -euo pipefail
if [[ ${EUID:-$(id -u)} -eq 0 ]]; then
  echo 'sudo 없이 평소 사용하는 student 계정으로 실행하세요.' >&2
  exit 2
fi
for required_tool in curl python3 sha256sum mktemp; do
  command -v "$required_tool" >/dev/null || { echo "필요한 도구 없음: $required_tool" >&2; exit 2; }
done
addons_tmp=$(mktemp -d -t pi-vision-ros-addons.XXXXXXXX)
trap 'rm -f -- "$addons_tmp/vision_ros_addons.zip" "$addons_tmp/install_vision_ros_addons.py"; rmdir -- "$addons_tmp" 2>/dev/null || true' EXIT
addons_archive="$addons_tmp/vision_ros_addons.zip"
curl -fL --retry 2 --connect-timeout 10 --max-time 180 \
  https://raw.githubusercontent.com/WHLee-HGU/raspberry-pi-ros2-python-labs/main/vision_ros_addons.zip \
  -o "$addons_archive"
printf '6d67c516ee36192dc2e459bd645e8d7b5645b3b97395027ce9a207ab0d05fe2e  %s\n' "$addons_archive" | sha256sum --check
# 해시를 확인한 묶음에서 설치기 하나만 꺼냅니다. 예제 파일은 설치기가 개별 검증합니다.
python3 - "$addons_archive" "$addons_tmp/install_vision_ros_addons.py" <<'PY'
from pathlib import Path, PurePosixPath
import stat, sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as z:
    seen=set()
    total=0
    for item in z.infolist():
        path=PurePosixPath(item.filename)
        mode=item.external_attr >> 16
        if (item.filename in seen or path.is_absolute() or not path.parts
                or '..' in path.parts or '\\' in item.filename or ':' in item.filename
                or '\x00' in item.filename or stat.S_ISLNK(mode)
                or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR))):
            raise SystemExit('안전하지 않은 ZIP 항목입니다.')
        seen.add(item.filename)
        total+=item.file_size
        if item.file_size>8*1024*1024 or total>32*1024*1024:
            raise SystemExit('예제 묶음 크기가 예상 범위를 초과했습니다.')
    data=z.read('install_vision_ros_addons.py')
    Path(sys.argv[2]).write_bytes(data)
PY
python3 "$addons_tmp/install_vision_ros_addons.py" --archive "$addons_archive" "$@"
