"""AI 결과를 LED 상태로 바꾸는 작은 규칙. 카메라·ROS 없이도 검사할 수 있습니다."""
import math
import json


def classify_gesture(categories, hand_count=1, min_score=.6):
    """공식 모델의 Closed_Fist/Open_Palm만 수업의 두 동작으로 사용합니다."""
    if hand_count != 1 or len(categories) != 1 or not categories[0]:
        return 'UNKNOWN'
    try:
        top = categories[0][0]
        score = float(top.score)
        if not math.isfinite(score) or not min_score <= score <= 1:
            return 'UNKNOWN'
        return {'Closed_Fist': 'FIST', 'Open_Palm': 'OPEN'}.get(top.category_name, 'UNKNOWN')
    except (AttributeError, TypeError, ValueError):
        return 'UNKNOWN'


class StableGesture:
    """같은 손동작이 3프레임 이어져야 확정합니다. 불명확하면 즉시 UNKNOWN."""
    def __init__(self, frames=3):
        self.frames = frames
        self.candidate = 'UNKNOWN'
        self.count = 0

    def update(self, raw):
        if raw not in ('FIST', 'OPEN'):
            self.candidate, self.count = 'UNKNOWN', 0
            return 'UNKNOWN'
        self.count = self.count + 1 if raw == self.candidate else 1
        self.candidate = raw
        return raw if self.count >= self.frames else 'UNKNOWN'


class StablePhone:
    """2프레임 검출로 PHONE, 0.5초 동안 2프레임 이상 미검출이면 CLEAR."""
    def __init__(self, frames=2, clear_seconds=0.5):
        self.frames = frames
        self.clear_seconds = clear_seconds
        self.positives = self.negatives = 0
        self.clear_since = None

    def update(self, present, now):
        if present is None or not math.isfinite(now):
            self.positives = self.negatives = 0
            self.clear_since = None
            return 'UNKNOWN'
        if present:
            self.positives += 1
            self.negatives = 0
            self.clear_since = None
            return 'PHONE' if self.positives >= self.frames else 'UNKNOWN'
        self.positives = 0
        self.negatives += 1
        if self.clear_since is None or now < self.clear_since:
            self.clear_since = now
        if self.negatives >= self.frames and now-self.clear_since >= self.clear_seconds:
            return 'CLEAR'
        return 'UNKNOWN'


def encode_state(sample, key, allowed, now):
    """String.data에 넣을 JSON. 촬영 시각을 바꾸지 않고 함께 전달합니다."""
    label, source_time = 'UNKNOWN', now
    if isinstance(sample, dict):
        payload = sample.get('payload')
        candidate = payload.get(key) if isinstance(payload, dict) else None
        timestamp = sample.get('timestamp_s')
        if isinstance(candidate, str) and candidate in allowed and isinstance(timestamp, (int, float)) and not isinstance(timestamp, bool):
            if math.isfinite(timestamp) and -.2 <= now-timestamp <= 1.0:
                label, source_time = candidate, float(timestamp)
    return json.dumps({key: label, 'source_time': source_time}, allow_nan=False)


def decode_state(text, key, allowed, now):
    """잘못된 내용·오래된 결과·알 수 없는 상태는 UNKNOWN으로 처리합니다."""
    try:
        payload = json.loads(text)
        label, stamp = payload[key], payload['source_time']
        if not isinstance(label, str) or label not in allowed or isinstance(stamp, bool) or not isinstance(stamp, (int, float)):
            return 'UNKNOWN', now
        if not math.isfinite(stamp) or not -.2 <= now-stamp <= 1.0:
            return 'UNKNOWN', now
        return label, float(stamp)
    except (TypeError, ValueError, KeyError):
        return 'UNKNOWN', now


def hand_colors(gesture):
    return {'red': float(gesture == 'FIST'), 'blue': float(gesture == 'OPEN')}


def phone_colors(state, now):
    # PHONE이면 1초마다 한 번 점멸합니다(켜짐 0.5초, 꺼짐 0.5초).
    return {'red': float(state == 'PHONE' and now % 1.0 < .5),
            'blue': float(state == 'CLEAR')}
