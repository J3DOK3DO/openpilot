"""Discriminating synthetic tests for the MVL architecture-delta findings F1, F2, F4, F5 and F7."""
import pytest

from tools.trackb_research.source_evidence_contracts import (
  ABSENT, FRESH, INVALID, LIFECYCLE_STAGES, NO_REFERENCE_OBSERVED, REFERENCE_HELD, REFERENCE_STALE, REFERENCE_TICK,
  REJECTED, RELAY_CLOSED_INFERRED, RELAY_OPEN_INFERRED, RELAY_UNKNOWN, STALE, RelayInference, StartupFaultRecord,
  StreamWindow, TickReference, classify_stream, lane_metadata_consistent, record_hides_fault,
  return_to_stock_established, startup_fault_record,
)

MAX_AGE = 0.1  # symbolic


# F1 — silence vs rejection vs staleness

@pytest.mark.parametrize("window,expected", (
  (StreamWindow(0, 0, None), ABSENT),
  (StreamWindow(5, 0, None), REJECTED),
  (StreamWindow(5, 0, 0.05), REJECTED),
  (StreamWindow(0, 0, 0.5), STALE),
  (StreamWindow(0, 0, 0.05), FRESH),
  (StreamWindow(3, 1, 0.01), FRESH),
))
def test_stream_classes_are_distinct(window, expected):
  assert classify_stream(window, MAX_AGE) == expected


@pytest.mark.parametrize("window", (
  StreamWindow(1, 2, 0.0), StreamWindow(-1, 0, None), StreamWindow(1, 1, None), StreamWindow(1, 1, 0.5),
  StreamWindow(0, 0, float("nan")), StreamWindow(0, 0, -1.0), StreamWindow(True, 0, None), "frame",
))
def test_contradictory_or_malformed_windows_are_invalid(window):
  assert classify_stream(window, MAX_AGE) == INVALID


def test_rejected_frames_are_never_reported_as_silence():
  assert classify_stream(StreamWindow(10, 0, None), MAX_AGE) != ABSENT


def test_relay_open_requires_silence_after_seeing_camera_fresh():
  relay = RelayInference(5)
  assert [relay.observe(STALE) for _ in range(10)] == [RELAY_UNKNOWN] * 10  # never seen: no inference
  assert relay.observe(FRESH) == RELAY_CLOSED_INFERRED
  assert [relay.observe(STALE) for _ in range(5)] == [RELAY_UNKNOWN] * 4 + [RELAY_OPEN_INFERRED]


def test_continuous_camera_frames_never_infer_open_even_after_500_updates():
  # MVL's 500-update fallback would label the relay open here; this contract must not.
  relay = RelayInference(5)
  assert {relay.observe(FRESH) for _ in range(1000)} == {RELAY_CLOSED_INFERRED}


@pytest.mark.parametrize("anomaly", (REJECTED, INVALID, "unexpected"))
def test_rejected_or_invalid_camera_stream_resets_silence_and_is_unknown(anomaly):
  relay = RelayInference(3)
  relay.observe(FRESH)
  relay.observe(STALE)
  relay.observe(STALE)
  assert relay.observe(anomaly) == RELAY_UNKNOWN
  assert [relay.observe(STALE) for _ in range(3)] == [RELAY_UNKNOWN, RELAY_UNKNOWN, RELAY_OPEN_INFERRED]


def test_relay_labels_are_inferences_not_measurements():
  assert all("inferred" in label or label == RELAY_UNKNOWN for label in (RELAY_OPEN_INFERRED, RELAY_CLOSED_INFERRED, RELAY_UNKNOWN))
  with pytest.raises(ValueError):
    RelayInference(0)


# F2 — tick cadence needs an observed reference

def test_no_tick_without_an_observed_reference_however_many_updates():
  tick = TickReference(16, 1.0)
  assert {tick.observe(t * 0.01) for t in range(500)} == {NO_REFERENCE_OBSERVED}


def test_wrong_length_reference_is_not_a_reference():
  tick = TickReference(16, 1.0)
  assert tick.observe(0.0, 32, 1) == NO_REFERENCE_OBSERVED
  assert tick.observe(0.1, 6, 2) == NO_REFERENCE_OBSERVED
  assert tick.observe(0.2) == NO_REFERENCE_OBSERVED


def test_tick_only_on_counter_change_of_a_valid_fresh_reference_then_stale():
  tick = TickReference(16, 1.0)
  assert tick.observe(0.0, 16, 1) == REFERENCE_HELD   # first sighting establishes, does not tick
  assert tick.observe(0.1, 16, 1) == REFERENCE_HELD   # duplicate counter
  assert tick.observe(0.2, 16, 2) == REFERENCE_TICK
  assert tick.observe(0.3) == REFERENCE_HELD
  assert tick.observe(1.5) == REFERENCE_STALE
  assert tick.observe(1.6) == NO_REFERENCE_OBSERVED
  assert tick.observe(1.7, 16, 3) == REFERENCE_HELD   # re-established, no tick from the stale history


def test_frozen_counter_goes_stale_however_often_the_frame_repeats():
  # Codex RB1: repeated same-counter frames must not keep a reference fresh.
  tick = TickReference(16, 1.0)
  assert tick.observe(0.0, 16, 5) == REFERENCE_HELD
  assert [tick.observe(t / 10, 16, 5) for t in range(1, 11)] == [REFERENCE_HELD] * 10
  assert tick.observe(1.05, 16, 5) == REFERENCE_STALE
  assert tick.observe(1.1, 16, 6) == REFERENCE_HELD   # re-established; the frozen history yields no tick


def test_clock_reversal_drops_the_reference():
  tick = TickReference(16, 1.0)
  tick.observe(1.0, 16, 1)
  assert tick.observe(0.5, 16, 2) == NO_REFERENCE_OBSERVED
  assert tick.observe(0.6, 16, 3) == REFERENCE_HELD


# F5 — startup faults are never hidden

@pytest.mark.parametrize("elapsed", (0.0, 5.0, 10.0, 60.0))
def test_raw_fault_is_always_reported_and_never_available(elapsed):
  record = startup_fault_record(True, elapsed, 10.0)
  assert record.raw_fault and record.reported_fault and not record.available
  assert not record_hides_fault(record)


def test_settle_window_only_withholds_availability():
  assert startup_fault_record(False, 5.0, 10.0) == StartupFaultRecord(False, False, False, 5.0)
  assert startup_fault_record(False, 10.0, 10.0) == StartupFaultRecord(False, False, True, 10.0)


@pytest.mark.parametrize("record", (
  StartupFaultRecord(True, False, False, 3.0),   # MVL startup suppression: reported clear while raw fault present
  StartupFaultRecord(True, True, True, 30.0),    # available during a fault
  StartupFaultRecord(False, True, False, 3.0),   # reported fault without a raw fault (inconsistent record)
  "record",
))
def test_suppressed_or_inconsistent_records_are_detected(record):
  assert record_hides_fault(record)


def test_invalid_startup_inputs_fail_closed():
  assert startup_fault_record("no", 1.0, 1.0) == StartupFaultRecord(True, True, False, 0.0)
  assert startup_fault_record(False, float("nan"), 1.0).available is False


# F4 — restoration to stock needs physical evidence at every stage

def test_constructed_enable_request_alone_does_not_restore_stock():
  stages = dict.fromkeys(LIFECYCLE_STAGES, "unknown")
  stages["request_constructed"] = "source_only"
  assert not return_to_stock_established(stages)


@pytest.mark.parametrize("weak_stage", LIFECYCLE_STAGES)
@pytest.mark.parametrize("weak_kind", ("source_only", "synthetic_only", "unknown"))
def test_any_stage_without_physical_evidence_holds(weak_stage, weak_kind):
  stages = dict.fromkeys(LIFECYCLE_STAGES, "target_measurement")
  stages[weak_stage] = weak_kind
  assert not return_to_stock_established(stages)


def test_only_complete_physical_evidence_establishes_return_and_shape_is_exact():
  assert return_to_stock_established(dict.fromkeys(LIFECYCLE_STAGES, "target_measurement"))
  assert not return_to_stock_established(dict.fromkeys(LIFECYCLE_STAGES[:-1], "target_measurement"))
  assert not return_to_stock_established({**dict.fromkeys(LIFECYCLE_STAGES, "oem_authenticated"), "extra": "oem_authenticated"})
  assert not return_to_stock_established([("request_constructed", "oem_authenticated")])


# F7 — lane metadata and path from one current snapshot

def test_lane_metadata_and_path_must_share_the_current_revision():
  assert lane_metadata_consistent(7, 7, 7)
  assert not lane_metadata_consistent(6, 7, 7)   # MVL ordering: metadata from the previous cached snapshot
  assert not lane_metadata_consistent(7, 7, 8)   # missed refresh
  assert not lane_metadata_consistent(7, 7.0, 7)
  assert not lane_metadata_consistent(-1, -1, -1)
