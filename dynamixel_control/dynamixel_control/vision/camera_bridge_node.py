from rclpy.node import Node
from sensor_msgs.msg import Image
import rclpy
from dynamixel_control.utils.calibration import Calibration
import numpy as np
from std_msgs.msg import String, Int32
from cv_bridge import CvBridge
import cv2
import os

class CameraBridgeNode(Node):    
    def __init__(self):
        super().__init__('camera_bridge_node')
        self.get_logger().info('Camera Bridge Node has been started.')
        self.declare_parameter('debug_show_windows', False)
        self.declare_parameter('debug_save_images', True)
        self.declare_parameter('debug_output_dir', '/tmp/chess_debug')
        self.declare_parameter('interactive_manual_corners', True)
        self.declare_parameter('manual_corners', [])
        self.debug_show_windows = bool(self.get_parameter('debug_show_windows').value)
        self.debug_save_images = bool(self.get_parameter('debug_save_images').value)
        self.debug_output_dir = str(self.get_parameter('debug_output_dir').value)
        self.interactive_manual_corners = bool(
            self.get_parameter('interactive_manual_corners').value
        )
        self.manual_corners = self.get_parameter('manual_corners').value
        os.makedirs(self.debug_output_dir, exist_ok=True)
        self.bridge = CvBridge()
        self.raw_image = None
        self.manual_corners_locked = False
        #camera_node에서 토픽 받아옴
        self.camera_sub = self.create_subscription(Image, 'raw_camera_image', self.camera_callback, 10)
        #chess_timer에서 토픽 받아옴   
        self.timer_sub = self.create_subscription(Int32, 'camera_timer', self.timer_callback, 10)
        self.calibration = Calibration()
        self._configure_manual_corners()
        #chess_brain으로 토픽 보냄
        self.notatation_pub = self.create_publisher(String, 'notation',10)

    def _configure_manual_corners(self):
        if not self.manual_corners:
            self.get_logger().info('Calibration mode: auto corner detection')
            return

        try:
            values = [float(v) for v in self.manual_corners]
            if len(values) != 8:
                raise ValueError(
                    f'manual_corners length must be 8, got {len(values)}'
                )
            points = [
                [values[0], values[1]],  # TL
                [values[2], values[3]],  # TR
                [values[4], values[5]],  # BR
                [values[6], values[7]],  # BL
            ]
            self.calibration.set_manual_corners(points)
            self.manual_corners_locked = True
            self.get_logger().info(
                f'Calibration mode: manual corners TL,TR,BR,BL={points}'
            )
        except Exception as e:
            self.get_logger().error(
                f'Invalid manual_corners parameter: {self.manual_corners}, error: {e}'
            )

    def _select_manual_corners_from_clicks(self, image):
        window_name = 'Select 4 corners: TL -> TR -> BR -> BL (q: cancel)'
        clicked_points = []
        display = image.copy()

        def on_mouse(event, x, y, _flags, _param):
            if event != cv2.EVENT_LBUTTONDOWN:
                return
            if len(clicked_points) >= 4:
                return
            clicked_points.append([float(x), float(y)])
            label = ['TL', 'TR', 'BR', 'BL'][len(clicked_points) - 1]
            cv2.circle(display, (x, y), 6, (0, 0, 255), -1)
            cv2.putText(
                display,
                f'{label}({x},{y})',
                (x + 8, y - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1,
                cv2.LINE_AA,
            )

        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, on_mouse)

        while True:
            cv2.imshow(window_name, display)
            key = cv2.waitKey(20) & 0xFF
            if len(clicked_points) == 4:
                break
            if key == ord('q'):
                clicked_points = []
                break

        cv2.destroyWindow(window_name)
        return clicked_points

    def camera_callback(self, msg):
        self.raw_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        
        
    def timer_callback(self, msg):
        self.player_phase = msg.data
        self.get_logger().info('Timer callback received message: {}'.format(msg.data))
        if self.raw_image is None:
            self.get_logger().warn('No camera image received yet.')
            return

        if self.player_phase == 1:
            if (not self.manual_corners_locked) and self.interactive_manual_corners:
                try:
                    points = self._select_manual_corners_from_clicks(self.raw_image)
                    if len(points) == 4:
                        self.calibration.set_manual_corners(points)
                        self.manual_corners_locked = True
                        self.get_logger().info(
                            f'Interactive corners set TL,TR,BR,BL={points}'
                        )
                    else:
                        self.get_logger().warn(
                            'Interactive corner selection canceled. '
                            'Falling back to auto corner detection.'
                        )
                except Exception as e:
                    self.get_logger().error(
                        f'Interactive corner selection failed: {e}. '
                        'Falling back to auto corner detection.'
                    )

            self.cal_image_before = self.calibration.calibrate(self.raw_image)
            print(f"[calibration][before] corners(TL,TR,BR,BL): {self.calibration.get_last_corners()}")
            before_debug = self.calibration.draw_last_corners(self.raw_image)
            grid_before = self._build_grid_preview(self.cal_image_before)
            if self.debug_show_windows:
                cv2.imshow('corners_before', before_debug)
                cv2.imshow('cal_image_before', self.cal_image_before)
            self.cutted_image_before = self.cut_image(self.cal_image_before)
            if self.debug_save_images:
                before_board = self._compose_board_image(self.cutted_image_before)
                self._save_debug_image('corners_before', before_debug)
                self._save_debug_image('cal_image_before', self.cal_image_before)
                self._save_debug_image('grid_before', grid_before)
                self._save_debug_image('cutted_before_board', before_board)
            if self.debug_show_windows:
                cv2.imshow('grid_before', grid_before)
                cv2.waitKey(1)

        elif self.player_phase == 2:
            self.cal_image_after = self.calibration.calibrate(self.raw_image)
            print(f"[calibration][after] corners(TL,TR,BR,BL): {self.calibration.get_last_corners()}")
            after_debug = self.calibration.draw_last_corners(self.raw_image)
            grid_after = self._build_grid_preview(self.cal_image_after)
            if self.debug_show_windows:
                cv2.imshow('corners_after', after_debug)
                cv2.imshow('cal_image_after', self.cal_image_after)
            self.cutted_image_after = self.cut_image(self.cal_image_after)
            if self.debug_save_images:
                after_board = self._compose_board_image(self.cutted_image_after)
                self._save_debug_image('corners_after', after_debug)
                self._save_debug_image('cal_image_after', self.cal_image_after)
                self._save_debug_image('grid_after', grid_after)
                self._save_debug_image('cutted_after_board', after_board)
            if self.debug_show_windows:
                cv2.imshow('grid_after', grid_after)
            result = self.compare_images()
            print(f'[compare_images] result: {result}')
            if self.debug_show_windows:
                cv2.waitKey(1)

        else: pass
    
    def cut_image(self, image):
        cutted_image = [[0 for _ in range(8)] for _ in range(8)]
        cutted_image_width = int(len(image[0]) // 8)
        cutted_image_height = int(len(image) // 8)
        for i in range (8):
            for j in range(8):
                y0, y1 = i * cutted_image_height, (i + 1) * cutted_image_height
                x0, x1 = j * cutted_image_width, (j + 1) * cutted_image_width
                cutted_image[i][j] = image[y0:y1, x0:x1]
        return cutted_image

    def _build_grid_preview(self, image):
        preview = image.copy()
        h, w = preview.shape[:2]
        cell_w = w // 8
        cell_h = h // 8

        for i in range(1, 8):
            cv2.line(preview, (i * cell_w, 0), (i * cell_w, h), (0, 255, 0), 1)
            cv2.line(preview, (0, i * cell_h), (w, i * cell_h), (0, 255, 0), 1)

        return preview

    def _compose_board_image(self, cutted_image):
        rows = [np.hstack(row) for row in cutted_image]
        return np.vstack(rows)

    def _save_debug_image(self, name, image):
        file_path = os.path.join(self.debug_output_dir, f'{name}.png')
        ok = cv2.imwrite(file_path, image)
        if ok:
            self.get_logger().info(f'Saved debug image: {file_path}')
        else:
            self.get_logger().warn(f'Failed to save debug image: {file_path}')

    def compare_images(self):
        differences = np.zeros((8, 8), dtype=np.int64)
        for i in range(8):
            for j in range(8):
                differences[i, j] = self.compute_difference(
                    self.cutted_image_before[i][j],
                    self.cutted_image_after[i][j]
                )
            # 2. 행렬을 1차원 배열로 펴기 (Flatten)
        flat_diff = differences.flatten()

        # 3. 값이 큰 순서대로 정렬하여 인덱스 4개 뽑기 (argsort 사용)
        # argsort는 작은 순서대로 정렬하므로 [::-1]로 뒤집어서 큰 값이 먼저 오게 함
        top_6_indices = np.argsort(flat_diff)[::-1][:6]

        # 4. 1차원 인덱스를 다시 (행, 열) 좌표로 변환 (unravel_index)
        top_indices = []
        top_coords = []
        print("=== 변화량 Top ===")
        top_6_values = flat_diff[top_6_indices]
        max_mean = (top_6_values[0] + top_6_values[1]) / 2
        min_mean = (top_6_values[4] + top_6_values[5]) / 2
        middle_mean = (top_6_values[2] + top_6_values[3]) / 2

        if max_mean - middle_mean > middle_mean - min_mean:
            # 캐슬링이 아니라면 상위 2개 선택
            top_indices = top_6_indices[:2]
        else:
            # 캐슬링이라면 상위 4개 선택
            top_indices = top_6_indices[:4]

        for idx in top_indices:
            # unravel_index: 1차원 인덱스(0~63)를 (행, 열)로 바꿔줌
            row, col = np.unravel_index(int(idx), differences.shape)
            value = differences[row, col]
            
            # 체스 좌표 변환 (예: (0,0) -> a1)
            chess_notation = f"{chr(ord('a') + col)}{8 - (row)}"
            
            #예시:['e2', 'e4'] or ['e1', 'g1', 'h1', 'f1']
            top_coords.append({'name': chess_notation, 'row': row, 'col': col})
            print(f"좌표: ({row}, {col}) -> {chess_notation} | 변화량: {value}")

        #결론적으로는 e2e4 이런식으로 반환해야함
        # 캐슬링: ['e1', 'g1', 'h1', 'f1'] or ['e1', 'c1', 'a1', 'd1']
        if len(top_coords) == 2:
            # 일반 이동: ['e2', 'e4']
            first = top_coords[0]
            second = top_coords[1]
            img1 = self.cutted_image_after[first['row']][first['col']]
            img2 = self.cutted_image_after[second['row']][second['col']] 
            var1 = np.var(img1)
            var2 = np.var(img2)    
             
            if var1 < var2:
                commend_coords = f"{first['name']}{second['name']}"
            else:
                commend_coords = f"{second['name']}{first['name']}"     

        elif len(top_coords) == 4:  
            # 어떤 캐슬링인지 판별
            if any(coord['name'] == "h1" for coord in top_coords):
                commend_coords = 'e1g1'
            else:
                commend_coords = 'e1c1'
        else:
            commend_coords = "error"

        #chess_brain으로 명령 전송
        msg = String()
        msg.data = commend_coords
        self.notatation_pub.publish(msg)
        self.get_logger().info(f'{commend_coords}로 이동')

        #필요없을거 같긴함
        return commend_coords
            
                  
    def compute_difference(self, img1, img2):
        # 3채널(BGR) 이미지를 안전하게 비교하기 위해 그레이스케일로 변환 후 절대차 합산
        if img1.ndim == 3:
            img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        if img2.ndim == 3:
            img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(img1, img2)
        return int(np.sum(diff))
        
def main(args=None):
    rclpy.init(args=args)
    node = CameraBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
