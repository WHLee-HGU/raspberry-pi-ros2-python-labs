#!/usr/bin/env bash
# 배포된 Bookworm 수업 SD에 새 코드/모델만 추가합니다. sudo 없이 실행합니다.
set -euo pipefail
if [[ ${EUID:-$(id -u)} -eq 0 ]]; then
  echo 'sudo 없이 평소 사용하는 student 계정으로 실행하세요.' >&2
  exit 2
fi
for required_tool in curl python3 sha256sum mktemp; do
  command -v "$required_tool" >/dev/null || { echo "필요한 기본 도구 없음: $required_tool" >&2; exit 2; }
done
ros2_lab_tmp=$(mktemp -d -t pi-ros2-labs.XXXXXXXX)
archive="$ros2_lab_tmp/ros2_python_labs_code.zip"
curl -fL --retry 2 --connect-timeout 10 --max-time 180 \
  https://raw.githubusercontent.com/WHLee-HGU/raspberry-pi-ros2-python-labs/main/ros2_python_labs_code.zip \
  -o "$archive"
printf '47733138a36d1008df31b4ffa151439ed93b992975ad87b24366357eddb9196a  %s\n' "$archive" | sha256sum --check
python3 -m zipfile -e "$archive" "$ros2_lab_tmp"
bash "$ros2_lab_tmp/ros2_python_labs/install_on_pi.sh" "$@"
echo '다음: cd ~/pi_basics_6h/ros2_python_labs && bash run_lab.sh check'
