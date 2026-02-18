import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray


# 체스판 위치 토크 변환 코드
class pos_torque_trans(Node):
    def __init__(self):
        super().__init__('calculator')

        # 로봇 팔 길이 (cm 단위)
        self.L1 = 25.18 #어께-팔꿈치
        self.L2 = 20.05#팔꿈치-손

        #다이나믹셀 설정 (0~1023, 512가 중앙, 1단위 당 0.29도)
        self.CENTER_VAL = 512
        self.DEG_PER_UNIT = 0.293

        # 자로 크기 입력
        self.SQUARE_SIZE_Y = 4.25 # 체스 한 칸의 가로4.25
        self.SQUARE_SIZE_X = 4.20 # 체스 한 칸의 세로길이4.2

        # 로봇 어깨 중심(0,0)에서 체스판의 a1까지의 길이
        self.OFFSET_X = 11.05 # 로봇 앞쪽으로 얼마나 먼지 2.55 + 8.5
        self.OFFSET_Y = -17 #로봇 중심선에서 얼마나 좌/우로 치우쳤는지

    
        self.publisher_ = self.create_publisher(
            Int32MultiArray,
            'set_position_array',
            10)
        
    # 계산기
    def calculate(self):
        
        while rclpy.ok():
            square_name = input("목표 칸 입력 (예: e2, 종료는 q) > ")     

            col_idx = ( ord(square_name[0]) - ord('a') )
            row_idx = 7 - ( int(square_name[1]) - 1 )

            # 공식: 시작점 + (칸 개수 * 칸 크기) + (칸 크기 / 2)
            x = self.OFFSET_X + (row_idx * self.SQUARE_SIZE_X) + (self.SQUARE_SIZE_X / 2)
            y = self.OFFSET_Y + (col_idx * self.SQUARE_SIZE_Y) + (self.SQUARE_SIZE_Y / 2)

            print(f"목표 좌표: x={x: .2f}cm, y={y: .2f}cm")
            
            # 코사인 법칙을 이용한 역기구학
            cos_angle2 = (x**2 + y**2 - self.L1**2 - self.L2**2) / (2 * self.L1 * self.L2)
            cos_angle2 = max(-1.0, min(1.0, cos_angle2))

            # 2번 모터(팔꿈치)의 각도(라디안)
            theta2 = math.acos(cos_angle2)

            # 1번 모터(어깨)의 각도(라디안)
            #alpha : 원점과 목표점을 잇는 직선의 각도
            #beta : 그 직선과 첫 번째 팔 사이의 각도
            alpha = math.atan2(y, x)
            beta = math.acos((x**2 + y**2 + self.L1**2 - self.L2**2) / (2*self.L1*math.sqrt(x**2 + y**2)))

            theta1 = alpha - beta # 오른팔
        
            # 라디안 -> 도(Degree)로 변환
            # deg: 0~150?
            deg1 = math.degrees(theta1) - 45
            deg2 = math.degrees(theta2)
            print(f"계산된 각도: 모터1: {deg1: .2f}도, 모터2: {deg2: .2f}도")

            # 512를 0도로 기준 잡고 모터변환
            val1 = int(round(self.CENTER_VAL + (deg1 / self.DEG_PER_UNIT)))
            val2 = int(round(self.CENTER_VAL + (deg2 / self.DEG_PER_UNIT)))

            msg = Int32MultiArray()
            msg.data = [810, val1, val2, 416]
            self.publisher_.publish(msg)
  

def main(args=None):
    rclpy.init(args=args)
    node = pos_torque_trans()

    try:
        node.calculate()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

   