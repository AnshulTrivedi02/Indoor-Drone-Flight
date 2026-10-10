-- watcher_arming_auth.lua -- DRAFT, UNTESTED. Proposal for gap G6(ii) (docs/real_flights_plan.md 7.2.0).
--
-- Purpose: the FC refuses to ARM unless the mocap watcher's MAVLink HEARTBEAT (system ID = MAV_GCS_SYSID) has been
-- seen within FS_GCS_TIMEOUT. Stock ArduCopter cannot do this on its own: failsafe_gcs_check() returns early while
-- the GCS has never been seen (ArduCopter/events.cpp:134-136), so a watcher that was never started trips nothing;
-- AP_Arming_Copter::gcs_failsafe_check() (AP_Arming_Copter.cpp:519-525) refuses only while failsafe.gcs is latched,
-- i.e. after the watcher was seen and then lost.
--
-- Mechanism: auxiliary arming authorisation (AP_Arming::aux_auth_checks, AP_Arming.cpp:1556-1600, part of
-- pre_arm_checks at :1745). Bindings verified in libraries/AP_Scripting/docs/docs.lua at 7bac20cbcc:
--   arming:get_aux_auth_id() -> integer|nil ; arming:set_aux_auth_failed(id, msg) ; arming:set_aux_auth_passed(id)
--   gcs:last_seen() -> uint32_t_ud (ms; 0 = never; refreshed only by HEARTBEAT / RC override / MANUAL_CONTROL from a
--   GCS system ID, GCS_Common.cpp:4345-4351, 7652-7679) ; millis() -> uint32_t_ud
--
-- Preconditions / caveats (all to be verified on the target board before bench test B1c):
--   * the board build must include scripting (AP_SCRIPTING_ENABLED = HAL_PROGRAM_SIZE_LIMIT_KB > 1024) and therefore
--     aux auth (AP_ARMING_AUX_AUTH_ENABLED = AP_SCRIPTING_ENABLED); SCR_ENABLE 1, enough SCR_HEAP_SIZE;
--   * ARMING_SKIPCHK must not skip bit 17 (AUX_AUTH) and must not be -1 (should_skip_all_checks() then runs only the
--     mandatory checks, which do not include aux auth);
--   * a FORCE-arm (MAV_CMD_COMPONENT_ARM_DISARM param2 2989 or 21196, GCS_Common.cpp:5271) skips ALL pre-arm checks,
--     including this one. The flight script and the procedure must never force-arm (e.g. MAVProxy `arm throttle
--     force` is forbidden);
--   * the aux-auth state does not expire: if this script stops (error, out of memory, SCR_ENABLE 0), its LAST state
--     persists. The update is therefore wrapped in pcall and a failure sets FAILED; a crashed script stops updating
--     and the watcher-side checks (flight script refuses to arm) remain the primary layer;
--   * it gates ARMING only. In flight the native GCS failsafe (FS_GCS_ENABLE 5) does the landing.

local PERIOD_MS = 200
local auth_id = arming:get_aux_auth_id()

local function check()
  if not auth_id then
    auth_id = arming:get_aux_auth_id()
    return
  end
  local timeout_ms = math.floor((param:get('FS_GCS_TIMEOUT') or 3) * 1000)
  local last = gcs:last_seen()
  if last:toint() == 0 then
    arming:set_aux_auth_failed(auth_id, "Watcher: never seen")
    return
  end
  local age = (millis() - last):toint()
  if age > timeout_ms then
    arming:set_aux_auth_failed(auth_id, string.format("Watcher: heartbeat %.1fs old", age / 1000))
  else
    arming:set_aux_auth_passed(auth_id)
  end
end

local function update()
  local ok, err = pcall(check)
  if not ok then
    if auth_id then arming:set_aux_auth_failed(auth_id, "Watcher auth script error") end
    gcs:send_text(3, "watcher_arming_auth: " .. tostring(err))
  end
  return update, PERIOD_MS
end

if auth_id then arming:set_aux_auth_failed(auth_id, "Watcher: starting") end
return update, PERIOD_MS
