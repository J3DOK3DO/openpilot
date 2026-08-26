"""Exact-platform routing helpers for the isolated Accord longitudinal layer."""

from opendbc.car.honda.values import CAR as HONDA_CAR


def is_mvl_accord(CP):
  return CP.carFingerprint == HONDA_CAR.HONDA_ACCORD_11G


def apply_global_accel_limit(mvl_accord_mode, output_accel, global_max_accel):
  return output_accel if mvl_accord_mode else min(output_accel, global_max_accel)


def create_long_control(CP):
  if is_mvl_accord(CP):
    from openpilot.selfdrive.controls.lib.mvl_accord_longcontrol import MVLAccordLongControl
    return MVLAccordLongControl(CP)

  from openpilot.selfdrive.controls.lib.longcontrol import LongControl
  return LongControl(CP)


def create_longitudinal_planner(CP):
  if is_mvl_accord(CP):
    from openpilot.selfdrive.controls.lib.mvl_accord_longitudinal_planner import MVLAccordLongitudinalPlanner
    return MVLAccordLongitudinalPlanner(CP)

  from openpilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlanner
  return LongitudinalPlanner(CP)
