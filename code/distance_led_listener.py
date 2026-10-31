"""ROS2 컨테이너: 거리를 받아 LED PWM 밝기 명령으로 바꾼다."""
import argparse
import math
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from common import brightness_for_distance, write_command


class DistanceLedListener(Node):
    def __init__(self, topic, near_cm, far_cm):
        super().__init__("class_distance_led_listener")
        self.near_m, self.far_m = near_cm / 100, far_cm / 100
        self.brightness = 0.0
        self.captured = None
        self.received = None
        self.subscription = self.create_subscription(Range, topic, self.on_distance, 10)
        self.create_timer(0.1, self.update_led)

    def on_distance(self, message):
        captured = message.header.stamp.sec + message.header.stamp.nanosec / 1_000_000_000
        age = time.time() - captured
        valid = (math.isfinite(age) and 0 <= age <= 1.0 and math.isfinite(message.range)
                 and 0.02 <= message.range <= 2.0
                 and message.min_range <= message.range <= message.max_range)
        self.brightness = (brightness_for_distance(message.range, self.near_m, self.far_m)
                           if valid else 0.0)
        self.captured = captured if valid else None
        self.received = time.monotonic()

    def update_led(self):
        fresh = (self.received is not None and time.monotonic() - self.received <= 1.0
                 and self.captured is not None and 0 <= time.time() - self.captured <= 1.0)
        write_command("distance_led", {"brightness": self.brightness if fresh else 0.0},
                      source_time=self.captured if fresh else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", default="/edu/range")
    parser.add_argument("--near-cm", type=float, default=10.0)
    parser.add_argument("--far-cm", type=float, default=80.0)
    args, ros_args = parser.parse_known_args()
    if not 2 <= args.near_cm < args.far_cm <= 200:
        parser.error("2 <= near-cm < far-cm <= 200을 만족해야 합니다.")
    rclpy.init(args=ros_args)
    node = DistanceLedListener(args.topic, args.near_cm, args.far_cm)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        write_command("distance_led", {"brightness": 0.0})
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
