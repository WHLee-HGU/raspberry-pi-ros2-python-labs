"""컨테이너: 스마트폰은 빨강 점멸, 미검출 확정은 파랑 표시등으로 표현합니다."""
import argparse
import time
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from std_msgs.msg import String
from common import write_command
from vision_policy import decode_state, phone_colors


class PhoneLedListener(Node):
    def __init__(self):
        super().__init__('phone_led_listener')
        self.state, self.source_time = 'UNKNOWN', 0.0
        self.subscription = self.create_subscription(String, '/edu/phone_state', self.on_message, 10)
        self.timer = self.create_timer(.1, self.update_led)

    def on_message(self, message):
        state, stamp = decode_state(message.data, 'state', ('PHONE', 'CLEAR', 'UNKNOWN'), time.time())
        if state != self.state:
            self.get_logger().info('phone='+state)
        self.state, self.source_time = state, stamp

    def update_led(self):
        now = time.time()
        state = self.state if -.2 <= now-self.source_time <= 1.0 else 'UNKNOWN'
        write_command('phone_led', phone_colors(state, now), source_time=self.source_time if state != 'UNKNOWN' else now)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duration', type=float, default=0)
    args, ros_args = parser.parse_known_args()
    rclpy.init(args=ros_args)
    node = PhoneLedListener()
    start = time.monotonic()
    try:
        while rclpy.ok() and (args.duration <= 0 or time.monotonic()-start < args.duration):
            rclpy.spin_once(node, timeout_sec=.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        write_command('phone_led', {'red': 0.0, 'blue': 0.0})
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
