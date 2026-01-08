import rclpy
from rclpy.node import Node
import chess
import chess.engine
from std_msgs.msg import String

# 스톡피쉬 엔진 경로 (터미널 which stockfish로 확인 가능)
STOCKFISH_PATH = "/usr/games/stockfish"

class ChessBrain(Node):
    def __init__(self):
        super().__init__('chess_brain')

        self.get_logger().info(' 체스 AI 두뇌 가동 중...')

        self.move_publisher = self.create_publisher(String, 'next_move', 10)

        # 1. 체스보드 생성(초기화)
        self.board = chess.Board()

        # 2. 스톡피쉬 엔진 연결
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
            self.engine.configure({"Skill Level": 20})
            self.get_logger().info(' 스톡피쉬 엔진 연결 성공!')
        except FileNotFoundError:
            self.get_logger().error(f' 스톡피쉬를 찾을 수 없습니다. 경로 확인: {STOCKFISH_PATH}')
            #sudo apt install stockfish했는지 확인 필요
            return
        
    def play_game(self):
        # 게임 진행하는 루프
        print("\n"+ "="*40)
        print(" [ 체스 게임 시작 ] ")
        print("당신은 백(white)입니다. 좌표를 입력하세요 예) e2e4 ")
        print("종료하려면 'q'를 입력하세요")
        print("="*40)

        while rclpy.ok() and not self.board.is_game_over():
            # --- 1. 현재 보드 상태 출력 ---
            print("\n" + str(self.board))

            # --- 2. 사용자 입력 (HUMAN MOVE) ---
            user_move_str = input("\n당신의 수 (예: e2e4) > ")

            if user_move_str.lower() == 'q' :
                break

            try: 
                # 입력받은 문자 확인
                move = chess.Move.from_uci(user_move_str)
                if move in self.board.legal_moves:
                    self.board.push(move) #보드에 수 적용
                else:
                    print("잘못된 수 입니다. 다시 작성해주세요")
                    continue
            except:
                print(" 잘못된 입력 형식입니다. (예: e2e4)")
                continue

            # 게임 종료 체크
            if self.board.is_game_over():
                break

            # --- 3. AI 생각 (Stockfish Move) ---
            print("\n AI가 생각 중입니다...")

            
            #0.1초 동안 생각하고 가장 좋은 수 두기(시간 조절 가능)
            result = self.engine.play(self.board, chess.engine.Limit(time=0.5))
            ai_move = result.move
            ai_move_str = ai_move.uci() # ai_move의 string 버전

            is_capture = self.board.is_capture(ai_move)
            is_castling = self.board.is_castling(ai_move)
            move_type = "move"
            if is_capture:
                move_type = "capture"
            elif is_castling:
                # e > g king side / e > c queen side
                if ai_move_str[2] == 'g':
                    move_type = "king_castling"
                else:
                    move_type = "queen_castling"
            if len(ai_move_str) == 5:
                move_type = 'promotion'

            msg = String()
            msg.data = f"{ai_move_str}:{move_type}"
            self.board.push(ai_move) #AI 수 적용
            print(f" AI의 선택: {ai_move}")
            self.move_publisher.publish(msg)
            self.get_logger().info(f'이동 명령 전송: {ai_move}(타입: {move_type})')


        print("\n게임 종료!")
        print(self.board.outcome())

    def close_engine(self):
        if hasattr(self, 'engine'):
            self.engine.quit()
            
    
def main(args=None):
    rclpy.init(args=args)
    node = ChessBrain()

    try:
        if hasattr(node, 'engine'):
            node.play_game()
    except KeyboardInterrupt:
        pass
    finally:
        node.close_engine()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()