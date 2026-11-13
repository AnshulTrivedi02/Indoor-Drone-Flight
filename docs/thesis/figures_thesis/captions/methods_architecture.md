Figure 3.1. System architecture: sensors, bridges, the three estimators and where each one runs.

Panel (a) shows the sensors and the relays that carry their measurements to the flight controller and to the recorded data used offline. Panel (b) shows the flight controller, where each of the three estimators runs (outlined in its own colour, as in every other figure: EKF3 blue, UKF green, FGO orange), the safety watchers, and the offline replay and evaluation. In the open-loop experiments the vehicle flies on simulator truth, EKF3 runs passively alongside it and the UKF and FGO are replayed offline against the same recording; in the closed-loop experiments one estimator flies while the other two run in shadow. The FGO runs as a separate process whose state the flight controller reads.

Verdicts: Table A.4, none (descriptive).
