import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np


class CameraNode(Node):
    """Publishes camera feed as ROS2 Image messages."""
    
    def __init__(self):
        super().__init__('camera_node')
        
        self.get_logger().info('Camera Node starting...')
        
        # Camera configuration
        self.CAMERA_INDEX = 0  # Default camera (0 = /dev/video0)
        self.FRAME_WIDTH = 640
        self.FRAME_HEIGHT = 480
        self.FPS = 30
        self.is_connected = False
        self.display_window = 'Camera Feed'  # Window name for display
        
        # Initialize camera
        self.cap = None
        self._init_camera()
        
        # OpenCV to ROS2 bridge
        self.bridge = CvBridge()
        
        # Image publisher
        self.image_publisher = self.create_publisher(
            Image,
            'raw_camera_image',
            10
        )
        
        # Timer for publishing frames
        publish_period = 1.0 / self.FPS  # Publish at 30 FPS
        self.timer = self.create_timer(publish_period, self.publish_frame)
        
        self.frame_count = 0
    
    def _init_camera(self):
        """Initialize camera capture."""
        try:
            self.cap = cv2.VideoCapture(self.CAMERA_INDEX)
            
            if not self.cap.isOpened():
                self.get_logger().error(f'Failed to open camera at index {self.CAMERA_INDEX}')
                return
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.FRAME_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, self.FPS)
            
            # Warmup camera
            for _ in range(5):
                self.cap.read()
            
            self.is_connected = True
            self.get_logger().info(f'Camera initialized: {self.FRAME_WIDTH}x{self.FRAME_HEIGHT} @ {self.FPS} FPS')
            
        except Exception as e:
            self.get_logger().error(f'Camera initialization error: {e}')
            self.is_connected = False
    
    def publish_frame(self):
        """Capture and publish a frame from camera."""
        if not self.is_connected or self.cap is None:
            return
        
        try:
            ret, frame = self.cap.read()
            
            if not ret:
                self.get_logger().warn('Failed to read frame from camera')
                return
            
            # Display the frame on screen
            cv2.imshow(self.display_window, frame)
            cv2.waitKey(1)  # Needed for display to update
            
            # Convert OpenCV frame to ROS2 Image message
            ros_image = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            
            # Publish the image
            self.image_publisher.publish(ros_image)
            
            self.frame_count += 1
            if self.frame_count % 100 == 0:
                self.get_logger().info(f'Published {self.frame_count} frames')
            
        except Exception as e:
            self.get_logger().error(f'Error publishing frame: {e}')
    
    def get_camera_info(self) -> dict:
        """
        Get current camera information.
        
        Returns:
            Dictionary with camera properties
        """
        if not self.is_connected or self.cap is None:
            return {}
        
        return {
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.cap.get(cv2.CAP_PROP_FPS)),
            'frame_count': int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        }
    
    def set_camera_property(self, property_name: str, value: float) -> bool:
        """
        Set a camera property.
        
        Args:
            property_name: Name of property ('brightness', 'contrast', 'saturation', etc.)
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected or self.cap is None:
            return False
        
        property_map = {
            'brightness': cv2.CAP_PROP_BRIGHTNESS,
            'contrast': cv2.CAP_PROP_CONTRAST,
            'saturation': cv2.CAP_PROP_SATURATION,
            'hue': cv2.CAP_PROP_HUE,
            'exposure': cv2.CAP_PROP_EXPOSURE,
            'focus': cv2.CAP_PROP_FOCUS,
            'zoom': cv2.CAP_PROP_ZOOM,
        }
        
        if property_name not in property_map:
            self.get_logger().warn(f'Unknown camera property: {property_name}')
            return False
        
        try:
            self.cap.set(property_map[property_name], value)
            self.get_logger().info(f'Set {property_name} to {value}')
            return True
        except Exception as e:
            self.get_logger().error(f'Failed to set {property_name}: {e}')
            return False
    
    def destroy_node(self):
        """Cleanup camera on shutdown."""
        if self.cap is not None:
            self.cap.release()
            self.get_logger().info('Camera released')
        
        # Close OpenCV windows
        cv2.destroyAllWindows()
        
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
