"""ROS2 컨테이너: 호스트 초음파 측정값을 Range 메시지로 발행한다."""
import argparse
import math
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from common import read_sample


class DistancePublisher(Node):
    def __init__(self, topic, period):
        super().__init__("class_distance_publisher")
        self.publisher = self.create_publisher(Range, topic, 10)
        self.create_timer(period, self.publish_distance)

    def publish_distance(self):
        sample = read_sample("distance", max_age=0.5)
        captured = time.time() if sample is None else sample["timestamp_s"]
        value = None if sample is None else sample["payload"].get("distance_m")
        valid = (not isinstance(value, bool) and isinstance(value, (int, float))
                 and math.isfinite(value) and 0.02 <= value <= 2.0)
        message = Range()                         # 타입: sensor_msgs/msg/Range
        message.header.stamp.sec = int(captured)
        message.header.stamp.nanosec = int((captured - int(captured)) * 1_000_000_000)
        message.header.frame_id = "class_ultrasonic"
        message.radiation_type = Range.ULTRASOUND
        message.field_of_view = 0.26               # 수업용 근사값(rad)
        message.min_range = 0.02                   # 단위 m
        message.max_range = 2.0
        message.range = float(value) if valid else float("nan")
        self.publisher.publish(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", default="/edu/range")
    parser.add_argument("--period", type=float, default=0.1)
    args, ros_args = parser.parse_known_args()
    if not math.isfinite(args.period) or args.period <= 0:
        parser.error("period는 양수입니다.")
    rclpy.init(args=ros_args)
    node = DistancePublisher(args.topic, args.period)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()

