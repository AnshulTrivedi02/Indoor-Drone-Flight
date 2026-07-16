#!/usr/bin/env bash
# Launch the full simulation stack in five gnome-terminal tabs.
#
# Usage: ./start_sim.sh [WORLD.sdf]
#
# WORLD is a filename in ~/ardupilot_gazebo/worlds/ (default: iris_runway.sdf).
# Available worlds:
#   iris_runway.sdf         - degraded baseline (blank), 20 m x 20 m
#   iris_textured.sdf       - nominal baseline (textured), 20 m x 20 m
#   corridor_textured.sdf   - nominal, 20 m x 160 m corridor (checkerboard throughout)
#   corridor_blank.sdf      - degraded, 20 m x 160 m corridor (featureless throughout)
#   corridor_transition.sdf - 20 m x 160 m corridor, textured y:0-80, blank y:80-160
#                              (boundary at y=80 m — see CLAUDE.md "Corridor Worlds")
#
# gnome-terminal 3.52: the `--` flag stops all option parsing, so subsequent
# --tab flags get swallowed as arguments to the first command.  Use -e instead,
# which is the per-terminal command flag and does not break argument parsing.
# Commands are written to temp scripts to avoid quoting issues inside -e "...".

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  sed -n '3,13p' "$0"
  exit 0
fi

WORLD="${1:-iris_runway.sdf}"

if [ ! -f "$HOME/ardupilot_gazebo/worlds/$WORLD" ]; then
  echo "Error: world file not found: $HOME/ardupilot_gazebo/worlds/$WORLD" >&2
  echo "Available worlds:" >&2
  ls "$HOME/ardupilot_gazebo/worlds/"*.sdf 2>/dev/null | xargs -n1 basename | sed 's/^/  /' >&2
  exit 1
fi

SCRIPTS=$(mktemp -d --suffix=_sim_tabs)
rm -f /tmp/thesis_sim_stop

cat > "$SCRIPTS/gazebo.sh" << EOF
#!/usr/bin/env bash
cd ~/ardupilot_gazebo
export GZ_SIM_RESOURCE_PATH=\$HOME/ardupilot_gazebo/models:\$HOME/ardupilot_gazebo/worlds:\$GZ_SIM_RESOURCE_PATH
export GZ_SIM_SYSTEM_PLUGIN_PATH=\$HOME/ardupilot_gazebo/build:\$GZ_SIM_SYSTEM_PLUGIN_PATH
gz sim -v4 -r worlds/$WORLD
while ! [ -f /tmp/thesis_sim_stop ]; do sleep 0.3; done
EOF

cat > "$SCRIPTS/sitl.sh" << EOF
#!/usr/bin/env bash
echo "Waiting 5 s for Gazebo to load world..."
sleep 5
source ~/venv-ardupilot/bin/activate
cd ~/ardupilot/ArduCopter
../Tools/autotest/sim_vehicle.py \
  -v ArduCopter \
  -f gazebo-iris \
  --model JSON \
  --console \
  --map \
  --out 127.0.0.1:14551 \
  --out 127.0.0.1:14552 \
  --out 127.0.0.1:14553 \
  --out 127.0.0.1:14554 \
  --out 127.0.0.1:14555 \
  --add-param-file \$HOME/thesis_ws/lidar_rangefinder.parm \
  --add-param-file \$HOME/thesis_ws/flow_ekf.parm \
  --add-param-file \$HOME/thesis_ws/gnss_denied.parm \
  --no-rebuild
while ! [ -f /tmp/thesis_sim_stop ]; do sleep 0.3; done
EOF

cat > "$SCRIPTS/bridge.sh" << EOF
#!/usr/bin/env bash
echo "Waiting 10 s for Gazebo + SITL to connect..."
sleep 10
source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_bridge parameter_bridge \
  /downward_camera/image@sensor_msgs/msg/Image@gz.msgs.Image \
  /downward_camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo \
  /downward_lidar/range@sensor_msgs/msg/Range[gz.msgs.LaserScan \
  /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock \
  /world/${WORLD%.sdf}/dynamic_pose/info@geometry_msgs/msg/PoseArray[gz.msgs.Pose_V
while ! [ -f /tmp/thesis_sim_stop ]; do sleep 0.3; done
EOF

cat > "$SCRIPTS/attitude.sh" << EOF
#!/usr/bin/env bash
echo "Waiting 15 s for SITL + ROS2 clock bridge..."
sleep 15
source /opt/ros/jazzy/setup.bash
source ~/venv-ardupilot/bin/activate
python3 ~/thesis_ws/attitude_bridge.py --ros-args -p use_sim_time:=true
while ! [ -f /tmp/thesis_sim_stop ]; do sleep 0.3; done
EOF

cat > "$SCRIPTS/lidar.sh" << EOF
#!/usr/bin/env bash
echo "Waiting 15 s for SITL + ROS2 clock bridge..."
sleep 15
source /opt/ros/jazzy/setup.bash
source ~/venv-ardupilot/bin/activate
python3 ~/thesis_ws/lidar_bridge.py --ros-args -p use_sim_time:=true
while ! [ -f /tmp/thesis_sim_stop ]; do sleep 0.3; done
EOF

cat > "$SCRIPTS/flow.sh" << EOF
#!/usr/bin/env bash
echo "Waiting 15 s for ROS2 bridge..."
sleep 15
source /opt/ros/jazzy/setup.bash
source ~/thesis_ws/install/setup.bash
ros2 run optical_flow_node flow_tracker --ros-args -p use_sim_time:=true
while ! [ -f /tmp/thesis_sim_stop ]; do sleep 0.3; done
EOF

cat > "$SCRIPTS/flow_ekf.sh" << EOF
#!/usr/bin/env bash
echo "Waiting 18 s for optical_flow_node to be publishing..."
sleep 18
source /opt/ros/jazzy/setup.bash
source ~/venv-ardupilot/bin/activate
python3 ~/thesis_ws/flow_bridge.py --ros-args -p use_sim_time:=true
while ! [ -f /tmp/thesis_sim_stop ]; do sleep 0.3; done
EOF

cat > "$SCRIPTS/ekf.sh" << EOF
#!/usr/bin/env bash
echo "Waiting 15 s for SITL + ROS2 clock bridge..."
sleep 15
source /opt/ros/jazzy/setup.bash
source ~/venv-ardupilot/bin/activate
python3 ~/thesis_ws/ekf_bridge.py --ros-args -p use_sim_time:=true
while ! [ -f /tmp/thesis_sim_stop ]; do sleep 0.3; done
EOF

cat > "$SCRIPTS/imu.sh" << EOF
#!/usr/bin/env bash
echo "Waiting 15 s for SITL + ROS2 clock bridge..."
sleep 15
source /opt/ros/jazzy/setup.bash
source ~/venv-ardupilot/bin/activate
python3 ~/thesis_ws/imu_bridge.py --ros-args -p use_sim_time:=true
while ! [ -f /tmp/thesis_sim_stop ]; do sleep 0.3; done
EOF

cat > "$SCRIPTS/viewer.sh" << EOF
#!/usr/bin/env bash
echo "Waiting 20 s for ROS2..."
sleep 20
source /opt/ros/jazzy/setup.bash
ros2 run rqt_image_view rqt_image_view
while ! [ -f /tmp/thesis_sim_stop ]; do sleep 0.3; done
EOF

chmod +x "$SCRIPTS"/*.sh

gnome-terminal \
  --tab --title="Gazebo"       -e "bash $SCRIPTS/gazebo.sh" \
  --tab --title="SITL"         -e "bash $SCRIPTS/sitl.sh" \
  --tab --title="ROS2 Bridge"  -e "bash $SCRIPTS/bridge.sh" \
  --tab --title="Attitude"     -e "bash $SCRIPTS/attitude.sh" \
  --tab --title="LiDAR"        -e "bash $SCRIPTS/lidar.sh" \
  --tab --title="Optical Flow" -e "bash $SCRIPTS/flow.sh" \
  --tab --title="Flow EKF"     -e "bash $SCRIPTS/flow_ekf.sh" \
  --tab --title="EKF Pose"     -e "bash $SCRIPTS/ekf.sh" \
  --tab --title="IMU"          -e "bash $SCRIPTS/imu.sh" \
  --tab --title="Image Viewer" -e "bash $SCRIPTS/viewer.sh"
