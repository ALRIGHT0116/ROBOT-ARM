import cv2
import time
import numpy as np
import rclpy

from rclpy.node import Node

# 전역 변수 설정
width, height = 800, 600
p1_time, p2_time = 600, 600  # 10 minutes each
current_player = 0 # 0: no turn, 1: Player1, 2: Player2
last_tick = time.time()


class timer(Node):
    def __init__(self):
        super().__init__('chess_timer')
        self.get_logger().info("Chess Timer Node Initialized")
        
        self.timer_pub = self.create_publisher(int, 
                                               'camera_timer', 
                                               10)

    def turn_change(event,x,y,flags,param):
        global current_player, p1_time, p2_time
        if event == cv2.EVENT_LBUTTONDOWN:
            if current_player == 0:
                # 게임 시작 시 왼쪽 클릭 = Player1 턴으로 시작
                current_player = 1
            else:
                # 왼쪽 클릭 = Player2 턴으로 교체
                if x < width // 2:
                    current_player = 2
                # 오른쪽 클릭 = Player1 턴으로 교체
                else:
                    current_player = 1

    def send_playerturn(self, player):
        # camera_bridge_node로 토픽 전송
        msg = int(player)
        self.timer_pub.publish(msg)
        self.get_logger().info(f'Sent turn change action: Player {player}')

        
    # GUI 생성
    cv2.namedWindow("Chess Timer")
    cv2.setMouseCallback("Chess Timer", turn_change)


    prev_player = 0
    while True:
        # 배경
        img = np.zeros((height, width, 3), dtype=np.uint8)
    
        # 시간 업데이트
        now = time.time()
        dt = now - last_tick
        last_tick = now
        
        if current_player == 1 and p1_time > 0:
            p1_time -= dt
        elif current_player == 2 and p2_time > 0:
            p2_time -= dt

        # GUI 설정
        # p1 영역
        p1_color = (0, 255, 0) if current_player == 1 else (200, 200, 200)
        cv2.rectangle(img, (0, 0), (width // 2, height), p1_color, -1 if current_player == 1 else 2)   
        
        # p2 영역
        p2_color = (0, 255, 0) if current_player == 2 else (200, 200, 200)
        cv2.rectangle(img, (width // 2, 0), (width, height), p2_color, -1 if current_player == 2 else 2)

        # 시간 표시
        line_x = 100
        line_y = 300
        line_height = 50

        p1_name = "Challenger"
        p1_current_time = f'{int(p1_time // 60):02d}:{int(p1_time % 60):02d}'

        p2_name = "AI"
        p2_current_time = f'{int(p2_time // 60):02d}:{int(p2_time % 60):02d}'

        cv2.putText(img, p1_name, (line_x, line_y), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        line_y+=line_height
        cv2.putText(img, p1_current_time, (line_x, line_y), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)

        line_y = 300
        cv2.putText(img, p2_name, (line_x + 400, line_y), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        line_y+=line_height
        cv2.putText(img, p2_current_time, (line_x + 400, line_y), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)

        # 출력 및 종료
        cv2.imshow("Chess Timer", img)

        key = cv2.waitKey(10)
        if key == 27:  # ESC 키로 종료
            break   
        elif key == 32:
            if current_player == 0: # 스페이스바로 게임 시작
                current_player = 1
            elif current_player == 1: # 스페이스바로 턴 교체
                current_player = 2
            else:
                current_player = 1 
        
        # 턴 변경 감지 및 액션 전송
        if current_player != prev_player:
            # 게임이 막 시작되었거나(0 -> 1) 턴이 바뀌었을 때
            if current_player != 0:
                send_playerturn(current_player)
            
            # 상태 업데이트 (중요: 한 번만 실행되도록)
            prev_player = current_player
        
    cv2.destroyAllWindows()

def main(args=None):
    rclpy.init(args=args)
    node = timer()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()