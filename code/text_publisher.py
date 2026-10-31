"""컨테이너 안에서 실행: String 메시지를 발행하는 가장 작은 수업 예제."""
import argparse
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class TextPublisher(Node):
    def __init__(self, message, topic, period):
        super().__init__("class_text_publisher")
        self.message = message
        self.publisher = self.create_publisher(String, topic, 10)
        self.create_timer(period, self.publish_text)

    def publish_text(self):
        message = String()                 # 메시지 타입: String
        message.data = self.message        # 메시지 내용: 문자열
        self.publisher.publish(message)    # 토픽에 발행
        self.get_logger().info(message.data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", default="안녕하세요 ROS2")
    parser.add_argument("--topic", default="/edu/text")
    parser.add_argument("--period", type=float, default=1.0)
    args, ros_args = parser.parse_known_args()
    if not 0.05 <= args.period <= 60:
        parser.error("period는 0.05~60초입니다.")
    rclpy.init(args=ros_args)
    node = TextPublisher(args.message, args.topic, args.period)
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

