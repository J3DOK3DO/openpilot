import unittest
from collections import Counter
from types import SimpleNamespace as NS
import timeline


def panda(**changes):
  can = dict(irq0CallRate=0, irq1CallRate=0, receiveErrorCnt=0, totalErrorCnt=0,
             errorWarning=False, errorPassive=False, busOff=False, lastError='noError')
  can.update({k: 0 for k in timeline.COUNTERS})
  can.update(changes.pop('can', {}))
  p = dict(canState1=NS(**can), uptime=3, safetyModel='hondaBosch', safetyParam=80,
           alternativeExperience=0, controlsAllowed=False, faults=[], faultStatus='faultTemp',
           safetyRxChecksInvalid=False, heartbeatLost=False)
  p.update(changes)
  return NS(**p)


class TimelineTests(unittest.TestCase):
  @staticmethod
  def raw_state():
    return {'counter_totals': Counter(), 'counter_epochs': 0, 'counter_boundaries': 0,
            'raw_panda_samples': 0, 'peak_irq0': None, 'peak_irq1': None,
            'max_mono_ns': None, 'counter_quarantine_until_ns': None,
            'high_rate_sample_count': 0, 'high_rate_second_set': set(),
            'first_rate': None, 'first_fault': None}

  @classmethod
  def observed(cls, rows):
    state = cls.raw_state()
    for row in rows:
      timeline.observe_panda(state, row)
    return state

  def test_boundary_active_fault_and_sticky_status(self):
    rows = [timeline.panda_record(panda(can={'irq0CallRate': 16000}), 1_000_000_000),
            timeline.panda_record(panda(can={'irq0CallRate': 16001}, faults=['interruptRateCan2']), 2_000_000_000)]
    result = timeline.summarize_rows(rows, [{'mono_ns': 3_000_000_000, 'name': 'controlsMismatch'}], [], 'COMPLETE', self.observed(rows))
    self.assertEqual(result['first_rate_exceed_ns'], 2_000_000_000)
    self.assertEqual(result['first_active_fault_ns'], 2_000_000_000)
    self.assertEqual(result['first_controls_mismatch_ns'], 3_000_000_000)
    self.assertEqual(result['high_rate_seconds'], 1)

  def test_counter_reset_has_no_false_delta(self):
    a = timeline.panda_record(panda(can={'totalErrorCnt': 500}), 1)
    b = timeline.panda_record(panda(uptime=1, can={'totalErrorCnt': 2}), 2, a)
    self.assertTrue(b['reset'])
    self.assertIsNone(b['counter_deltas']['totalErrorCnt'])

  def test_counter_wrap_is_boundary_without_wraparound_inference(self):
    state = self.raw_state()
    a = timeline.panda_record(panda(can={'totalErrorCnt': 2**32 - 2}), 1)
    timeline.observe_panda(state, a)
    b = timeline.panda_record(panda(can={'totalErrorCnt': 3}), 2, a)
    timeline.observe_panda(state, b)
    self.assertTrue(b['reset'])
    self.assertIsNone(b['counter_deltas']['totalErrorCnt'])
    self.assertEqual(state['counter_totals']['totalErrorCnt'], 0)

  def test_all_raw_counter_deltas_across_skipped_samples(self):
    state = self.raw_state()
    previous = None
    selected = []
    for i in range(10):
      row = timeline.panda_record(panda(can={'totalErrorCnt': 100 + 10*i, 'totalRxCnt': 100 + 10*i}),
                                  1_000_000_000 + 100_000_000*i, previous)
      timeline.observe_panda(state, row)
      if i in (0, 9):
        selected.append(row)
      previous = row
    self.assertEqual(timeline.selected_counter_delta(selected[1], selected[0])['totalErrorCnt'], 90)
    result = timeline.summarize_rows(selected, [], [], 'COMPLETE', state)
    self.assertEqual(result['observed_counter_delta_sum']['totalErrorCnt'], 90)
    self.assertEqual(result['observed_counter_delta_sum']['totalRxCnt'], 90)

  def test_intermediate_reset_and_recovery_invalidates_endpoint(self):
    state = self.raw_state()
    a = timeline.panda_record(panda(can={'totalErrorCnt': 100}), 1)
    timeline.observe_panda(state, a)
    b = timeline.panda_record(panda(uptime=1, can={'totalErrorCnt': 2}), 2, a)
    timeline.observe_panda(state, b)
    c = timeline.panda_record(panda(uptime=2, can={'totalErrorCnt': 190}), 3, b)
    timeline.observe_panda(state, c)
    self.assertIsNone(timeline.selected_counter_delta(c, a)['totalErrorCnt'])
    self.assertEqual(state['counter_totals']['totalErrorCnt'], 188)
    self.assertEqual(state['counter_boundaries'], 1)

  def test_nonmonotonic_time_starts_new_epoch(self):
    state = self.raw_state()
    a = timeline.panda_record(panda(can={'totalErrorCnt': 100}), 20)
    timeline.observe_panda(state, a)
    b = timeline.panda_record(panda(can={'totalErrorCnt': 190}), 10, a)
    timeline.observe_panda(state, b)
    c = timeline.panda_record(panda(can={'totalErrorCnt': 200}), 11, b)
    timeline.observe_panda(state, c)
    d = timeline.panda_record(panda(can={'totalErrorCnt': 300}), 21, c)
    timeline.observe_panda(state, d)
    e = timeline.panda_record(panda(can={'totalErrorCnt': 310}), 22, d)
    timeline.observe_panda(state, e)
    self.assertTrue(b['counter_discontinuity'])
    self.assertIsNone(timeline.selected_counter_delta(b, a)['totalErrorCnt'])
    self.assertIsNone(timeline.selected_counter_delta(c, b)['totalErrorCnt'])
    self.assertIsNone(timeline.selected_counter_delta(d, b)['totalErrorCnt'])
    self.assertEqual(state['counter_totals']['totalErrorCnt'], 10)

  def test_brief_raw_rate_spike_survives_nearest_second_selection(self):
    state = self.raw_state()
    a = timeline.panda_record(panda(can={'irq0CallRate': 0}), 1_000_000_000)
    timeline.observe_panda(state, a)
    b = timeline.panda_record(panda(can={'irq0CallRate': 16001}), 1_100_000_000, a)
    timeline.observe_panda(state, b)
    result = timeline.summarize_rows([a], [], [], 'COMPLETE', state)
    self.assertEqual(result['first_rate_exceed_ns'], b['mono_ns'])
    self.assertEqual(state['first_rate'], b['mono_ns'])
    self.assertEqual(result['peak_irq0'], 16001)
    self.assertEqual(result['high_rate_seconds'], 1)
    self.assertEqual(result['high_rate_panda_samples'], 1)

  def test_order_and_sanitization(self):
    a = timeline.panda_record(panda(), 2_000_000_000)
    b = timeline.panda_record(panda(), 1_000_000_000)
    r = timeline.summarize_rows([a, b], [], [], 'COMPLETE', self.observed([a, b]))
    self.assertEqual(r['windows'], [])
    self.assertEqual(r['transitions'][0]['mono_ns'], 1_000_000_000)
    self.assertIsNone(timeline.safe_log('{"msg":"VIN secret coordinates"}'))
    self.assertEqual(timeline.safe_log('{"msg":"ublox NACK VIN 123"}'), 'gnss_nack')
    self.assertNotIn('VIN', str(r))
    self.assertNotIn('counters', str(r['transitions']))

if __name__ == '__main__':
  unittest.main()
