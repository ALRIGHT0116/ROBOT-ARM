from rclpy.node import Node


class CameraBridgeNode(Node):    
    def __init__(self):
        super().__init__('camera_bridge_node')
        self.get_logger().info('Camera Bridge Node has been started.')

        # Timer subscription (chess_timer에서 토픽 받아옴) 구독자 만들어야함    
        self.timer_sub = self.create_subscription(int, 'timer', self.timer_callback, 10)
        
def main(args=None):