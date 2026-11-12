#!/usr/bin/env bash
# 배포된 수업용 Raspberry Pi OS SD의 예제 초기화. sudo 없이 실행합니다.
set -euo pipefail
if [[ ${EUID:-$(id -u)} -eq 0 ]]; then
  echo 'sudo 없이 student 계정의 파이 OS 터미널에서 실행하세요.' >&2; exit 2
fi
for tool in curl python3 sha256sum mktemp; do
  command -v "$tool" >/dev/null || { echo "기본 도구 없음: $tool" >&2; exit 2; }
done
course_tmp=$(mktemp -d -t pi-course-v2.XXXXXXXX)
trap 'rm -rf -- "$course_tmp"' EXIT
curl -fL --retry 2 --connect-timeout 10 --max-time 180 \
  https://raw.githubusercontent.com/WHLee-HGU/raspberry-pi-ros2-python-labs/main/course_v2.zip \
  -o "$course_tmp/course_v2.zip"
printf '182dea8e9e16ce6b027f901337c146da62672edf6f90b56baf9327d45a9d8d94  %s\n' "$course_tmp/course_v2.zip" | sha256sum --check
# 다운로드를 검증한 다음 임시 폴더 안에서만 압축을 푼다.
python3 - "$course_tmp" <<'PY'
from pathlib import Path, PurePosixPath
import stat, sys, zipfile
root = Path(sys.argv[1])
with zipfile.ZipFile(root/'course_v2.zip') as archive:
    if sum(x.file_size for x in archive.infolist()) > 64*1024*1024:
        raise SystemExit('배포 ZIP 크기 초과')
    for item in archive.infolist():
        path = PurePosixPath(item.filename)
        if path.is_absolute() or '..' in path.parts or '\\' in item.filename or ':' in item.filename:
            raise SystemExit('잘못된 ZIP 경로')
        if stat.S_ISLNK(item.external_attr >> 16):
            raise SystemExit('ZIP 심볼릭 링크는 지원하지 않습니다.')
    archive.extractall(root/'extracted')
PY
python3 "$course_tmp/extracted/reset_course_v2.py" "$@"
