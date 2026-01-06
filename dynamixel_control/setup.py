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
            'motor_node = dynamixel_control.motor_node:main',
            'motor_publisher = dynamixel_control.motor_publisher:main',
            'motor_input = dynamixel_control.motor_input_publisher:main',
        ],
    },
)
