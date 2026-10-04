import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory('exoskeleton')
    urdf_path = os.path.join(share, 'urdf', 'exoskeleton.urdf')
    rviz_path = os.path.join(share, 'rviz', 'exoskeleton.rviz')
    config_path = os.path.join(share, 'config', 'hardware.yaml')

    with open(urdf_path, 'r', encoding='utf-8') as handle:
        robot_description = handle.read()

    return LaunchDescription([
        DeclareLaunchArgument('esp32_host', default_value='192.168.0.173'),
        DeclareLaunchArgument('esp32_port', default_value='80'),
        DeclareLaunchArgument('rviz', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('rvizconfig', default_value=rviz_path),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
        ),
        Node(
            package='exoskeleton',
            executable='hardware_bridge',
            name='hardware_bridge',
            parameters=[{
                'config_file': config_path,
                'esp32_host': LaunchConfiguration('esp32_host'),
                'esp32_port': LaunchConfiguration('esp32_port'),
            }],
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', LaunchConfiguration('rvizconfig')],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])
