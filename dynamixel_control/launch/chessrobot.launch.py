from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # chess_brain 노드 실행
    node_1 = Node(
        package='dynamixel_control', #패키지 이름 = dynamixel_control
        executable='chess_brain',   #실행 파일 이름 - setup.py에 정의된 이름
        name='chess_brain_node',      #노드 이름 - 임의로 지정 가능
        output='screen',            #터미널에 출력한다는 의미
    )
    node_2 = Node(
        package='dynamixel_control',
        executable='chess_mapper',
        name='chess_mapper_node',
        output='screen',
    )
    node_3 = Node(
        package='dynamixel_control',
        executable='motor_node',
        name='motor_node_node',
        output='screen',   
    )
    node_4 = Node(
        package='dynamixel_control',       
        executable='motor_publisher',
        name='motor_publisher_node',
        output='screen',
    )


    return LaunchDescription([
        node_1,
        node_2,
        node_3,
        node_4
    ])