"""Validated MVL radar lead policy isolated to the Honda Accord 11G."""

import math
from typing import Any

from opendbc.car.honda.values import CAR as HONDA_CAR


RADAR_TO_CAMERA = 1.52
MVL_ACCORD_LEAD_ACCEL_TAU = 1.5
MVL_ACCORD_MODEL_LEAD_PROBABILITY = 0.5


def is_mvl_accord_radar(CP) -> bool:
  return CP.carFingerprint == HONDA_CAR.HONDA_ACCORD_11G


def update_mvl_accord_accel_tau(a_lead_tau, a_lead_k: float) -> None:
  if abs(a_lead_k) < 0.5:
    a_lead_tau.x = MVL_ACCORD_LEAD_ACCEL_TAU
  else:
    a_lead_tau.update(0.0)


def _laplacian_pdf(x: float, mu: float, scale: float) -> float:
  scale = max(scale, 1e-4)
  return math.exp(-abs(x - mu) / scale)


def mvl_match_vision_to_track(v_ego: float, lead, tracks: dict[int, Any]):
  """Return the highest-probability track when it passes validated MVL sanity gates."""
  if not tracks:
    return None

  offset_vision_dist = lead.x[0] - RADAR_TO_CAMERA

  def probability(track) -> float:
    prob_d = _laplacian_pdf(track.dRel, offset_vision_dist, lead.xStd[0])
    prob_y = _laplacian_pdf(track.yRel, -lead.y[0], lead.yStd[0])
    prob_v = _laplacian_pdf(track.vRel + v_ego, lead.v[0], lead.vStd[0])
    return prob_d * prob_y * prob_v

  track = max(tracks.values(), key=probability)
  dist_sane = abs(track.dRel - offset_vision_dist) < max(offset_vision_dist * 0.25, 5.0)
  vel_sane = abs(track.vRel + v_ego - lead.v[0]) < 10.0 or v_ego + track.vRel > 3.0
  return track if dist_sane and vel_sane else None


def mvl_get_radar_state_from_vision(lead, v_ego: float, model_v_ego: float, lead_prob: float) -> dict[str, Any]:
  lead_v_rel_pred = lead.v[0] - model_v_ego
  return {
    "dRel": float(lead.x[0] - RADAR_TO_CAMERA),
    "yRel": float(-lead.y[0]),
    "vRel": float(lead_v_rel_pred),
    "vLead": float(v_ego + lead_v_rel_pred),
    "vLeadK": float(v_ego + lead_v_rel_pred),
    "aLeadK": float(lead.a[0]),
    "aLeadTau": 0.3,
    "fcw": False,
    "modelProb": float(lead_prob),
    "status": True,
    "radar": False,
    "radarTrackId": -1,
  }


def mvl_get_lead(v_ego: float, ready: bool, tracks: dict[int, Any], lead, model_v_ego: float,
                 lead_prob: float, low_speed_override: bool = True) -> dict[str, Any]:
  """Select one Accord lead without StarPilot preferred-track or target-shaping policy."""
  if tracks and ready and lead_prob > MVL_ACCORD_MODEL_LEAD_PROBABILITY:
    track = mvl_match_vision_to_track(v_ego, lead, tracks)
  else:
    track = None

  lead_dict: dict[str, Any] = {"status": False}
  if track is not None:
    lead_dict = track.get_RadarState(lead_prob)
  elif ready and lead_prob > MVL_ACCORD_MODEL_LEAD_PROBABILITY:
    lead_dict = mvl_get_radar_state_from_vision(lead, v_ego, model_v_ego, lead_prob)

  if low_speed_override:
    low_speed_tracks = [candidate for candidate in tracks.values() if candidate.potential_low_speed_lead(v_ego)]
    if low_speed_tracks:
      closest_track = min(low_speed_tracks, key=lambda candidate: candidate.dRel)
      if not lead_dict["status"] or closest_track.dRel < lead_dict["dRel"]:
        lead_dict = closest_track.get_RadarState()

  for radar_track in tracks.values():
    radar_track.leadTrackID = lead_dict.get("radarTrackId", -1)

  return lead_dict
