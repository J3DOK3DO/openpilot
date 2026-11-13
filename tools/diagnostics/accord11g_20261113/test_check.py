import copy
import json
import unittest
import tempfile
from pathlib import Path
from check import LIMIT, check_summary, source_contract

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / 'route-summary.json').read_text())

class OfflineContracts(unittest.TestCase):
  def test_static_firmware_rejects_limit_and_mapping_changes(self):
    with tempfile.TemporaryDirectory() as tmp:
      base = Path(tmp)
      files = ['panda/board/stm32h7/stm32h7_config.h', 'panda/board/drivers/interrupts.h', 'panda/board/drivers/fdcan.h', 'panda/board/sys/sys.h']
      repo = HERE.parents[2]
      for name in files:
        target = base / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((repo / name).read_text())
      self.assertEqual(source_contract(base)['limit_per_second'], LIMIT)
      for name, old, new in [(files[0], '#define CAN_INTERRUPT_RATE 16000U', '#define CAN_INTERRUPT_RATE 17000U'),
                             (files[2], 'FDCAN2_IT0_IRQ_Handler(void) { can_rx(1); }', 'FDCAN2_IT0_IRQ_Handler(void) { can_rx(0); }')]:
        target = base / name
        original = target.read_text()
        self.assertIn(old, original)
        target.write_text(original.replace(old, new))
        with self.subTest(name=name), self.assertRaises(AssertionError):
          source_contract(base)
        target.write_text(original)

  def test_summary_passes(self):
    self.assertIn('PASS', check_summary(DATA))

  def test_fault_and_threshold_failures(self):
    for key, value in [('can1_irq0_peak', LIMIT), ('active_interrupt_rate_can2', 10913), ('controls_mismatch', 0)]:
      case = copy.deepcopy(DATA)
      case['routes'][0][key] = value
      with self.subTest(key=key), self.assertRaises(AssertionError):
        check_summary(case)

  def test_truncated_coverage_fails(self):
    case = copy.deepcopy(DATA)
    case['full_rlogs'] = 83
    with self.assertRaises(AssertionError):
      check_summary(case)

  def test_profile_mutation_fails(self):
    for key, value in [('safety_param', 81), ('alternative_experience', 32), ('openpilot_longitudinal', True)]:
      case = copy.deepcopy(DATA)
      case['routes'][2]['profile'][key] = value
      with self.subTest(key=key), self.assertRaises(AssertionError):
        check_summary(case)

if __name__ == '__main__':
  unittest.main()
