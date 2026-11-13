import unittest
from aol_matrix import BASE, decide

class MatrixTests(unittest.TestCase):
  def test_recorded_profile_not_independent(self):
    d = decide(BASE, preference=True)
    self.assertTrue(d['profile_eligible'])
    self.assertFalse(d['independent_session_proven'])
    self.assertIn('profile_unmarked', d['unproven_or_failed_gates'])

  def test_negative_profiles(self):
    for key, value in [('safety_param', 112), ('flags', 2181), ('pcm_cruise', False),
                       ('alternative_experience', 7), ('fingerprint', 'OTHER')]:
      with self.subTest(key=key):
        p = BASE | {key: value}
        self.assertFalse(decide(p, preference=True)['profile_eligible'])

  def test_marked_without_native_grant(self):
    p = BASE | {'alternative_experience': 32}
    self.assertFalse(decide(p, preference=True, fresh_state=True, physical_intent=True)['independent_session_proven'])

if __name__ == '__main__':
  unittest.main()
