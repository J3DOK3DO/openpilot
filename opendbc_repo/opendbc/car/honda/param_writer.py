import threading

from openpilot.common.swaglog import cloudlog


class HondaParamWriter:
  """Single asynchronous owner for persisted Honda longitudinal learning.

  Contract:
  - CarController never performs disk writes.
  - Persistence cadence is one snapshot every 6000 controller frames.
  - submit() never waits for disk I/O.
  - At most one pending snapshot exists; a newer snapshot replaces it.
  - The background worker writes one complete latest snapshot.
  - close() drains the latest pending snapshot and joins the worker.
  """

  PERSIST_INTERVAL_FRAMES = 6000

  def __init__(self, params):
    self.params = params

    self._condition = threading.Condition()
    self._pending = None
    self._closed = False
    self._thread = None
    self._last_error = None

  @property
  def last_error(self):
    return self._last_error

  def _start_worker_locked(self):
    if self._thread is None:
      self._thread = threading.Thread(
        target=self._run,
        name="honda-param-writer",
        daemon=True,
      )
      self._thread.start()

  def submit(self, gas_factor: float, wind_factor: float, gasalpha: float | None = None) -> bool:
    snapshot = (
      float(gas_factor),
      float(wind_factor),
      None if gasalpha is None else float(gasalpha),
    )

    with self._condition:
      if self._closed:
        return False

      # One-slot whole-snapshot coalescing: latest complete state wins.
      self._pending = snapshot
      self._start_worker_locked()
      self._condition.notify()

    return True

  def maybe_submit(self, frame: int, gas_factor: float, wind_factor: float,
                   gasalpha: float | None = None) -> bool:
    if frame <= 0 or frame % self.PERSIST_INTERVAL_FRAMES != 0:
      return False

    return self.submit(gas_factor, wind_factor, gasalpha)

  def _write_snapshot(self, snapshot):
    gas_factor, wind_factor, gasalpha = snapshot

    # These calls may block on disk, but this method runs only on the
    # dedicated background worker and never on CarController.update().
    self.params.put_float("HondaGasFactorParams", gas_factor)
    self.params.put_float("HondaWindFactorParams", wind_factor)

    if gasalpha is not None:
      self.params.put_float("HondaGasAlphaParams", gasalpha)

  def _run(self):
    while True:
      with self._condition:
        while self._pending is None and not self._closed:
          self._condition.wait()

        if self._pending is None and self._closed:
          return

        snapshot = self._pending
        self._pending = None

      try:
        self._write_snapshot(snapshot)
        self._last_error = None
      except Exception as exc:
        self._last_error = exc
        cloudlog.exception("HondaParamWriter failed to persist learned parameters")

  def close(self):
    with self._condition:
      if not self._closed:
        self._closed = True
        self._condition.notify_all()

      thread = self._thread

    if thread is not None and thread is not threading.current_thread():
      thread.join()
