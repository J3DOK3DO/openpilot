"""Offline-only symbolic models for the 17 retained MVL-inspired research IDs.

This file deliberately has no vehicle, ECU, CAN, diagnostic, packer, checksum,
or transport types.  All numeric bounds below are caller-owned test symbols,
not calibration, timing, or command values.  The records are research labels;
none represents permission to transmit or control anything.
"""

from dataclasses import dataclass
from math import isfinite


RESEARCH_ONLY = "research_only"
WITHDRAWN = "withdrawn"
UNKNOWN = "unknown"
ABSTRACT_COAST = "abstract_coast"
ABSTRACT_BRAKE = "abstract_brake"
ABSTRACT_PROPULSION = "abstract_propulsion"

_AEB_STATES = frozenset(("clear", "active", "unknown"))
_RADAR_TOPICS = frozenset(("hud", "tick", "mux", "lead", "checksum"))
_MAX_UINT64 = (1 << 64) - 1


@dataclass(frozen=True, slots=True)
class OwnershipResearchObservation:
  """Synthetic source-evidence observation for BC-009 through BC-012."""

  sequence: int
  observed_monotonic: float
  source_fresh: bool
  stock_owner_label: str
  relay_label: str
  transition_label: str
  aeb_status: str
  valid: bool


@dataclass(frozen=True, slots=True)
class OwnershipResearchRecord:
  classification: str
  reason: str
  sequence: int | None


class OwnershipTransitionResearch:
  """Classifies ambiguity and silence; it never identifies a real owner."""

  def __init__(self) -> None:
    self._last_sequence: int | None = None
    self._last_time: float | None = None

  def observe(self, observation: object) -> OwnershipResearchRecord:
    if type(observation) is not OwnershipResearchObservation:
      return OwnershipResearchRecord(WITHDRAWN, "observation_type_invalid", None)
    if not _valid_ownership(observation):
      return OwnershipResearchRecord(WITHDRAWN, "observation_invalid", observation.sequence)
    if self._last_sequence is not None and observation.sequence <= self._last_sequence:
      return OwnershipResearchRecord(WITHDRAWN, "duplicate_or_out_of_order_observation", observation.sequence)
    if self._last_time is not None and observation.observed_monotonic < self._last_time:
      return OwnershipResearchRecord(WITHDRAWN, "observation_clock_reversed", observation.sequence)
    self._last_sequence = observation.sequence
    self._last_time = observation.observed_monotonic
    if not observation.source_fresh:
      return OwnershipResearchRecord(UNKNOWN, "source_evidence_stale", observation.sequence)
    if observation.aeb_status != "clear":
      return OwnershipResearchRecord(UNKNOWN, "aeb_status_not_known_clear", observation.sequence)
    if observation.stock_owner_label != "stock_source_only":
      return OwnershipResearchRecord(UNKNOWN, "stock_owner_not_established", observation.sequence)
    if observation.relay_label != "ambiguous":
      return OwnershipResearchRecord(UNKNOWN, "relay_not_ambiguous_source_only", observation.sequence)
    if observation.transition_label == "silent_transition_observed":
      return OwnershipResearchRecord(UNKNOWN, "silent_transition_failure_observed", observation.sequence)
    return OwnershipResearchRecord(RESEARCH_ONLY, "stock_owner_source_only_relay_ambiguous", observation.sequence)


@dataclass(frozen=True, slots=True)
class RadarMetadataObservation:
  """A symbolic claim topic, never a frame, payload, identifier, or checksum."""

  sequence: int
  topic: str
  source_claim_present: bool
  input_fresh: bool
  anomaly_label: str
  valid: bool


@dataclass(frozen=True, slots=True)
class RadarMetadataRecord:
  classification: str
  reason: str
  topic: str | None


class RadarMetadataResearch:
  """BC-020..024 metadata anomaly classifier with no operational interpretation."""

  def __init__(self) -> None:
    self._seen: set[int] = set()
    self._last_sequence: int | None = None

  def classify(self, observation: object) -> RadarMetadataRecord:
    if type(observation) is not RadarMetadataObservation:
      return RadarMetadataRecord(WITHDRAWN, "metadata_type_invalid", None)
    if not _valid_radar_metadata(observation):
      return RadarMetadataRecord(WITHDRAWN, "metadata_invalid", observation.topic if type(observation.topic) is str else None)
    if observation.sequence in self._seen:
      return RadarMetadataRecord(WITHDRAWN, "duplicate_metadata", observation.topic)
    if self._last_sequence is not None and observation.sequence <= self._last_sequence:
      return RadarMetadataRecord(WITHDRAWN, "out_of_order_metadata", observation.topic)
    self._seen.add(observation.sequence)
    self._last_sequence = observation.sequence
    if not observation.input_fresh:
      return RadarMetadataRecord(UNKNOWN, "metadata_stale", observation.topic)
    if not observation.source_claim_present:
      return RadarMetadataRecord(UNKNOWN, "source_claim_missing", observation.topic)
    if observation.anomaly_label != "none":
      return RadarMetadataRecord(UNKNOWN, "metadata_anomaly:" + observation.anomaly_label, observation.topic)
    return RadarMetadataRecord(RESEARCH_ONLY, "source_claim_metadata_only", observation.topic)


@dataclass(frozen=True, slots=True)
class BrakeResearchInput:
  """Abstract, synthetic values for DRV-001/003/005..010; never motion inputs."""

  sequence: int
  target_value: float
  corrected_value: float
  driver_brake: bool
  driver_gas: bool
  fault_latched: bool
  restart: bool
  rearm: bool
  valid: bool


@dataclass(frozen=True, slots=True)
class BrakeResearchPolicy:
  """Test-only symbolic thresholds, not vehicle limits or calibration."""

  symbolic_brake_entry: float
  symbolic_brake_release: float
  symbolic_integrator_floor: float
  symbolic_relaxation_step: float
  symbolic_near_zero_negative: float


@dataclass(frozen=True, slots=True)
class BrakeResearchRecord:
  classification: str
  reason: str
  selected_path: str | None
  symbolic_integrator: float | None
  target_value: float | None
  corrected_value: float | None


class BrakeSelectionResearch:
  """Fail-closed symbolic brake-selection research, with an explicit fault latch.

  ``selected_path`` is an analytical label only.  It is not a pedal, torque,
  gas, brake, acceleration, or ECU output.  A fault/restart clears state and
  requires an explicit later rearm.  Positive target values cannot re-enter
  the abstract brake path, even when a separate corrected value is negative.
  """

  def __init__(self) -> None:
    self._last_sequence: int | None = None
    self._fault_latched = False
    self._integrator = 0.0

  def evaluate(self, candidate: object, policy: object) -> BrakeResearchRecord:
    if type(candidate) is not BrakeResearchInput or type(policy) is not BrakeResearchPolicy:
      return self._withdraw("input_type_invalid", candidate)
    if not _valid_brake(candidate, policy):
      return self._withdraw("input_invalid", candidate)
    if self._last_sequence is not None and candidate.sequence <= self._last_sequence:
      return self._withdraw("duplicate_or_out_of_order_input", candidate)
    self._last_sequence = candidate.sequence
    if candidate.fault_latched or candidate.restart:
      return self._withdraw("fault_or_restart_latched", candidate)
    if candidate.driver_brake or candidate.driver_gas:
      return self._withdraw("driver_override", candidate)
    if self._fault_latched:
      if not candidate.rearm:
        return self._record(WITHDRAWN, "rearm_required", None, candidate)
      self._fault_latched = False
      self._integrator = 0.0
    if candidate.target_value > 0.0 and candidate.corrected_value < 0.0:
      return self._record(UNKNOWN, "positive_target_brake_reentry_suppressed", ABSTRACT_COAST, candidate)
    # Include signed zero deliberately: it remains a symbolic tolerance result,
    # never an operational neutral/permission signal.
    if -policy.symbolic_near_zero_negative <= candidate.corrected_value <= 0.0:
      self._integrator = 0.0
      return self._record(RESEARCH_ONLY, "near_zero_negative_relaxed", ABSTRACT_COAST, candidate)
    if candidate.corrected_value <= policy.symbolic_brake_entry:
      self._integrator = max(policy.symbolic_integrator_floor, candidate.corrected_value)
      return self._record(RESEARCH_ONLY, "abstract_brake_selected", ABSTRACT_BRAKE, candidate)
    if self._integrator < 0.0 and candidate.corrected_value > self._integrator:
      self._integrator = min(0.0, self._integrator + policy.symbolic_relaxation_step)
      return self._record(RESEARCH_ONLY, "one_sided_relaxation_limited", ABSTRACT_BRAKE, candidate)
    self._integrator = 0.0
    path = ABSTRACT_PROPULSION if candidate.target_value > 0.0 else ABSTRACT_COAST
    return self._record(RESEARCH_ONLY, "abstract_non_brake_selection", path, candidate)

  def _withdraw(self, reason: str, candidate: object) -> BrakeResearchRecord:
    self._fault_latched = True
    self._integrator = 0.0
    return self._record(WITHDRAWN, reason, None, candidate)

  def _record(self, classification: str, reason: str, selected_path: str | None, candidate: object) -> BrakeResearchRecord:
    if type(candidate) is BrakeResearchInput:
      return BrakeResearchRecord(classification, reason, selected_path, self._integrator, candidate.target_value, candidate.corrected_value)
    return BrakeResearchRecord(classification, reason, selected_path, self._integrator, None, None)


def _finite(value: object) -> bool:
  return type(value) is float and isfinite(value)


def _valid_ownership(value: OwnershipResearchObservation) -> bool:
  return (type(value.sequence) is int and 0 < value.sequence <= _MAX_UINT64 and _finite(value.observed_monotonic) and
          type(value.source_fresh) is bool and type(value.valid) is bool and value.valid and
          type(value.stock_owner_label) is str and type(value.relay_label) is str and
          type(value.transition_label) is str and type(value.aeb_status) is str and
          value.stock_owner_label in {"stock_source_only", "unknown"} and value.relay_label in {"ambiguous", "claimed"} and
          value.transition_label in {"none", "silent_transition_observed"} and value.aeb_status in _AEB_STATES)


def _valid_radar_metadata(value: RadarMetadataObservation) -> bool:
  return (type(value.sequence) is int and 0 < value.sequence <= _MAX_UINT64 and type(value.topic) is str and
          value.topic in _RADAR_TOPICS and type(value.source_claim_present) is bool and type(value.input_fresh) is bool and
          type(value.anomaly_label) is str and bool(value.anomaly_label) and value.anomaly_label == value.anomaly_label.strip() and
          type(value.valid) is bool and value.valid)


def _valid_brake(value: BrakeResearchInput, policy: BrakeResearchPolicy) -> bool:
  return (type(value.sequence) is int and 0 < value.sequence <= _MAX_UINT64 and
          all(_finite(item) for item in (value.target_value, value.corrected_value, policy.symbolic_brake_entry,
                                         policy.symbolic_brake_release, policy.symbolic_integrator_floor,
                                         policy.symbolic_relaxation_step, policy.symbolic_near_zero_negative)) and
          all(type(item) is bool for item in (value.driver_brake, value.driver_gas, value.fault_latched,
                                              value.restart, value.rearm, value.valid)) and value.valid and
          policy.symbolic_integrator_floor <= policy.symbolic_brake_entry <= policy.symbolic_brake_release <= 0.0 and
          policy.symbolic_relaxation_step > 0.0 and
          0.0 <= policy.symbolic_near_zero_negative <= -policy.symbolic_brake_release)
