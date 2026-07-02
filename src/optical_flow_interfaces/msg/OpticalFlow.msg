std_msgs/Header header

float64 flow_x            # pixel flow x (px/s) — derotated if derotation_enabled, else raw
float64 flow_y            # pixel flow y (px/s) — derotated if derotation_enabled, else raw
int32   feature_count     # features tracked this frame
float64 inlier_ratio      # fraction of features surviving RANSAC (0–1)
bool    valid             # measurement is trustworthy

float64 flow_x_rad        # angular flow x (rad/s) — zero until gyro decoupling implemented
float64 flow_y_rad        # angular flow y (rad/s) — zero until gyro decoupling implemented

float64 flow_x_raw        # pixel flow x pre-derotation (px/s), always raw
float64 flow_y_raw        # pixel flow y pre-derotation (px/s), always raw
bool    derotation_enabled # true if flow_x/flow_y above had rotational flow subtracted
