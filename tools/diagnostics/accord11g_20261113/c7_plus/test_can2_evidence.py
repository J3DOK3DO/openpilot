import json
import tempfile
import unittest
from pathlib import Path

from can2_evidence import summarize


class Can2EvidenceTests(unittest.TestCase):
  def test_active_fault_and_rate_are_distinct(self):
    data = {"limit_per_second": 16000, "routes": [
      {"route_index": 1, "decoded_segments": 1, "peak_irq0": 9700,
       "high_rate_panda_samples": 0, "first_active_fault_ns": 12,
       "first_controls_mismatch_ns": 13,
       "observed_counter_delta_sum": {key: 0 for key in ("totalRxCnt", "totalErrorCnt", "totalRxLostCnt", "busOffCnt", "canCoreResetCnt")}},
    ]}
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / "summary.json"
      path.write_text(json.dumps(data))
      result = summarize(path)["routes"][0]
    self.assertFalse(result["above_limit"])
    self.assertEqual(result["first_active_fault_ns"], 12)
    self.assertEqual(result["first_mismatch_ns"], 13)


if __name__ == "__main__":
  unittest.main()
