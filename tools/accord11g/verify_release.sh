#!/usr/bin/env bash
set -euo pipefail

readonly BASE="b7393ad04a7b692dda95240fbe4bba3af156b926"
readonly DRIVING_CHECKPOINT="a16bd673f84f6570b51cd14ce2f6964ae2957502"
readonly DIAGNOSTIC_CHECKPOINT="2ca2ef43bd5bb7159e02d1f94d0fc467d58e77e7"
readonly EXPECTED_WHITESPACE_REPORT="selfdrive/controls/tests/test_mvl_accord_radar.py:425: new blank line at EOF."

readonly COMMITS=(
  "94161bc09cc7927a0ed7e2dae50d9bbcbaad6b98"
  "917527727478d3079901706b580aa0e3800d359e"
  "690b3e073c9ab3f7097af072c934aa3b3b6bd5c4"
  "00db2fcf9cead3fdd46bc501d15bf4e5d866d9ba"
  "00ebd3aead3e451c64c7a362b3c8911e490ab242"
  "8e79ba1b358e4a669ca975276035ec3c455032aa"
  "a16bd673f84f6570b51cd14ce2f6964ae2957502"
  "2ca2ef43bd5bb7159e02d1f94d0fc467d58e77e7"
)

readonly PARENTS=(
  "$BASE"
  "94161bc09cc7927a0ed7e2dae50d9bbcbaad6b98"
  "917527727478d3079901706b580aa0e3800d359e"
  "690b3e073c9ab3f7097af072c934aa3b3b6bd5c4"
  "00db2fcf9cead3fdd46bc501d15bf4e5d866d9ba"
  "00ebd3aead3e451c64c7a362b3c8911e490ab242"
  "8e79ba1b358e4a669ca975276035ec3c455032aa"
  "a16bd673f84f6570b51cd14ce2f6964ae2957502"
)

readonly HASHES=(
  "26ed1ecc8f1d1c527806940f8a8a02ccfdece00731f0050fd04312a541132564"
  "a602b3057437fb794f60e8e11dd6a3df18e1009110e55c98a9c2f242e49cac8f"
  "53be74854855c0f007313d5c9d946d427cd4d06a53c8a96e5ce0faf1a3694ca3"
  "44483f4ae16a4a246529bdfce8591f2c5a78f60438d898172b10bf4a525a5511"
  "749436fc853c7197db7f6bd2ec81c553761a11b418cc2d2b28c75273c539cc20"
  "3d4452c4fa0e51ced7b29cec218249cfd4ac777563fabf4ee24c2a7a75820ca3"
  "779d7bf03dd94d15e2cb642ea58b3923ee8e76546d332469ea2a504c68102fb9"
  "f25572e0a921856177b7c0689b32daa4d83d99da6bab310b708ac4e2ba173fc1"
)

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

usage() {
  echo "Usage: $0 [--run-tests]"
}

run_tests=false
case "${1:-}" in
  "") ;;
  --run-tests) run_tests=true ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac
[[ $# -le 1 ]] || { usage >&2; exit 2; }

root="$(git rev-parse --show-toplevel 2>/dev/null)" || fail "not inside a Git worktree"
cd "$root"

git cat-file -e "$BASE^{commit}" 2>/dev/null || fail "protected base is missing: $BASE"
git merge-base --is-ancestor "$DIAGNOSTIC_CHECKPOINT" HEAD || fail "HEAD is not a descendant of the diagnostic checkpoint"

for i in "${!COMMITS[@]}"; do
  commit="${COMMITS[$i]}"
  expected_parent="${PARENTS[$i]}"
  expected_hash="${HASHES[$i]}"
  git cat-file -e "$commit^{commit}" 2>/dev/null || fail "missing commit: $commit"
  actual_parent="$(git rev-parse "$commit^")"
  [[ "$actual_parent" == "$expected_parent" ]] || fail "$commit parent is $actual_parent, expected $expected_parent"
  actual_hash="$(git diff "$commit^..$commit" --binary | sha256sum | awk '{print $1}')"
  [[ "$actual_hash" == "$expected_hash" ]] || fail "$commit hash is $actual_hash, expected $expected_hash"
  printf 'verified %s  %s\n' "$commit" "$actual_hash"
done

[[ "${COMMITS[6]}" == "$DRIVING_CHECKPOINT" ]] || fail "internal driving-checkpoint manifest error"
whitespace_report="$(git diff --check "$BASE..$DIAGNOSTIC_CHECKPOINT" || true)"
if [[ -n "$whitespace_report" && "$whitespace_report" != "$EXPECTED_WHITESPACE_REPORT" ]]; then
  printf '%s\n' "$whitespace_report" >&2
  fail "unexpected whitespace errors in protected range"
fi
if [[ "$whitespace_report" == "$EXPECTED_WHITESPACE_REPORT" ]]; then
  echo "verified known historical whitespace exception: $EXPECTED_WHITESPACE_REPORT"
fi
if git diff --name-only "$DIAGNOSTIC_CHECKPOINT^..$DIAGNOSTIC_CHECKPOINT" | grep -q 'radar_interface'; then
  fail "diagnostic checkpoint unexpectedly changes a radar interface"
fi

if [[ "$run_tests" == true ]]; then
  mapfile -t python_files < <(git diff --name-only "$BASE..$DIAGNOSTIC_CHECKPOINT" | grep -E '\.py$')
  ((${#python_files[@]} > 0)) || fail "no Python files found in protected range"
  ruff_files=()
  for python_file in "${python_files[@]}"; do
    case "$python_file" in
      selfdrive/controls/controlsd.py|selfdrive/controls/lib/latcontrol_pid.py|selfdrive/modeld/modeld.py)
        echo "skipping known protected full-file Ruff debt: $python_file"
        ;;
      *) ruff_files+=("$python_file") ;;
    esac
  done
  ((${#ruff_files[@]} > 0)) || fail "no Ruff-eligible Python files found in protected range"
  uv run ruff check "${ruff_files[@]}"
  uv run python -m pytest -q selfdrive/controls/tests/test_mvl_accord_longitudinal.py
  uv run python -m pytest -q selfdrive/controls/tests/test_mvl_accord_radar.py
  uv run python -m pytest -q selfdrive/controls/tests/test_mvl_accord_lateral.py
  uv run python -m pytest -q selfdrive/controls/tests/test_latcontrol.py
  uv run python -m pytest -q --confcutdir=opendbc_repo \
    opendbc_repo/opendbc/can/tests/test_packer_parser.py \
    opendbc_repo/opendbc/car/honda/tests/test_honda.py
  uv run python -m pytest -q --confcutdir=selfdrive/locationd/test \
    selfdrive/locationd/test/test_paramsd.py \
    selfdrive/locationd/test/test_lagd.py \
    -k "not read_saved_params"
fi

if [[ -n "$(git status --porcelain)" ]]; then
  fail "worktree is not clean"
fi

echo "Accord 11G release verification passed at $(git rev-parse HEAD)"
