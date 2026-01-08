import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32MultiArray
# dynamixel 연결 해서 모터가 가동되는지 알기위한 불러오기
# from dynamixel_workbench_msgs.msg import DynamixelsTateList 
import sys


class MotorPublisher(Node):
    def __init__(self):
        super().__init__('motor_publisher')

        self.is_moving = False
        
        # 1. Publisher 생성 (토픽 이름이 Subscriber와 같아야함: /set_position_array)
        self.publihser_ = self.create_publisher(
            Int32MultiArray, 
            'set_position_array', 
            10)
        self.get_logger().info(' 키보드 제어 노드가 시작되었습니다! ')

        # 2. subscription 생성 chess_mapper.py로부터 motor_torque 토픽을 Int형태로 받음
        self.subscription_ = self.create_subscription(
            String, 
            "motor_torque",
            self.move_callback,
            10)
        
        # 3. is_moving 값을 변화시키기 위해 motor_node.py로부터 is_moving 토픽을 bool형태로 받음
        #ros2 interface show dynamixel_workbench_msgs/msg/DynamixelStateList 이걸로 토픽 형태 확인해야함
        self.status_subscription = self.create_subscription(
            #이거 바꿔야함###############################################
            Int32MultiArray, ##########################################################
            ##########################################################
            "is_moving",
            self.status_callback,
            10
        )
        
    def status_callback(self, is_moving):
        #여러개의 모터 하나라도 움직이면?
        #is_moving.dynamixel_state 이 맞는지는 확인해야함
        moving_status = any(state.moving for state in is_moving.dynamixel_state)
        self.is_moving = moving_status
        
    def motor(self, positions):
        """입력받은 위치 리스트를 퍼블리시하는 함수"""       
        msg = Int32MultiArray()
        msg.data = positions
        self.publihser_.publish(msg)
        self.get_logger().info(f' 명령 전송: {positions}')

    def wait_motor(self):
        while self.is_moving:
        # 중요: 이 코드가 있어야 대기하는 동안에도 다른 메시지를 수신할 수 있습니다.
            rclpy.spin_once(self, timeout_sec=0.1)

    def send_command(self, position):
        self.wait_motor()
        self.motor(position)

    def move_callback(self, msg):
        data_list = msg.data.split(',')
        msg.data = [int(data_list[0]),int(data_list[1]),int(data_list[2]),int(data_list[3]),data_list[4],int(data_list[5]),int(data_list[6]),int(data_list[7]),int(data_list[8])]

        # 기본적인 행동
        if msg.data[4] == 'move':
            # 1. 첫번째 위치 이동
            position = [None, msg.data[0], msg.data[1], None]
            self.send_command(position)
            # 2. 몸통 내리기
            position = [0, msg.data[0], msg.data[1], None]
            self.send_command(position)
            # 3. 그리퍼 닫기
            position = [0, msg.data[0], msg.data[1], 0]
            self.send_command(position)
            # 4. 몸통 올리기
            position = [None, msg.data[0], msg.data[1], 0]
            self.send_command(position)
            # 5. 두번째 위치 이동
            position = [None, msg.data[2], msg.data[3], 0]
            self.send_command(position)
            # 6. 몸통 내리기
            position = [0, msg.data[2], msg.data[3], 0]
            self.send_command(position)  
            # 7. 그리퍼 열기
            position = [0, msg.data[2], msg.data[3], None]
            self.send_command(position)
            # 8. 몸통 올리기
            position = [None, msg.data[2], msg.data[3], None]
            self.send_command(position)
            # 9. 초기 상태 이동
            position = [None, 0, 0, None]
            self.send_command(position)

        elif msg.data[4] == 'capture':
            # 두번째 위치로 이동
            position = [None, msg.data[2], msg.data[3], None]
            self.send_command(position)
            # 몸통내리기
            position = [0, msg.data[0], msg.data[1], None]
            self.send_command(position)
            # 그리퍼 닫기 
            position = [0, msg.data[0], msg.data[1], 0]
            self.send_command(position)
            # 몸통올리기
            position = [None, msg.data[0], msg.data[1], 0]
            self.send_command(position)
            # 버리는 자리 이동
            position = [None, 1023, 1023, 0]
            self.send_command(position)
            # 놓기
            position = [None, 1023, 1023, None]
            self.send_command(position)
            # 1. 첫번째 위치 이동
            position = [None, msg.data[0], msg.data[1], None]
            self.send_command(position)
            # 2. 몸통 내리기
            position = [0, msg.data[0], msg.data[1], None]
            self.send_command(position)
            # 3. 그리퍼 닫기
            position = [0, msg.data[0], msg.data[1], 0]
            self.send_command(position)
            # 4. 몸통 올리기
            position = [None, msg.data[0], msg.data[1], 0]
            self.send_command(position)
            # 5. 두번째 위치 이동
            position = [None, msg.data[2], msg.data[3], 0]
            self.send_command(position)
            # 6. 몸통 내리기
            position = [0, msg.data[2], msg.data[3], 0]
            self.send_command(position)  
            # 7. 그리퍼 열기
            position = [0, msg.data[2], msg.data[3], None]
            self.send_command(position)
            # 8. 몸통 올리기
            position = [None, msg.data[2], msg.data[3], None]
            self.send_command(position)
            # 9. 초기 상태 이동
            position = [None, 0, 0, None]
            self.send_command(position)

        elif msg.data[4] in ['king_castling','queen_castling']:
            # 1. 첫번째 위치 이동
            position = [None, msg.data[0], msg.data[1], None]
            self.send_command(position)
            # 2. 몸통 내리기
            position = [0, msg.data[0], msg.data[1], None]
            self.send_command(position)
            # 3. 그리퍼 닫기
            position = [0, msg.data[0], msg.data[1], 0]
            self.send_command(position)
            # 4. 몸통 올리기
            position = [None, msg.data[0], msg.data[1], 0]
            self.send_command(position)
            # 5. 두번째 위치 이동
            position = [None, msg.data[2], msg.data[3], 0]
            self.send_command(position)
            # 6. 몸통 내리기
            position = [0, msg.data[2], msg.data[3], 0]
            self.send_command(position)  
            # 7. 그리퍼 열기
            position = [0, msg.data[2], msg.data[3], None]
            self.send_command(position)
            # 8. 몸통 올리기
            position = [None, msg.data[2], msg.data[3], None]
            self.send_command(position)
            # 10. 룩 첫번째 위치 이동
            position = [None, msg.data[5], msg.data[6], None]
            self.send_command(position)
            # 11. 몸통 내리기
            position = [0, msg.data[5], msg.data[6], None]
            self.send_command(position)
            # 12. 그리퍼 닫기
            position = [0, msg.data[5], msg.data[6], 0]
            self.send_command(position)
            # 13. 몸통 올리기
            position = [None, msg.data[5], msg.data[6], 0]
            self.send_command(position)
            # 14. 룩 두번째 위치 이동
            position = [None, msg.data[7], msg.data[8], 0]
            self.send_command(position)
            # 15. 몸통 내리기
            position = [0, msg.data[7], msg.data[8], 0]
            self.send_command(position)
            # 16. 그리퍼 열기
            position = [0, msg.data[7], msg.data[8], None]
            self.send_command(position)
            # 17. 몸통 올리기
            position = [None, msg.data[7], msg.data[8], None]
            self.send_command(position)
            # 18. 초기 상태 이동
            position = [None, 0, 0, None]
            self.send_command(position)

        elif msg.data[4] == ':promotion':
            # 1. 첫번째 위치 이동
            position = [None, msg.data[0], msg.data[1], None]
            self.send_command(position)
            # 2. 몸통 내리기
            position = [0, msg.data[0], msg.data[1], None]
            self.send_command(position)
            # 3. 그리퍼 닫기
            position = [0, msg.data[0], msg.data[1], 0]
            self.send_command(position)
            # 4. 몸통 올리기
            position = [None, msg.data[0], msg.data[1], 0]
            self.send_command(position)
            # 5. 두번째 위치 이동
            position = [None, msg.data[2], msg.data[3], 0]
            self.send_command(position)
            # 6. 몸통 내리기
            position = [0, msg.data[2], msg.data[3], 0]
            self.send_command(position)  
            # 7. 그리퍼 열기
            position = [0, msg.data[2], msg.data[3], None]
            self.send_command(position)
            # 8. 몸통 올리기
            position = [None, msg.data[2], msg.data[3], None]
            self.send_command(position)
            # 9. 몸통 내리기
            position = [0, msg.data[2], msg.data[3], None]
            self.send_command(position)
            # 10. 그리퍼 닫기
            position = [0, msg.data[2], msg.data[3], 0]
            self.send_command(position)
            # 11. 몸통 올리기
            position = [None, msg.data[2], msg.data[3], 0]
            self.send_command(position)
            # 12. 버리는 위치로 이동
            position = [None, 1023, 1023, 0]
            self.send_command(position)
            # 13. 놓기
            position = [None, 1023, 1023, None]
            self.send_command(position)

            # 14. 퀸 놓여있는 위치로 이동
            # 이거 퀀 놔둘 위치의 토크값을 알아서 찾아서 바꾸기
            ##########################################################
            position = [None, 10, 10, None]
            self.send_command(position)
            # 15.몸통 내리기
            position = [0, 10, 10, None]
            self.send_command(position)
            # 16. 그리퍼 닫기
            position = [0, 10, 10, 0]
            self.send_command(position)
            # 17. 몸통 올리기
            position = [None, 10, 10, 0]
            self.send_command(position)
            ##########################################################
            # 18. 두번째 위치 이동
            position = [None, msg.data[2], msg.data[3], 0]
            self.send_command(position)
            # 19. 몸통 내리기
            position = [0, msg.data[2], msg.data[3], 0]
            self.send_command(position)  
            # 20. 그리퍼 열기
            position = [0, msg.data[2], msg.data[3], None]
            self.send_command(position)
            # 21. 몸통 올리기
            position = [None, msg.data[2], msg.data[3], None]
            self.send_command(position)
            # 22. 초기 상태로 이동
            position = [None, 0, 0, None]
            self.send_command(position)
            
def main(args=None):
    rclpy.init(args=args)
    node = MotorPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("motorpublisher 노드 종료")
    finally:
        node.destory_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

  
    


    

