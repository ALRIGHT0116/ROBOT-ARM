import rclpy
from sensor_msgs.msg import Image
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import numpy as np
import cv2
from cv_bridge import CvBridge

class VisionControlNode(Node):    
    def __init__(self):
        super().__init__('vision_control_node')
        self.get_logger().info('Vision Control Node has been started.')
        
        # camera_node에서 토픽 받아옴
        self.camera_sub = self.create_subscription(Image, 'raw_camera_image', self.camera_callback, 10)
        
        # chess_brain으로 토픽 보냄
        self.move_pub = self.create_publisher(Float64MultiArray, 'detected_angles', 10)
        self.bridge = CvBridge()

        # HSV color thresholds (tune for your lighting)
        self.red_lower_1 = np.array([0, 120, 80])
        self.red_upper_1 = np.array([10, 255, 255])
        self.red_lower_2 = np.array([170, 120, 80])
        self.red_upper_2 = np.array([180, 255, 255])
        self.blue_lower = np.array([90, 120, 80])
        self.blue_upper = np.array([130, 255, 255])
        self.min_area = 80  # minimum contour area to count as a point

    def camera_callback(self, msg):
        self.get_logger().info('Received image for processing.')
        # 이미지 데이터 처리 로직 추가 필요
        detected_angles = self.process_image(msg)
        
        if detected_angles is not None:
            move_msg = Float64MultiArray()
            move_msg.data = detected_angles
            self.move_pub.publish(move_msg)
            self.get_logger().info(f'Published detected angles: {detected_angles}')

    def process_image(self, image_msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(image_msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'Failed to convert image: {e}')
            return None

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        red_points = self._find_color_points(
            hsv,
            [(self.red_lower_1, self.red_upper_1), (self.red_lower_2, self.red_upper_2)]
        )
        blue_points = self._find_color_points(
            hsv,
            [(self.blue_lower, self.blue_upper)]
        )

        if len(red_points) < 2 or len(blue_points) < 2:
            self.get_logger().warn(
                f'Not enough points detected. red={len(red_points)}, blue={len(blue_points)}'
            )
            return None

        red_points = self._select_two_points(red_points)
        blue_points = self._select_two_points(blue_points)

        red_angle = self._line_angle_deg(red_points[0], red_points[1])
        blue_angle = self._line_angle_deg(blue_points[0], blue_points[1])
        relative_angle = self._smallest_angle_deg(blue_angle - red_angle)

        return [float(blue_angle), float(relative_angle)]

    def _find_color_points(self, hsv, ranges):
        mask = None
        for lower, upper in ranges:
            current = cv2.inRange(hsv, lower, upper)
            mask = current if mask is None else cv2.bitwise_or(mask, current)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        points = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.min_area:
                continue
            moments = cv2.moments(cnt)
            if moments['m00'] == 0:
                continue
            cx = int(moments['m10'] / moments['m00'])
            cy = int(moments['m01'] / moments['m00'])
            points.append(((cx, cy), area))

        return points

    def _select_two_points(self, points_with_area):
        # pick two largest blobs
        points_with_area.sort(key=lambda p: p[1], reverse=True)
        return [points_with_area[0][0], points_with_area[1][0]]

    def _line_angle_deg(self, p1, p2):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        angle = np.degrees(np.arctan2(dy, dx))
        return angle

    def _smallest_angle_deg(self, angle):
        # wrap to [-180, 180]
        wrapped = (angle + 180.0) % 360.0 - 180.0
        return wrapped
    
def main(args=None):
    rclpy.init(args=args)
    vision_control_node = VisionControlNode()
    rclpy.spin(vision_control_node)
    vision_control_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
