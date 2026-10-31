"""컨테이너: Float32 메시지의 data 필드를 받아 출력한다."""
import argparse
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class NumberListener(Node):
    def __init__(self, topic):
        super().__init__('class_number_listener')
        self.subscription = self.create_subscription(Float32, topic, self.on_number, 10)

    def on_number(self, message):
        self.get_logger().info(f'받은 숫자: {message.data:.2f}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topic', default='/edu/number')
    args, ros_args = parser.parse_known_args()
    rclpy.init(args=ros_args)
    node = NumberListener(args.topic)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
