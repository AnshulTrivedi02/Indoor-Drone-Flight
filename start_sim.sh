#!/usr/bin/env bash
# Launch the full simulation stack in five gnome-terminal tabs.
#
# gnome-terminal 3.52: the `--` flag stops all option parsing, so subsequent
# --tab flags get swallowed as arguments to the first command.  Use -e instead,
# which is the per-terminal command flag and does not break argument parsing.
# Commands are written to temp scripts to avoid quoting issues inside -e "...".

SCRIPTS=$(mktemp -d --suffix=_sim_tabs)
WORLD="${1:-iris_runway.sdf}"
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
  /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock \
  /world/${WORLD%.sdf}/dynamic_pose/info@geometry_msgs/msg/PoseArray[gz.msgs.Pose_V
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
  --tab --title="Optical Flow" -e "bash $SCRIPTS/flow.sh" \
  --tab --title="Image Viewer" -e "bash $SCRIPTS/viewer.sh"
