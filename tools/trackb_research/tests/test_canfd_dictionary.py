"""Regression check for the deterministic B1 current-source dictionary."""
import json
from pathlib import Path

from tools.trackb_research.extract_honda_canfd_dictionary import extract


ROOT = Path(__file__).resolve().parents[3]


def test_checked_in_dictionary_exactly_matches_current_source_extractor():
  checked_in = json.loads((ROOT / "docs" / "accord11g_trackb" / "CANFD_SOURCE_DICTIONARY.json").read_text(encoding="utf-8"))
  assert checked_in == extract()
  assert len(checked_in["messages"]) == 50
  assert sum(len(message["signals"]) for message in checked_in["messages"]) == 412
