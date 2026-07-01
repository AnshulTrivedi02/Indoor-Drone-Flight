std_msgs/Header header

float64 flow_x            # pixel flow x (px/s)
float64 flow_y            # pixel flow y (px/s)
int32   feature_count     # features tracked this frame
float64 inlier_ratio      # fraction of features surviving RANSAC (0–1)
bool    valid             # measurement is trustworthy

float64 flow_x_rad        # angular flow x (rad/s) — zero until gyro decoupling implemented
float64 flow_y_rad        # angular flow y (rad/s) — zero until gyro decoupling implemented
