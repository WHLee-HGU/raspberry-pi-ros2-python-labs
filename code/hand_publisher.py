"""컨테이너: MediaPipe 결과를 /edu/hand_gesture 토픽으로 발행합니다."""
import argparse
import time
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from std_msgs.msg import String
from common import read_sample
from vision_policy import encode_state


class HandPublisher(Node):
    def __init__(self):
        super().__init__('hand_publisher')
        self.publisher = self.create_publisher(String, '/edu/hand_gesture', 10)
        self.timer = self.create_timer(.1, self.publish_hand)

    def publish_hand(self):
        sample = read_sample('hand', max_age=1.0)
        message = String()
        message.data = encode_state(sample, 'gesture', ('FIST', 'OPEN', 'UNKNOWN'), time.time())
        self.publisher.publish(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duration', type=float, default=0)
    args, ros_args = parser.parse_known_args()
    rclpy.init(args=ros_args)
    node = HandPublisher()
    start = time.monotonic()
    try:
        while rclpy.ok() and (args.duration <= 0 or time.monotonic()-start < args.duration):
            rclpy.spin_once(node, timeout_sec=.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
