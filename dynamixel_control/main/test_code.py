"""Simple IK test harness for chess_mapper.pos_torque_trans

This script instantiates the `pos_torque_trans` node, calls `calculate()`
for sample squares, simulates `get_motor_angle()` for normal and castling
moves, captures published messages, and performs basic assertions.
"""

import sys
import rclpy
from std_msgs.msg import String
import math

from chess_mapper import pos_torque_trans


def run_checks():
    rclpy.init()
    node = pos_torque_trans()

    # Capture published messages instead of sending them over ROS
    published = []
    node.publisher_.publish = lambda msg: published.append(msg.data)

    try:
        squares = ['a1', 'c2', 'b4', 'd3']
        print('Running calculate() on sample squares:')
        for s in squares:
            v1, v2 = node.calculate(s)
            print(f'  {s} -> ({v1}, {v2})')
            assert isinstance(v1, int) and isinstance(v2, int)
            assert 0 <= v1 <= 1023 and 0 <= v2 <= 1023
            assert not (v1 == 512 and v2 == 512), f'IK returned error values for {s}'
            v1_rad = (v1 - 512) * (300.0 / 1023) * (3.14159265 / 180)
            assert -2.61799 <= v1_rad <= 2.61799, f'Angle out of range for {s}'
            v2_rad = (v2 - 512) * (300.0 / 1023) * (3.14159265 / 180)
            assert -2.61799 <= v2_rad <= 2.61799, f'Angle out of range for {s}'
            x = 13.8 * math.cos(v1_rad) + 14.0 * math.cos(v1_rad + v2_rad)
            y = 13.8 * math.sin(v1_rad) + 14.0 * math.sin(v1_rad + v2_rad)
            print (f'    FK -> (x: {x:.2f} cm, y: {y:.2f} cm)')

        print('\nTesting get_motor_angle() for a normal move:')
        msg = String()
        msg.data = 'e2e4 normal'
        node.get_motor_angle(msg)
        print('  Published:', published[-1])

        print('\nTesting get_motor_angle() for king-side castling:')
        msg2 = String()
        msg2.data = 'e1g1 king_castling'
        node.get_motor_angle(msg2)
        print('  Published:', published[-1])

        print('\nAll checks passed.')

    except AssertionError as e:
        print('Assertion failed:', e)
        return 1
    except Exception as e:
        print('Error during checks:', e)
        return 2
    finally:
        node.destroy_node()
        rclpy.shutdown()

    return 0


if __name__ == '__main__':
    sys.exit(run_checks())