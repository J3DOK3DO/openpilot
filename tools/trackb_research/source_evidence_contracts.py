"""Offline contracts for the seven MVL architecture-delta findings (F1, F2, F4, F5, F7).

MVL 3fec9a infers ownership, relay state, radar cadence, startup faults and lane metadata from parser history and
update counts. These models derive the same labels from explicit synthetic evidence and refuse the shortcuts the
delta analysis identified. Everything is stdlib-only and symbolic: no frame, payload, bus, CAN, UDS or actuator type.
A result here is source-consistency evidence at most; it never measures a vehicle or authorizes control.
"""

from dataclasses import dataclass
from math import isfinite

# Stream classes (F1).
ABSENT = "absent"            # no frame received in the window
REJECTED = "rejected"        # frames received but every one failed checksum/counter/length
STALE = "stale"              # last accepted frame older than the freshness bound
FRESH = "fresh"              # at least one accepted frame within the bound
INVALID = "invalid_input"

# Inference labels (F1/F2). "inferred" labels are hypotheses about the vehicle, never measurements.
RELAY_UNKNOWN = "relay_unknown"
RELAY_CLOSED_INFERRED = "relay_closed_inferred"
RELAY_OPEN_INFERRED = "relay_open_inferred"
NO_REFERENCE_OBSERVED = "no_reference_observed"
REFERENCE_STALE = "reference_stale"
REFERENCE_TICK = "reference_tick"
REFERENCE_HELD = "reference_held"

# Lifecycle evidence kinds (F4). Only target or OEM evidence can establish a physical stage.
PHYSICAL_EVIDENCE = frozenset(("oem_authenticated", "target_measurement"))
EVIDENCE_KINDS = PHYSICAL_EVIDENCE | frozenset(("source_only", "synthetic_only", "unknown"))
LIFECYCLE_STAGES = ("request_constructed", "safety_accepted", "ecu_acknowledged", "stock_stream_resumed", "fault_cleared")


def _finite(value: object) -> bool:
  return type(value) in (int, float) and isfinite(value)


def _count(value: object) -> bool:
  return type(value) is int and value >= 0


@dataclass(frozen=True, slots=True)
class StreamWindow:
  """What one synthetic update window saw for one source stream."""

  received: int            # frames seen on the wire in this window
  accepted: int            # frames that passed checksum/counter/length
  age_s: float | None      # time since the last accepted frame, None if never accepted


def classify_stream(window: object, max_age_s: object) -> str:
  """F1: message silence, parser rejection and staleness are distinct, never merged into 'absent'."""
  if (type(window) is not StreamWindow or not _count(window.received) or not _count(window.accepted) or
      window.accepted > window.received or not _finite(max_age_s) or max_age_s <= 0 or
      not (window.age_s is None or (_finite(window.age_s) and window.age_s >= 0))):
    return INVALID
  if window.accepted > 0:
    return FRESH if window.age_s is not None and window.age_s <= max_age_s else INVALID
  if window.received > 0:
    return REJECTED
  if window.age_s is None:
    return ABSENT
  return STALE if window.age_s > max_age_s else FRESH


class RelayInference:
  """F1: relay state only as an inference from camera-steering silence after it was seen fresh.

  MVL also declares the relay open after a fixed number of CAN-FD updates, even while camera frames continue. This
  model has no update-count fallback: continuous fresh camera frames can never produce an open inference, and a
  rejected or invalid stream yields unknown rather than silence.
  """

  def __init__(self, silent_windows_for_open: int) -> None:
    if type(silent_windows_for_open) is not int or silent_windows_for_open < 1:
      raise ValueError("silent_windows_for_open must be a positive int")
    self._needed = silent_windows_for_open
    self._seen_fresh = False
    self._silent = 0

  def observe(self, camera_class: str) -> str:
    if camera_class == FRESH:
      self._seen_fresh, self._silent = True, 0
      return RELAY_CLOSED_INFERRED
    if camera_class not in (ABSENT, STALE):
      # Rejected, invalid or unrecognized evidence is not silence and breaks any silent run.
      self._silent = 0
      return RELAY_UNKNOWN
    if not self._seen_fresh:
      return RELAY_UNKNOWN
    self._silent += 1
    return RELAY_OPEN_INFERRED if self._silent >= self._needed else RELAY_UNKNOWN


class TickReference:
  """F2: a cadence tick exists only after a correctly sized, fresh reference frame was actually observed."""

  def __init__(self, expected_length: int, max_age_s: float) -> None:
    if type(expected_length) is not int or expected_length <= 0 or not _finite(max_age_s) or max_age_s <= 0:
      raise ValueError("invalid tick reference bounds")
    self._length, self._max_age = expected_length, max_age_s
    self._reset()

  def _reset(self) -> None:
    self._last_counter: int | None = None
    self._last_progress: float | None = None  # first sighting or last counter change; freshness is measured here
    self._last_seen: float | None = None      # any observation; used only for clock ordering

  def _held_or_stale(self, now_s: float) -> str:
    if self._last_progress is None:
      return NO_REFERENCE_OBSERVED
    if now_s - self._last_progress > self._max_age:
      self._reset()
      self._last_seen = now_s
      return REFERENCE_STALE
    return REFERENCE_HELD

  def observe(self, now_s: float, frame_length: int | None = None, counter: int | None = None) -> str:
    if not _finite(now_s) or (self._last_seen is not None and now_s < self._last_seen):
      self._reset()
      return NO_REFERENCE_OBSERVED
    self._last_seen = now_s
    if frame_length is None or frame_length != self._length or type(counter) is not int or counter < 0:
      return self._held_or_stale(now_s)
    if self._last_counter is None:
      self._last_counter, self._last_progress = counter, now_s
      return REFERENCE_HELD
    if counter != self._last_counter:
      self._last_counter, self._last_progress = counter, now_s
      return REFERENCE_TICK
    # A frozen counter is not a fresh reference, however often the frame repeats.
    return self._held_or_stale(now_s)


@dataclass(frozen=True, slots=True)
class StartupFaultRecord:
  """F5: raw fault, reported fault, availability and elapsed time are separate fields."""

  raw_fault: bool
  reported_fault: bool
  available: bool
  elapsed_s: float


def startup_fault_record(raw_fault: bool, elapsed_s: float, settle_s: float) -> StartupFaultRecord:
  """The reported fault always equals the raw fault; the settle window may only withhold availability."""
  if type(raw_fault) is not bool or not _finite(elapsed_s) or not _finite(settle_s) or elapsed_s < 0 or settle_s < 0:
    return StartupFaultRecord(True, True, False, 0.0)
  return StartupFaultRecord(raw_fault, raw_fault, not raw_fault and elapsed_s >= settle_s, float(elapsed_s))


def record_hides_fault(record: object) -> bool:
  """True unless the reported fault equals the raw fault and nothing is available during a fault.

  Covers MVL-style suppression (raw fault reported clear), availability during a fault, and the reverse
  inconsistency (a reported fault with no raw fault), which would also make the record untrustworthy.
  """
  if type(record) is not StartupFaultRecord:
    return True
  return record.reported_fault != record.raw_fault or (record.raw_fault and record.available)


def return_to_stock_established(stages: object) -> bool:
  """F4: every restoration stage needs physical evidence; a constructed 'enable' request alone proves nothing."""
  if type(stages) is not dict or set(stages) != set(LIFECYCLE_STAGES):
    return False
  return all(stages[name] in PHYSICAL_EVIDENCE for name in LIFECYCLE_STAGES)


def lane_metadata_consistent(metadata_revision: object, path_revision: object, latest_revision: object) -> bool:
  """F7: lead lane metadata and the lane path must come from the same, current lane snapshot."""
  values = (metadata_revision, path_revision, latest_revision)
  if not all(type(v) is int and v >= 0 for v in values):
    return False
  return metadata_revision == path_revision == latest_revision
