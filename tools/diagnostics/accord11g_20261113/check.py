#!/usr/bin/env python3
"""Read-only source and sanitized-summary contract checks. No project imports."""
import argparse
import json
import re
from pathlib import Path

LIMIT = 16000

def source_contract(root):
  root = Path(root)
  def read(path):
    return (root / path).read_text()
  config = read('panda/board/stm32h7/stm32h7_config.h')
  irq = read('panda/board/drivers/interrupts.h')
  fdcan = read('panda/board/drivers/fdcan.h')
  fault_path = 'panda/board/sys/sys.h' if (root / 'panda/board/sys/sys.h').exists() else 'panda/board/faults_declarations.h'
  sys = read(fault_path)
  match = re.search(r'#define CAN_INTERRUPT_RATE\s+(\d+)U', config)
  assert match and int(match.group(1)) == LIMIT, 'watchdog limit differs from audited baseline'
  assert 'call_counter > interrupts[irq_type].max_call_rate' in irq
  assert 'fault_occurred(interrupts[irq_type].call_rate_fault)' in irq
  assert re.search(r'FDCAN2_IT0_IRQ_Handler\(void\)\s*\{\s*can_rx\(1\)', fdcan)
  assert re.search(r'REGISTER_INTERRUPT\(FDCAN2_IT0_IRQn, FDCAN2_IT0_IRQ_Handler, CAN_INTERRUPT_RATE, FAULT_INTERRUPT_RATE_CAN_2\)', fdcan)
  assert re.search(r'FAULT_INTERRUPT_RATE_CAN_2\s+\(1UL << 3\)', sys)
  return {'limit_per_second': LIMIT, 'can1_controller': 'FDCAN2', 'fault_bit': 8}

def check_summary(data):
  assert data['schema'] == 1
  assert data['full_rlogs'] == 82 and data['listed_segments'] == 83
  assert data['excluded_segment'] == 62
  assert len(data['routes']) == 3
  for i, route in enumerate(data['routes']):
    assert route['route_index'] == i
    assert route['profile'] == {'brand': 'honda', 'fingerprint': 'HONDA_ACCORD_11G', 'safety_model': 'hondaBosch', 'safety_param': 80, 'pcm_cruise': True, 'openpilot_longitudinal': False, 'alternative_experience': 0, 'flags': 2180}
    assert route['active_interrupt_rate_can2'] <= route['panda_states']
  first, second, third = data['routes']
  assert first['controls_mismatch'] == 2603 and first['active_interrupt_rate_can2'] == 10873 and first['panda_states'] == 10912
  assert first['can1_irq0_peak'] == 17862 and first['can1_irq0_peak'] > LIMIT
  assert second['controls_mismatch'] == 49 and second['active_interrupt_rate_can2'] == second['panda_states'] == 230
  assert third['controls_mismatch'] == third['active_interrupt_rate_can2'] == 0
  assert third['enabled_lateral_with_stock_acc'] and third['comm_issue_events'] == 1
  return 'PASS: three route contracts; 82/83 coverage; baseline profile; active faults; 17862 > 16000'

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--current', type=Path, required=True)
  parser.add_argument('--older', type=Path, required=True)
  parser.add_argument('--summary', type=Path, default=Path(__file__).with_name('route-summary.json'))
  args = parser.parse_args()
  assert args.current.resolve() != args.older.resolve()
  a, b = source_contract(args.current), source_contract(args.older)
  assert a == b
  print('PASS: current and C6-12 FDCAN2 rate/fault contract:', a)
  print(check_summary(json.loads(args.summary.read_text())))

if __name__ == '__main__':
  main()
