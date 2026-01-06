import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
import sys

class MotorPublisher(Node):
    def __init__(self):
        super().__init__('motor_publisher')
        
        # 1. Publisher 생성 (토픽 이름이 Subscriber와 같아야함: /set_position_array)
        self.publihser_ = self.create_publisher(
            Int32MultiArray, 
            'set_position_array', 
            10)
        self.get_logger().info('⌨️ 키보드 제어 노드가 시작되었습니다!')

    def send_command(self, positions):
        """입력받은 위치 리스트를 퍼블리시하는 함수"""
        msg = Int32MultiArray()
        msg.data = positions
        self.publihser_.publish(msg)
        self.get_logger().info(f'📤 명령 전송: {positions}')





def main(args=None):
    rclpy.init(args=args)
    node = MotorPublisher()
    
    try:
        #무한루프
        while rclpy.ok():
            print("\n"+ "="*40)
            print("모터 3개의 위치를 띄어쓰기로 구분해 입력하세요(0~1024)\nㄷ")
            print("종료하려면 'q' 또는 'exit' 입력")
            user_input = input("입력 > ")

            #종료 조건
            if user_input.lower() in ['q', 'exit']:
                break
                
            try:
                # 1. 문자열을 숫자로 변환 (얘: "500 5512 600" -> [500, 512, 600])
                pos_list = [int(x) for x in user_input.split()]

                # 2. 데이터 개수 확인 (모터가 3개라 가정)
                if len(pos_list) != 3:
                    print(f"⚠️ 에러: 숫자는 3개가 필요합니다. (입력된 개수: {len(pos_list)})")
                    continue

                # 3. 데이터 범위 확인 
                if any(p < 0 or p > 1023 for p in pos_list):
                    print("⚠️ 에러: 값은 0에서 1023 사이여야 합니다.")
                    continue

                # 4. 명령 전송
                node.send_command(pos_list)

            except ValueError:
                print("⚠️ 에러: 숫자만 입력해주세요.")
        
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main