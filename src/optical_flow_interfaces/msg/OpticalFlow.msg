std_msgs/Header header

# flow_x/flow_y: derotated if derotation_enabled, else equal to the raw
# fields below. CHARACTERISATION ONLY — quantifies rotational coupling for
# the methodology write-up and FGO factor design. NOT an estimator input.
# See CLAUDE.md, "Sensor Fusion Architecture".
float64 flow_x            # pixel flow x (px/s), characterisation only
float64 flow_y            # pixel flow y (px/s), characterisation only
int32   feature_count     # features tracked this frame
float64 inlier_ratio      # fraction of features surviving RANSAC (0–1)
bool    valid             # measurement is trustworthy

float64 flow_x_rad        # angular flow x (rad/s) — zero until pixel-to-radian conversion implemented
float64 flow_y_rad        # angular flow y (rad/s) — zero until pixel-to-radian conversion implemented

# flow_x_raw/flow_y_raw: raw pixel flow, pre-derotation. PRODUCTION VALUES —
# feed these (with /attitude/angular_rates) to ArduPilot EKF3's OPTICAL_FLOW_RAD
# input and to the FGO's flow factor; each estimator derotates internally.
float64 flow_x_raw        # pixel flow x pre-derotation (px/s), always raw
float64 flow_y_raw        # pixel flow y pre-derotation (px/s), always raw
bool    derotation_enabled # true if flow_x/flow_y above had rotational flow subtracted
