"""컨테이너 안에서 실행: 같은 토픽·타입의 String 메시지를 받는다."""
import argparse
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class TextListener(Node):
    def __init__(self, topic):
        super().__init__("class_text_listener")
        self.subscription = self.create_subscription(String, topic, self.on_message, 10)

    def on_message(self, message):
        self.get_logger().info("받은 내용: " + message.data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", default="/edu/text")
    args, ros_args = parser.parse_known_args()
    rclpy.init(args=ros_args)
    node = TextListener(args.topic)
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

