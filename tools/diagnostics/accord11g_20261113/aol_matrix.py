"""Non-actuating, conservative Accord 11G profile check. No vehicle imports."""

BASE = {'brand': 'honda', 'fingerprint': 'HONDA_ACCORD_11G', 'safety_model': 'hondaBosch',
        'safety_param': 80, 'flags': 2180, 'pcm_cruise': True, 'openpilot_longitudinal': False,
        'alternative_experience': 0, 'passive': False, 'dashcam_only': False, 'not_car': False,
        'transmission': 'automatic', 'safety_configs': 1}


def decide(profile, *, preference=False, native=None, fresh_state=False, physical_intent=False):
  """Report observed gates; never infer a native grant from a saved preference."""
  reasons = []
  for key in ('brand', 'fingerprint', 'safety_model', 'safety_param', 'flags', 'pcm_cruise',
              'openpilot_longitudinal', 'passive', 'dashcam_only', 'not_car', 'safety_configs'):
    if profile.get(key) != BASE[key]:
      reasons.append(key)
  if profile.get('transmission') not in ('automatic', 'cvt'):
    reasons.append('transmission')
  if profile.get('alternative_experience') not in (0, 32):
    reasons.append('alternative_experience_invalid')
  marked = profile.get('alternative_experience') == 32
  if not preference: reasons.append('preference_missing')
  if not marked: reasons.append('profile_unmarked')
  if not fresh_state: reasons.append('fresh_car_state_unproven')
  if not physical_intent: reasons.append('physical_intent_unproven')
  if native is None or not native.get('requested_lateral') or not native.get('lateral_allowed'):
    reasons.append('native_grant_unproven')
  if native is None or not native.get('inventory_match') or not native.get('session_match'):
    reasons.append('native_session_inventory_unproven')
  return {'profile_eligible': not any(x in reasons for x in ('brand','fingerprint','safety_model','safety_param','flags','pcm_cruise','openpilot_longitudinal','passive','dashcam_only','not_car','safety_configs','transmission','alternative_experience_invalid')),
          'independent_session_proven': not reasons, 'unproven_or_failed_gates': reasons}
