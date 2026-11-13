import unittest
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
  def test_boundary_active_fault_and_sticky_status(self):
    rows = [timeline.panda_record(panda(can={'irq0CallRate': 16000}), 1_000_000_000),
            timeline.panda_record(panda(can={'irq0CallRate': 16001}, faults=['interruptRateCan2']), 2_000_000_000)]
    result = timeline.summarize_rows(rows, [{'mono_ns': 3_000_000_000, 'name': 'controlsMismatch'}], [], 'COMPLETE')
    self.assertEqual(result['first_rate_exceed_ns'], 2_000_000_000)
    self.assertEqual(result['first_active_fault_ns'], 2_000_000_000)
    self.assertEqual(result['first_controls_mismatch_ns'], 3_000_000_000)
    self.assertEqual(result['high_rate_seconds'], 1)

  def test_counter_reset_has_no_false_delta(self):
    a = timeline.panda_record(panda(can={'totalErrorCnt': 500}), 1)
    b = timeline.panda_record(panda(uptime=1, can={'totalErrorCnt': 2}), 2, a)
    self.assertTrue(b['reset'])
    self.assertIsNone(b['counter_deltas']['totalErrorCnt'])

  def test_order_and_sanitization(self):
    a = timeline.panda_record(panda(), 2_000_000_000)
    b = timeline.panda_record(panda(), 1_000_000_000)
    r = timeline.summarize_rows([a, b], [], [], 'COMPLETE')
    self.assertEqual(r['windows'], [])
    self.assertEqual(r['transitions'][0]['mono_ns'], 1_000_000_000)
    self.assertIsNone(timeline.safe_log('{"msg":"VIN secret coordinates"}'))
    self.assertEqual(timeline.safe_log('{"msg":"ublox NACK VIN 123"}'), 'gnss_nack')
    self.assertNotIn('VIN', str(r))
    self.assertNotIn('counters', str(r['transitions']))

if __name__ == '__main__':
  unittest.main()
