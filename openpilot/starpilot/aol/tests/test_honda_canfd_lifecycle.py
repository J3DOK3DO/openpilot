"""Stock CAN-FD Honda caller, C++ negotiation, and native TX lifecycle."""
from opendbc.car.honda.values import CAR
from openpilot.starpilot.aol.tests.test_honda_recovery_lifecycle import TestHondaCurrentCaller as CurrentCaller

class TestHondaCanfdCaller(CurrentCaller):
  def test_canfd_0_eps_reverse_recovery(self):
    self.run_current_caller(candidate=CAR.HONDA_CRV_6G, word=16)

  def test_canfd_1_eps_reverse_recovery(self):
    self.run_current_caller(candidate=CAR.HONDA_PILOT_4G, word=16)

  def test_canfd_2_eps_reverse_recovery(self):
    self.run_current_caller(candidate=CAR.HONDA_PASSPORT_4G, word=16)

  def test_canfd_3_eps_reverse_recovery(self):
    self.run_current_caller(candidate=CAR.ACURA_MDX_4G_MMR, word=16)

  def test_canfd_4_eps_reverse_recovery(self):
    self.run_current_caller(candidate=CAR.ACURA_TLX_2G_MMR, word=16)


  def test_canfd_alternate_brake_eps_reverse_recovery(self):
    self.run_current_caller(candidate=CAR.HONDA_CRV_6G, word=17, alternate_brake=True)

  def test_accord_mvl_eps_reverse_recovery(self):
    self.run_current_caller(candidate=CAR.HONDA_ACCORD_11G, word=80)

  def test_accord_mvl_reverse_return_fresh_lkas(self):
    self.run_current_caller(candidate=CAR.HONDA_ACCORD_11G, word=80, accord_fresh_lkas=True)

  def test_accord_mvl_physical_cancel_with_independent_latch(self):
    self.run_current_caller(candidate=CAR.HONDA_ACCORD_11G, word=80, host_scenario='cancel')

  def test_accord_mvl_cancel_without_independent_latch(self):
    self.run_current_caller(candidate=CAR.HONDA_ACCORD_11G, word=80, host_scenario='cancel_without_latch')

  def test_accord_mvl_full_stop_no_late_resume(self):
    self.run_current_caller(candidate=CAR.HONDA_ACCORD_11G, word=80, full_stop=True)

  def test_accord_mvl_parked_drive_lkas_no_motion_rearm(self):
    self.run_current_caller(candidate=CAR.HONDA_ACCORD_11G, word=80, stationary_lkas=True)

  def test_accord_mvl_can2_interrupt_fault_withdraws(self):
    self.run_current_caller(candidate=CAR.HONDA_ACCORD_11G, word=80, fault='can2_early')

  def test_accord_mvl_rx_invalid_controls_mismatch_withdraws(self):
    self.run_current_caller(candidate=CAR.HONDA_ACCORD_11G, word=80, fault='rx_invalid_early')
