"""Pure, non-actuating Bosch-C ownership-evidence state model.

This accepts caller-created synthetic observations only. It does not decode,
transmit, forward, or suppress CAN/UDS traffic, and it is never imported by
production code. Its result labels evidence quality; it grants no authority.
"""

from dataclasses import dataclass
from math import isfinite

STATE_UNKNOWN = "unknown"
STATE_OBSERVED_STOCK = "observed_stock"
STATE_WITHDRAWN = "withdrawn"
_AEB_STATES = frozenset(("clear", "active", "unknown"))
_MAX_UINT64 = (1 << 64) - 1


@dataclass(frozen=True, slots=True)
class OwnershipObservation:
  """Synthetic, manually supplied evidence—not a vehicle or CAN object."""

  observation_id: int
  observed_monotonic: float
  stock_acc_enabled: bool
  aeb_cmbs_state: str
  diagnostics_requested: bool
  radar_suppression_requested: bool
  relay_state_claim: str
  topology_claim: str
  source_complete: bool
  valid: bool


@dataclass(frozen=True, slots=True)
class OwnershipEvidence:
  """A non-operational research result; state is not a control state."""

  state: str
  reason: str
  observation_id: int | None


class OwnershipEvidenceModel:
  """Fail closed unless source-only evidence describes retained stock ownership."""

  def __init__(self) -> None:
    self._last_id: int | None = None
    self._last_time: float | None = None

  def assess(self, observation: object) -> OwnershipEvidence:
    if type(observation) is not OwnershipObservation:
      return OwnershipEvidence(STATE_WITHDRAWN, "observation_type_invalid", None)
    if not _valid_shape(observation):
      return OwnershipEvidence(STATE_WITHDRAWN, "observation_shape_invalid", observation.observation_id)
    if self._last_id is not None and observation.observation_id <= self._last_id:
      return OwnershipEvidence(STATE_WITHDRAWN, "duplicate_or_out_of_order_observation", observation.observation_id)
    if self._last_time is not None and observation.observed_monotonic < self._last_time:
      return OwnershipEvidence(STATE_WITHDRAWN, "observation_clock_reversed", observation.observation_id)

    self._last_id = observation.observation_id
    self._last_time = observation.observed_monotonic
    if observation.diagnostics_requested:
      return OwnershipEvidence(STATE_WITHDRAWN, "diagnostics_prohibited", observation.observation_id)
    if observation.radar_suppression_requested:
      return OwnershipEvidence(STATE_WITHDRAWN, "radar_suppression_prohibited", observation.observation_id)
    if observation.aeb_cmbs_state != "clear":
      return OwnershipEvidence(STATE_UNKNOWN, "aeb_cmbs_not_clear", observation.observation_id)
    if not observation.stock_acc_enabled:
      return OwnershipEvidence(STATE_UNKNOWN, "stock_acc_not_enabled", observation.observation_id)
    if not observation.source_complete:
      return OwnershipEvidence(STATE_UNKNOWN, "source_evidence_incomplete", observation.observation_id)
    if observation.relay_state_claim != "unverified" or observation.topology_claim != "source_only":
      return OwnershipEvidence(STATE_UNKNOWN, "physical_claim_not_accepted", observation.observation_id)
    return OwnershipEvidence(STATE_OBSERVED_STOCK, "stock_ownership_retained_source_only", observation.observation_id)


def _valid_shape(observation: OwnershipObservation) -> bool:
  return (
    type(observation.observation_id) is int
    and 0 < observation.observation_id <= _MAX_UINT64
    and type(observation.observed_monotonic) is float
    and isfinite(observation.observed_monotonic)
    and type(observation.stock_acc_enabled) is bool
    and type(observation.diagnostics_requested) is bool
    and type(observation.radar_suppression_requested) is bool
    and type(observation.source_complete) is bool
    and type(observation.valid) is bool
    and observation.valid
    and type(observation.aeb_cmbs_state) is str
    and observation.aeb_cmbs_state in _AEB_STATES
    and type(observation.relay_state_claim) is str
    and observation.relay_state_claim in {"unverified", "claimed_open", "claimed_closed"}
    and type(observation.topology_claim) is str
    and observation.topology_claim in {"source_only", "physical_claim"}
  )
