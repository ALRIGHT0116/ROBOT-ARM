from rclpy.node import Node
from sensor_msgs.msg import Image
import rclpy
from utils.calibration import Calibration
import numpy as np
from std_msgs.msg import String

class CameraBridgeNode(Node):    
    def __init__(self):
        super().__init__('camera_bridge_node')
        self.get_logger().info('Camera Bridge Node has been started.')
        #camera_node에서 토픽 받아옴
        self.camera_sub = self.create_subscription(Image, 'raw_camera_image', self.camera_callback, 10)
        #chess_timer에서 토픽 받아옴   
        self.timer_sub = self.create_subscription(int, 'camera_timer', self.timer_callback, 10)
        self.calibration = Calibration()
        #chess_brain으로 토픽 보냄
        self.notatation_pub = self.create_publisher(String, 'notation',10)

    def camera_callback(self, msg):
        self.raw_image = msg.data
        
        
    def timer_callback(self, msg):
        self.player_phase = msg.data
        self.get_logger().info('Timer callback received message: {}'.format(msg.data))
        if self.player_phase == 1:
            self.cal_image_before = self.calibration.calibrate(self.raw_image)
            self.cutted_image_before = self.cut_image(self.cal_image_before)

        elif self.player_phase == 2:
            self.raw_image_after = self.calibration.calibrate(self.raw_image)
            self.cutted_image_after = self.cut_image(self.raw_image_after)
        
        else: pass
    
    def cut_image(self, image):
        cutted_image = [[0 for _ in range(8)] for _ in range(8)]
        cutted_image_width = int(len(image[0]) // 8)
        cutted_image_height = int(len(image) // 8)
        for i in range (8):
            for j in range(8):
                cutted_image[i][j] = image[i*cutted_image_width:(i+1)*cutted_image_width, j*cutted_image_height:(j+1)*cutted_image_height]
        return cutted_image

    def compare_images(self):
        differences = np.matrix([[0 for _ in range(8)] for _ in range(8)])
        for i in range(8):
            for j in range(8):
                differences[i][j] = self.compute_difference(self.cutted_image_before[i][j], self.cutted_image_after[i][j])
            # 2. 행렬을 1차원 배열로 펴기 (Flatten)
        flat_diff = differences.flatten()

        # 3. 값이 큰 순서대로 정렬하여 인덱스 4개 뽑기 (argsort 사용)
        # argsort는 작은 순서대로 정렬하므로 [::-1]로 뒤집어서 큰 값이 먼저 오게 함
        top_6_indices = np.argsort(flat_diff)[::-1][:6]

        # 4. 1차원 인덱스를 다시 (행, 열) 좌표로 변환 (unravel_index)
        top_indices = []
        top_coords = []
        print("=== 변화량 Top ===")
        max_mean = ( top_6_indices[0] + top_6_indices[1]) / 2
        min_mean = ( top_6_indices[4] + top_6_indices[5]) / 2
        middle_mean = ( top_6_indices[2] + top_6_indices[3] ) / 2

        if max_mean - middle_mean > middle_mean - min_mean:
            # 캐슬링이 아니라면 상위 2개 선택
            top_indices = top_6_indices[:2]
        else:
            # 캐슬링이라면 상위 4개 선택
            top_indices = top_6_indices[:4]

        for idx in top_indices:
            # unravel_index: 1차원 인덱스(0~63)를 (행, 열)로 바꿔줌
            row, col = np.unravel_index(idx, differences.shape)
            value = differences[row, col]
            
            # 체스 좌표 변환 (예: (0,0) -> a1)
            chess_notation = f"{chr(ord('a') + col)}{row + 1}"
            
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
             
            if var1 > var2:
                commend_coords = f"{first['name']}{second['name']}"
            else:
                commend_coords = f"{second['name']}{first['name']}"     

        elif len(top_coords) == 4:  
            # 어떤 캐슬링인지 판별
            if "h1" in top_coords:
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
        # 이미지 간의 차이를 계산하는 로직 구현
        difference = 0
        for i in range(len(img1)):
            for j in range(len(img1[0])):
                difference += abs(int(img1[i][j]) - int(img2[i][j]))
        return difference
        
def main(args=None):
    rclpy.init(args=args)
    node = CameraBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()