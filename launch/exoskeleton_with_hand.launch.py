# Copyright 2026 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    ld = LaunchDescription()

    default_model_path = '/home/rahat/exoskeleton/urdf/exoskeleton.urdf'
    default_rviz_config_path = '/home/rahat/exoskeleton/rviz/exoskeleton.rviz'

    ld.add_action(
        DeclareLaunchArgument(
            name='gui',
            default_value='true',
            choices=['true', 'false'],
            description='Flag to enable joint_state_publisher_gui',
        )
    )
    ld.add_action(
        DeclareLaunchArgument(
            name='model',
            default_value=default_model_path,
            description='Path to robot urdf file',
        )
    )
    ld.add_action(
        DeclareLaunchArgument(
            name='rvizconfig',
            default_value=default_rviz_config_path,
            description='Absolute path to rviz config file',
        )
    )
    ld.add_action(
        DeclareLaunchArgument(
            name='use_real_hardware',
            default_value='false',
            choices=['true', 'false'],
            description='Enable ESP32 bridge to real hand',
        )
    )
    ld.add_action(
        DeclareLaunchArgument(
            name='esp32_ip',
            default_value='192.168.0.100',
            description='ESP32 IP address on Wi-Fi',
        )
    )
    ld.add_action(
        DeclareLaunchArgument(
            name='rate',
            default_value='10.0',
            description='Bridge update rate Hz',
        )
    )

    robot_description_content = ParameterValue(
        Command(['xacro ', LaunchConfiguration('model')]), value_type=str
    )

    ld.add_action(
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description_content}],
        )
    )

    ld.add_action(
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            condition=IfCondition(LaunchConfiguration('gui')),
        )
    )

    ld.add_action(
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', LaunchConfiguration('rvizconfig')],
        )
    )

    ld.add_action(
        Node(
            package='exoskeleton',
            executable='esp32_hand_bridge.py',
            condition=IfCondition(LaunchConfiguration('use_real_hardware')),
            parameters=[
                {
                    'esp32_ip': LaunchConfiguration('esp32_ip'),
                    'rate': LaunchConfiguration('rate'),
                }
            ],
            output='screen',
        )
    )

    return ld
