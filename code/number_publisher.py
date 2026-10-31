"""컨테이너: String 대신 Float32 타입으로 숫자를 보내는 비교 예제."""
import argparse
import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32  # 1. 가져올 메시지 타입


class NumberPublisher(Node):
    def __init__(self, value, topic):
        super().__init__('class_number_publisher')
        self.value = value
        self.publisher = self.create_publisher(Float32, topic, 10)  # 2. 발행 타입
        self.create_timer(1.0, self.send_number)

    def send_number(self):
        message = Float32()             # 3. 생성할 메시지 타입
        message.data = float(self.value)  # 4. 타입에 맞는 내용
        self.publisher.publish(message)
        self.get_logger().info(f'{message.data:.2f}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--value', type=float, default=42.0)
    parser.add_argument('--topic', default='/edu/number')
    args, ros_args = parser.parse_known_args()
    if not math.isfinite(args.value) or abs(args.value) > 3.4e38:
        parser.error('Float32 범위의 유한한 숫자를 사용합니다.')
    rclpy.init(args=ros_args)
    node = NumberPublisher(args.value, args.topic)
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
