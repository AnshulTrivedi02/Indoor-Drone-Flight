#!/usr/bin/env bash
# Tear down the full simulation stack and close sim terminal tabs.

echo "Stopping simulation stack..."

pkill -f "gz sim"
pkill -f "sim_vehicle.py"
pkill -f "mavproxy"
pkill -f "ros2"
pkill -f "rqt_image_view"

# Signal all sim tabs to close (each tab polls for this file)
touch /tmp/thesis_sim_stop
sleep 1
rm -f /tmp/thesis_sim_stop

echo "Done."
