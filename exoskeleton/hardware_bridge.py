import json
import math
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool
from std_srvs.srv import SetBool, Trigger


DEG_PER_RAD = 180.0 / math.pi
RAD_PER_DEG = math.pi / 180.0


def default_config_path():
    share = get_package_share_directory('exoskeleton')
    return str(Path(share) / 'config' / 'hardware.yaml')


class HardwareBridge(Node):
    def __init__(self):
        super().__init__('hardware_bridge')

        self.declare_parameter('config_file', default_config_path())
        self.declare_parameter('esp32_host', '192.168.0.173')
        self.declare_parameter('esp32_port', '80')
        self.declare_parameter('poll_hz', 20.0)
        self.declare_parameter('command_hz', 20.0)
        self.declare_parameter('request_timeout_sec', 0.25)
        self.declare_parameter('center_deg', 90.0)
        self.declare_parameter('invert', False)

        self._load_servo_map()

        self.host = self.get_parameter('esp32_host').get_parameter_value().string_value
        self.port = int(str(self.get_parameter('esp32_port').value))
        self.timeout = float(self.get_parameter('request_timeout_sec').value)
        self.center_deg = float(self.get_parameter('center_deg').value)
        self.invert = bool(self.get_parameter('invert').value)
        poll_hz = max(1.0, float(self.get_parameter('poll_hz').value))
        command_hz = max(1.0, float(self.get_parameter('command_hz').value))

        self._http_lock = threading.Lock()
        self._cmd_lock = threading.Lock()
        self._pending_deg = {}
        self._last_sent_deg = {}
        self._auto_mode = False
        self._connected = False
        self._angles_deg = [self.center_deg] * 5

        self.joint_pub = self.create_publisher(JointState, 'joint_states', 10)
        self.connected_pub = self.create_publisher(Bool, 'exoskeleton/esp32_connected', 10)
        self.auto_pub = self.create_publisher(Bool, 'exoskeleton/auto_mode', 10)

        self.create_subscription(JointState, 'exoskeleton/command', self._on_command, 10)
        self.create_service(Trigger, 'exoskeleton/center', self._on_center)
        self.create_service(Trigger, 'exoskeleton/stop', self._on_stop)
        self.create_service(SetBool, 'exoskeleton/auto', self._on_auto)

        self.create_timer(1.0 / poll_hz, self._poll_timer)
        self.create_timer(1.0 / command_hz, self._flush_commands)

        self.get_logger().info(
            'ESP32 bridge ready at http://%s:%d  thumb=servo1' % (self.host, self.port)
        )

    def _load_servo_map(self):
        config_file = self.get_parameter('config_file').get_parameter_value().string_value
        with open(config_file, 'r', encoding='utf-8') as handle:
            raw = yaml.safe_load(handle)

        params = raw.get('hardware_bridge', {}).get('ros__parameters', raw)
        servos = params.get('servos', [])
        if len(servos) != 5:
            raise RuntimeError('hardware.yaml must define exactly 5 servos')

        self.servos = sorted(servos, key=lambda item: int(item['id']))
        self.servo_by_joint = {item['driven_joint']: item for item in self.servos}

    def _base_url(self):
        return 'http://%s:%d' % (self.host, self.port)

    def _http_get(self, path):
        url = self._base_url() + path
        request = urllib.request.Request(url, method='GET')
        with self._http_lock:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.read().decode('utf-8')

    def _send_command(self, cmd):
        query = urllib.parse.urlencode({'cmd': cmd})
        return self._http_get('/command?' + query)

    def deg_to_rad(self, deg):
        offset = float(deg) - self.center_deg
        if self.invert:
            offset = -offset
        return offset * RAD_PER_DEG

    def rad_to_deg(self, rad):
        offset = float(rad) * DEG_PER_RAD
        if self.invert:
            offset = -offset
        return self.center_deg + offset

    def _clamp_deg(self, servo, deg):
        return max(int(servo['min_deg']), min(int(servo['max_deg']), int(round(deg))))

    def _build_joint_state(self, stamp):
        names = []
        positions = []
        for servo, deg in zip(self.servos, self._angles_deg):
            driven = self.deg_to_rad(deg)
            names.append(servo['driven_joint'])
            positions.append(driven)
            for joint_name, multiplier in zip(
                servo.get('mimic_joints', []),
                servo.get('mimic_multipliers', []),
            ):
                names.append(joint_name)
                positions.append(driven * float(multiplier))

        msg = JointState()
        msg.header.stamp = stamp
        msg.name = names
        msg.position = positions
        return msg

    def _poll_timer(self):
        try:
            data = json.loads(self._http_get('/position'))
            angles = data.get('angles', [])
            if not isinstance(angles, list) or len(angles) != 5:
                raise ValueError('invalid /position payload')
            self._angles_deg = [float(value) for value in angles]
            self._auto_mode = bool(data.get('auto', False))
            self._connected = True
        except (urllib.error.URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as exc:
            self._connected = False
            self.get_logger().warn('ESP32 poll failed: %s' % exc, throttle_duration_sec=2.0)

        now = self.get_clock().now().to_msg()
        self.joint_pub.publish(self._build_joint_state(now))
        self.connected_pub.publish(Bool(data=self._connected))
        self.auto_pub.publish(Bool(data=self._auto_mode))

    def _on_command(self, msg: JointState):
        if self._auto_mode:
            self.get_logger().warn(
                'Ignoring command while AUTO is running',
                throttle_duration_sec=1.0,
            )
            return

        with self._cmd_lock:
            for name, position in zip(msg.name, msg.position):
                servo = self.servo_by_joint.get(name)
                if servo is None:
                    continue
                deg = self._clamp_deg(servo, self.rad_to_deg(position))
                self._pending_deg[int(servo['id'])] = deg

    def _flush_commands(self):
        if self._auto_mode:
            return

        with self._cmd_lock:
            pending = dict(self._pending_deg)
            self._pending_deg.clear()

        for servo_id, deg in pending.items():
            if self._last_sent_deg.get(servo_id) == deg:
                continue
            try:
                self._send_command('S%d:%d' % (servo_id, deg))
                self._last_sent_deg[servo_id] = deg
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                self.get_logger().warn('Send S%d:%d failed: %s' % (servo_id, deg, exc))
                with self._cmd_lock:
                    self._pending_deg.setdefault(servo_id, deg)

    def _on_center(self, _request, response):
        try:
            self._send_command('CENTER')
            response.success = True
            response.message = 'CENTERED'
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            response.success = False
            response.message = str(exc)
        return response

    def _on_stop(self, _request, response):
        try:
            self._send_command('STOP')
            self._auto_mode = False
            response.success = True
            response.message = 'AUTO_STOPPED'
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            response.success = False
            response.message = str(exc)
        return response

    def _on_auto(self, request, response):
        cmd = 'AUTO' if request.data else 'STOP'
        try:
            self._send_command(cmd)
            self._auto_mode = bool(request.data)
            response.success = True
            response.message = cmd
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            response.success = False
            response.message = str(exc)
        return response


def main(args=None):
    rclpy.init(args=args)
    node = HardwareBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
