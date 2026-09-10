import threading

from opendbc.car.honda.param_writer import HondaParamWriter


class RecordingParams:
  def __init__(self):
    self.calls = []
    self.lock = threading.Lock()

  def put_float(self, key, value):
    with self.lock:
      self.calls.append((key, float(value), threading.get_ident()))


class BlockingFirstWriteParams:
  def __init__(self):
    self.calls = []
    self.entered = threading.Event()
    self.release = threading.Event()
    self.blocked_once = False
    self.lock = threading.Lock()

  def put_float(self, key, value):
    if not self.blocked_once:
      self.blocked_once = True
      self.entered.set()
      assert self.release.wait(2.0)

    with self.lock:
      self.calls.append((key, float(value), threading.get_ident()))


def test_writer_cadence_and_close_drains_snapshot():
  params = RecordingParams()
  writer = HondaParamWriter(params)

  try:
    assert not writer.maybe_submit(0, 1.0, 1.0, 0.1)
    assert not writer.maybe_submit(5999, 1.0, 1.0, 0.1)
    assert writer.maybe_submit(6000, 1.25, 0.875, 0.2)
  finally:
    writer.close()

  assert [(k, v) for k, v, _ in params.calls] == [
    ("HondaGasFactorParams", 1.25),
    ("HondaWindFactorParams", 0.875),
    ("HondaGasAlphaParams", 0.2),
  ]


def test_non_accord_snapshot_preserves_exact_two_key_behavior():
  params = RecordingParams()
  writer = HondaParamWriter(params)

  try:
    assert writer.submit(1.1, 0.9, None)
  finally:
    writer.close()

  assert [(k, v) for k, v, _ in params.calls] == [
    ("HondaGasFactorParams", 1.1),
    ("HondaWindFactorParams", 0.9),
  ]


def test_submit_is_nonblocking_and_pending_snapshot_is_latest_wins():
  params = BlockingFirstWriteParams()
  writer = HondaParamWriter(params)
  caller_tid = threading.get_ident()

  try:
    # Worker blocks inside the first disk write.
    assert writer.submit(1.0, 1.0, None)
    assert params.entered.wait(2.0)

    # The control/caller thread must still be free to submit. While the
    # worker is occupied, snapshot 3 replaces snapshot 2 as a whole.
    assert writer.submit(2.0, 2.0, 0.2)
    assert writer.submit(3.0, 3.0, 0.3)

    params.release.set()
  finally:
    writer.close()

  calls = [(k, v) for k, v, _ in params.calls]

  assert calls == [
    ("HondaGasFactorParams", 1.0),
    ("HondaWindFactorParams", 1.0),
    ("HondaGasFactorParams", 3.0),
    ("HondaWindFactorParams", 3.0),
    ("HondaGasAlphaParams", 0.3),
  ]

  # No disk write ran on the submitting/control thread.
  assert all(tid != caller_tid for _, _, tid in params.calls)

  # Intermediate snapshot was coalesced away.
  assert not any(value == 2.0 for _, value, _ in params.calls)


def test_close_is_idempotent_and_rejects_future_submissions():
  params = RecordingParams()
  writer = HondaParamWriter(params)

  writer.close()
  writer.close()

  assert not writer.submit(1.0, 1.0, 0.1)
  assert params.calls == []
