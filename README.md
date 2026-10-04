# Exoskeleton

URDF and meshes for an exoskeleton hand, plus ESP32 WebUI sketch and ROS 2 bridge.

## ESP32 Sketch
- Upload `sketch_sep14a_copy_20261004192038.ino` to ESP32 with Adafruit PWMServoDriver library.
- Set Wi-Fi SSID/PASSWORD in sketch (KPS/kachra.polash). 
- Gets IP (serial monitor). Web UI at `http://<ESP32-IP>/` with sliders for 5 fingers, Center/Auto/Stop.
- API:
  - `GET /command?cmd=CENTER` -> center all
  - `GET /command?cmd=AUTO` -> start auto cycle
  - `GET /command?cmd=STOP` -> stop auto cycle
  - `GET /command?cmd=S1:90` -> set servo 1 to 90° (S1-S5, degrees clamped to per-servo limits)
  - `GET /position` -> returns JSON angles + auto state

Servo mapping (sketch): S1 thumb-like (80-180), S2 index/MCP (0-100), S3 (80-180), S4 (30-130), S5 (80-180). Tune to your hardware.

## ROS 2 (Humble)
Launch visualization (no hardware):
```bash
ros2 launch exoskeleton exoskeleton.launch.py gui:=true
```

Launch with real ESP32 hand:
```bash
ros2 launch exoskeleton exoskeleton_with_hand.launch.py use_real_hardware:=true esp32_ip:=<ESP32-IP> rate:=10.0
```

Bridge subscribes to `/joint_states` and maps: `thumb_joint1->S1`, `index_joint1->S2`, `finger2_joint1->S3`, `finger3_joint1->S4`, `finger4_joint1->S5`. Joints use URDF ranges ~[-1.2,1.6] rad mapped linearly to servo degrees (with per-servo clamps). Extend mapping in `scripts/esp32_hand_bridge.py` if you want to drive all phalanges.
