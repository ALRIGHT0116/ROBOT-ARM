import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'dynamixel_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share',package_name,'launch'), glob(os.path.join('launch','*launch.[pxy][yma]*'))),
        ('share/' + package_name + '/urdf', glob('urdf/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='shin',
    maintainer_email='shin@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'motor_node = dynamixel_control.main.motor_node:main',
            'motor_publisher = dynamixel_control.main.motor_publisher:main',
            'chess_brain = dynamixel_control.main.chess_brain:main',
            'chess_brain_test = dynamixel_control.main.chess_brain_test:main',
            'chess_mapper = dynamixel_control.main.chess_mapper:main',
            'rviz_bridge = dynamixel_control.main.rviz_bridge:main',
            'camera_node = dynamixel_control.vision.camera_node:main',
            'camera__bridge_node = dynamixel_control.vision.camera_bridge_node:main',
            'mapper_test = dynamixel_control.main.mapper_test:main',
        ],
    },
)
