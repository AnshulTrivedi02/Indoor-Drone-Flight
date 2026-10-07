-- Experiment O (2026-10-08): EKF3 source-set switch on GNSS fix status. The stock example
-- (AP_Scripting/examples/ahrs-source-gps-optflow.lua) votes on GPS SPEED ACCURACY, which SITL keeps at 0 when the GPS
-- is disabled, so it never switches. This keeps its 2 s vote (20 x 100 ms) but votes on
-- gps:status(primary) < GPS_OK_FIX_3D (SITL reports NO_FIX while SIM_GPS1_ENABLE = 0). No RC switches, no thresholds.
-- Source set 1 (index 0) = GPS, set 2 (index 1) = optical flow.
local VMAX = 20
local votes = 0
local current = 0
function update()
  local st = gps:status(gps:primary_sensor())
  if st < gps.GPS_OK_FIX_3D then
    votes = math.min(votes + 1, VMAX)
  else
    votes = math.max(votes - 1, -VMAX)
  end
  if votes >= VMAX and current ~= 1 then
    current = 1
    ahrs:set_posvelyaw_source_set(1)
    gcs:send_text(6, "O-switch: source set 2 (flow)")
  elseif votes <= -VMAX and current ~= 0 then
    current = 0
    ahrs:set_posvelyaw_source_set(0)
    gcs:send_text(6, "O-switch: source set 1 (GPS)")
  end
  return update, 100
end
gcs:send_text(6, "O-switch: loaded")
return update()
