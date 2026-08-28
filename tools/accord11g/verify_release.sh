#!/usr/bin/env bash
set -Eeuo pipefail

readonly BASE="227b5cf82ac7ace1e86d5a568c3fb2a0b5d95b2f"
readonly DRIVING_CHECKPOINT="a9b496c83270111602676458e30f8287a1eff367"
readonly DIAGNOSTIC_CHECKPOINT="83d1762b7355c66690b12a6c6c0bb2789bfbcd99"
readonly INTEGRATION_CHECKPOINT="39733a035068e74e321dc4a2db408662aabe268d"
readonly EXPECTED_WHITESPACE_REPORT="selfdrive/controls/tests/test_mvl_accord_radar.py:425: new blank line at EOF."

readonly COMMITS=(
  "d7747872fe50faff106381ec9f1b55559b659ea8"
  "0b4af9504ed38877d2c6528c75fb14b0f984a386"
  "643879a879a222714b6e4580231f2bd9ddf4d15e"
  "620db5f1904b2227555b0e9413469bc98a151a9f"
  "c7ff6f79faf5cd3942ccb934d8a0a6e01d313a6b"
  "01fa130fb4b729603cae54df7873f6515a419d28"
  "a9b496c83270111602676458e30f8287a1eff367"
  "83d1762b7355c66690b12a6c6c0bb2789bfbcd99"
  "39733a035068e74e321dc4a2db408662aabe268d"
)

readonly PARENTS=(
  "$BASE"
  "d7747872fe50faff106381ec9f1b55559b659ea8"
  "0b4af9504ed38877d2c6528c75fb14b0f984a386"
  "643879a879a222714b6e4580231f2bd9ddf4d15e"
  "620db5f1904b2227555b0e9413469bc98a151a9f"
  "c7ff6f79faf5cd3942ccb934d8a0a6e01d313a6b"
  "01fa130fb4b729603cae54df7873f6515a419d28"
  "a9b496c83270111602676458e30f8287a1eff367"
  "83d1762b7355c66690b12a6c6c0bb2789bfbcd99"
)

readonly HASHES=(
  "6f45b1307be12d7b2aea72c9f2defb775f851f834c1a0e3b064d79abb83a73d6"
  "044f54f6d91feba4c1a5beae77d3724c00704329c4d434103abc1bf5a666133a"
  "3ee6dc3cbf5636107f666bf57675abe259cc1801cd829fb6b35d88729132f025"
  "bc6ae6b96dc79fadc762e34910657fa6dc0264ca37de9ad8ae6038b45a5895fb"
  "749436fc853c7197db7f6bd2ec81c553761a11b418cc2d2b28c75273c539cc20"
  "3d4452c4fa0e51ced7b29cec218249cfd4ac777563fabf4ee24c2a7a75820ca3"
  "779d7bf03dd94d15e2cb642ea58b3923ee8e76546d332469ea2a504c68102fb9"
  "f25572e0a921856177b7c0689b32daa4d83d99da6bab310b708ac4e2ba173fc1"
  "d9d6fc2479e4d4a95b288fd3d00c5a88e9d08dbd8811180fa27816f13e7d578e"
)

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

usage() {
  printf 'Usage: %s [--run-tests]\n' "$0"
}

ensure_protected_sources_clean() {
  local path
  while IFS= read -r path; do
    git diff --quiet -- "$path" || fail "protected source has unstaged changes: $path"
    git diff --cached --quiet -- "$path" || fail "protected source has staged changes: $path"
  done < <(git diff --name-only "$BASE..$INTEGRATION_CHECKPOINT")
}

run_tests=false
case "${1:-}" in
  "") ;;
  --run-tests) run_tests=true ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac
[[ $# -le 1 ]] || { usage >&2; exit 2; }

for command_name in git sha256sum awk grep file uname; do
  command -v "$command_name" >/dev/null 2>&1 || fail "required command is missing: $command_name"
done

root="$(git rev-parse --show-toplevel 2>/dev/null)" || fail "not inside a Git worktree"
cd "$root"

git cat-file -e "$BASE^{commit}" 2>/dev/null || fail "protected base is missing: $BASE"
git merge-base --is-ancestor "$INTEGRATION_CHECKPOINT" HEAD || fail "HEAD is not a descendant of the integration checkpoint"

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
[[ "${COMMITS[7]}" == "$DIAGNOSTIC_CHECKPOINT" ]] || fail "internal diagnostic-checkpoint manifest error"
[[ "${COMMITS[8]}" == "$INTEGRATION_CHECKPOINT" ]] || fail "internal integration-checkpoint manifest error"

whitespace_report="$(git diff --check "$BASE..$INTEGRATION_CHECKPOINT" || true)"
if [[ -n "$whitespace_report" && "$whitespace_report" != "$EXPECTED_WHITESPACE_REPORT" ]]; then
  printf '%s\n' "$whitespace_report" >&2
  fail "unexpected whitespace errors in protected range"
fi
if [[ "$whitespace_report" == "$EXPECTED_WHITESPACE_REPORT" ]]; then
  printf 'verified known historical whitespace exception: %s\n' "$EXPECTED_WHITESPACE_REPORT"
fi
if git diff --name-only "$DIAGNOSTIC_CHECKPOINT^..$DIAGNOSTIC_CHECKPOINT" | grep -q 'radar_interface'; then
  fail "diagnostic checkpoint unexpectedly changes a radar interface"
fi

ensure_protected_sources_clean

if [[ "$run_tests" == true ]]; then
  command -v uv >/dev/null 2>&1 || fail "required command is missing: uv"
  [[ "$(uname -m)" == "x86_64" ]] || fail "host test architecture must be x86_64; found $(uname -m)"

  critical_artifacts=(
    "msgq_repo/msgq/ipc_pyx.so"
    "common/transformations/transformations.so"
    "common/params_pyx.so"
    "selfdrive/controls/lib/longitudinal_mpc_lib/c_generated_code/acados_ocp_solver_pyx.so"
    "selfdrive/controls/lib/longitudinal_mpc_lib/c_generated_code/libacados_ocp_solver_long.so"
    "rednose_repo/rednose/helpers/ekf_sym_pyx.so"
  )
  for artifact in "${critical_artifacts[@]}"; do
    [[ -f "$artifact" ]] || fail "missing native test artifact: $artifact; perform the clean full host build first"
    artifact_description="$(file -b "$artifact")"
    printf '%s: %s\n' "$artifact" "$artifact_description"
    grep -q 'x86-64' <<<"$artifact_description" || fail "native test artifact is not x86-64: $artifact"
  done

  mapfile -t python_files < <(git diff --name-only "$BASE..$INTEGRATION_CHECKPOINT" | grep -E '\.py$')
  ((${#python_files[@]} > 0)) || fail "no Python files found in protected range"
  ruff_files=()
  for python_file in "${python_files[@]}"; do
    case "$python_file" in
      selfdrive/controls/controlsd.py|selfdrive/controls/lib/latcontrol_pid.py|selfdrive/controls/lib/latcontrol_torque.py|selfdrive/modeld/modeld.py)
        printf 'skipping known protected full-file Ruff debt: %s\n' "$python_file"
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
  ensure_protected_sources_clean
else
  [[ -z "$(git status --porcelain)" ]] || fail "worktree is not clean"
fi

printf 'Accord 11G latest-DOM release verification passed at %s\n' "$(git rev-parse HEAD)"
