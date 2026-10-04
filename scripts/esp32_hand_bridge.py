#!/usr/bin/env python3

import math
import time
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class ESP32HandBridge(Node):
    def __init__(self):
        super().__init__('esp32_hand_bridge')

        # Params
        self.declare_parameter('esp32_ip', '192.168.0.100')
        self.declare_parameter('rate', 10.0)  # Hz
        self.declare_parameter('timeout', 1.0)  # seconds

        # Servo mapping (URDF joint name -> (servo_num, rad_min, rad_max, invert, clamp_min_deg, clamp_max_deg))
        # From sketch: S1-5 with limits: S1 80-180, S2 0-100, S3 80-180, S4 30-130, S5 80-180
        # Hand joints (approx URDF): thumb_joint1,2,3; index_joint1,2,3; finger2_joint1,2,3; finger3_joint1,2,3; finger4_joint1,2,3
        # Assigning 5 servos to 5 primary MCP/base joints as a starting safe map
        self.declare_parameter('mapping', [
            # joint name, servo number, rad_min, rad_max, invert (True if -rad maps to +deg)
            ['thumb_joint1', 1, -1.2, 1.6, False],
            ['index_joint1', 2, -1.2, 1.6, False],
            ['finger2_joint1', 3, -1.2, 1.6, False],
            ['finger3_joint1', 4, -1.2, 1.6, False],
            ['finger4_joint1', 5, -1.2, 1.6, False],
        ])

        self.esp32_ip = self.get_parameter('esp32_ip').get_parameter_value().string_value
        self.rate_hz = self.get_parameter('rate').get_parameter_value().double_value
        self.timeout = self.get_parameter('timeout').get_parameter_value().double_value
        mapping_raw = self.get_parameter('mapping').get_parameter_value()

        # Parse mapping
        self.mapping = []
        try:
            # rclpy may return list of lists of strings/ints
            for m in mapping_raw:
                if len(m) >= 5:
                    self.mapping.append({
                        'joint': str(m[0]),
                        'servo': int(m[1]),
                        'rmin': float(m[2]),
                        'rmax': float(m[3]),
                        'invert': bool(m[4]) if len(m) > 4 else False,
                    })
        except Exception as e:
            self.get_logger().warn(f'Failed to parse mapping, using defaults: {e}')
            self.mapping = [
                {'joint': 'thumb_joint1', 'servo': 1, 'rmin': -1.2, 'rmax': 1.6, 'invert': False},
                {'joint': 'index_joint1', 'servo': 2, 'rmin': -1.2, 'rmax': 1.6, 'invert': False},
                {'joint': 'finger2_joint1', 'servo': 3, 'rmin': -1.2, 'rmax': 1.6, 'invert': False},
                {'joint': 'finger3_joint1', 'servo': 4, 'rmin': -1.2, 'rmax': 1.6, 'invert': False},
                {'joint': 'finger4_joint1', 'servo': 5, 'rmin': -1.2, 'rmax': 1.6, 'invert': False},
            ]

        # Servo limits (deg) from sketch
        self.servo_limits = {
            1: (80, 180),
            2: (0, 100),
            3: (80, 180),
            4: (30, 130),
            5: (80, 180),
        }

        self.joint_sub = self.create_subscription(JointState, '/joint_states', self.joint_cb, 10)
        self.timer = self.create_timer(1.0 / self.rate_hz, self.timer_cb) if self.rate_hz > 0 else None

        self.last_cmd = None
        self.last_send = 0.0
        self.get_logger().info(f'ESP32 hand bridge ready: ip={self.esp32_ip}, rate={self.rate_hz}Hz, {len(self.mapping)} joints mapped')

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
        deg_mid = 90.0
        # rough linear map from joint span to 0-180 around center? simpler: map -1.2..1.6 rad to 0..180 with optional invert
        deg = 0.0 + t * 180.0
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
                _ = resp.read()
            return True
        except (URLError, HTTPError) as e:
            self.get_logger().warn(f'Failed to send {url}: {e}')
            return False
        except Exception as e:
            self.get_logger().warn(f'Error sending servo: {e}')
            return False

    def joint_cb(self, msg: JointState):
        name_to_pos = {n: p for n, p in zip(msg.name, msg.position)}

        now = time.time()
        # Throttle individual sends? send on timer by collecting targets
        self.targets = {}
        for m in self.mapping:
            jn = m['joint']
            if jn in name_to_pos:
                rad = name_to_pos[jn]
                deg = self.rad_to_deg(rad, m['rmin'], m['rmax'], invert=m['invert'])
                self.targets[m['servo']] = deg

    def timer_cb(self):
        if not hasattr(self, 'targets') or not self.targets:
            return
        now = time.time()
        if now - self.last_send < (1.0 / max(1.0, self.rate_hz) - 0.001):
            pass
        for s, d in self.targets.items():
            self.send_servo(s, d)
        self.last_send = now
