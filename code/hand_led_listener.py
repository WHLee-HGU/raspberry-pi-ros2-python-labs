"""컨테이너: 주먹은 빨강, 펼친 손은 파랑 LED 명령으로 바꿉니다."""
import argparse
import time
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from std_msgs.msg import String
from common import write_command
from vision_policy import decode_state, hand_colors


class HandLedListener(Node):
    def __init__(self):
        super().__init__('hand_led_listener')
        self.gesture, self.source_time = 'UNKNOWN', 0.0
        self.subscription = self.create_subscription(String, '/edu/hand_gesture', self.on_message, 10)
        self.timer = self.create_timer(.1, self.update_led)

    def on_message(self, message):
        gesture, stamp = decode_state(message.data, 'gesture', ('FIST', 'OPEN', 'UNKNOWN'), time.time())
        if gesture != self.gesture:
            self.get_logger().info('gesture='+gesture)
        self.gesture, self.source_time = gesture, stamp

    def update_led(self):
        now = time.time()
        gesture = self.gesture if -.2 <= now-self.source_time <= 1.0 else 'UNKNOWN'
        write_command('hand_led', hand_colors(gesture), source_time=self.source_time if gesture != 'UNKNOWN' else now)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duration', type=float, default=0)
    args, ros_args = parser.parse_known_args()
    rclpy.init(args=ros_args)
    node = HandLedListener()
    start = time.monotonic()
    try:
        while rclpy.ok() and (args.duration <= 0 or time.monotonic()-start < args.duration):
            rclpy.spin_once(node, timeout_sec=.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        write_command('hand_led', {'red': 0.0, 'blue': 0.0})
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
