#!/usr/bin/env python3
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


import time
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class ESP32HandBridge(Node):
    def __init__(self):
        super().__init__('esp32_hand_bridge')

        self.declare_parameter('esp32_ip', '192.168.0.100')
        self.declare_parameter('rate', 10.0)
        self.declare_parameter('timeout', 1.0)

        self.esp32_ip = (
            self.get_parameter('esp32_ip').get_parameter_value().string_value
        )
        self.rate_hz = (
            self.get_parameter('rate').get_parameter_value().double_value
        )
        self.timeout = (
            self.get_parameter('timeout').get_parameter_value().double_value
        )

        self.mapping = [
            {
                'joint': 'thumb_joint1',
                'servo': 1,
                'rmin': -1.2,
                'rmax': 1.6,
                'invert': False,
            },
            {
                'joint': 'index_joint1',
                'servo': 2,
                'rmin': -1.2,
                'rmax': 1.6,
                'invert': False,
            },
            {
                'joint': 'finger2_joint1',
                'servo': 3,
                'rmin': -1.2,
                'rmax': 1.6,
                'invert': False,
            },
            {
                'joint': 'finger3_joint1',
                'servo': 4,
                'rmin': -1.2,
                'rmax': 1.6,
                'invert': False,
            },
            {
                'joint': 'finger4_joint1',
                'servo': 5,
                'rmin': -1.2,
                'rmax': 1.6,
                'invert': False,
            },
        ]

        self.servo_limits = {
            1: (80, 180),
            2: (0, 100),
            3: (80, 180),
            4: (30, 130),
            5: (80, 180),
        }

        self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_cb,
            10
        )
        self.create_timer(1.0 / self.rate_hz, self.timer_cb)
        self.targets = {}
        self.last_send = 0.0
        self.get_logger().info('bridge ready')

    def rad_to_deg(self, rad, rmin, rmax, invert=False):
        if rad < rmin:
            rad = rmin
        if rad > rmax:
            rad = rmax
        span = rmax - rmin
        if span <= 0:
            t = 0.5
        else:
            t = (rad - rmin) / span
        deg = t * 180.0
        if invert:
            deg = 180.0 - deg
        return deg

    def send_servo(self, servo_num, deg):
        dmin, dmax = self.servo_limits.get(servo_num, (0, 180))
        if deg < dmin:
            deg = dmin
        if deg > dmax:
            deg = dmax
        deg_int = int(round(deg))
        url = f'http://{self.esp32_ip}/command?cmd=S{servo_num}:{deg_int}'
        try:
            with urlopen(url, timeout=self.timeout) as resp:
                resp.read()
            return True
        except (URLError, HTTPError) as e:
            self.get_logger().warn(f'Failed to send: {e}')
            return False

    def joint_cb(self, msg: JointState):
        name_to_pos = dict(zip(msg.name, msg.position))
        targets = {}
        for m in self.mapping:
            jn = m['joint']
            if jn in name_to_pos:
                rad = name_to_pos[jn]
                deg = self.rad_to_deg(rad, m['rmin'], m['rmax'], m['invert'])
                targets[m['servo']] = deg
        self.targets = targets

    def timer_cb(self):
        if not self.targets:
            return
        for s, d in self.targets.items():
            self.send_servo(s, d)
        self.last_send = time.time()


def main(args=None):
    rclpy.init(args=args)
    node = ESP32HandBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
