#!/usr/bin/env bash
# Guard ONLY the in-process, ordinary rename-failure window of an app update.
# Does NOT provide reboot/power-loss/startup-health rollback or authenticity.
# Return codes: 0 activated; 10 preflight; 20 first mv; 30 restored old after
# second mv failed; 40 unrecovered/unknown active state. Caller MUST stop on 40.

_g8_same_inode() {
  local path="$1" expected="$2" actual
  [[ -d "$path" && ! -L "$path" ]] || return 1
  actual="$(stat -c '%d:%i' -- "$path")" || return 1
  [[ "$actual" == "$expected" ]]
}

_g8_canonical_realpath() {
  local path="$1" actual
  [[ -e "$path" && ! -L "$path" ]] || return 1
  actual="$(readlink -e -- "$path")" || return 1
  [[ "$actual" == "$path" ]]
}

g8_activation_preflight() {
  local active="$1" root="$2" candidate="$2/finalized" backup="$2/old_openpilot"
  local d1 d2 d3 item
  case "$active" in
    /*) ;;
    *) echo "g8: active must be an absolute canonical path" >&2; return 10 ;;
  esac
  case "$root" in
    /*) ;;
    *) echo "g8: staging root must be an absolute canonical path" >&2; return 10 ;;
  esac
  if [[ "$active" == *:* || "$root" == *:* ||
        "$active" == "$root" ||
        "$active" == "$root/"* || "$root" == "$active/"* ||
        "$(dirname "$active")" != "$(dirname "$root")" ]]; then
    echo "g8: invalid or overlapping active/staging paths" >&2
    return 10
  fi
  for item in "$active" "$root" "$candidate"; do
    if [[ ! -d "$item" ]] || ! _g8_canonical_realpath "$item"; then
      echo "g8: noncanonical/symlinked/missing active or staging directory: $item" >&2
      return 10
    fi
  done
  if [[ -e "$backup" || -L "$backup" ]]; then
    echo "g8: prior backup exists; refusing activation" >&2
    return 10
  fi
  if [[ ! -f "$candidate/.overlay_consistent" || -L "$candidate/.overlay_consistent" ]]; then
    echo "g8: missing/invalid completed-stage consistency marker" >&2
    return 10
  fi
  for item in "$candidate/launch_chffrplus.sh" "$candidate/launch_env.sh" "$candidate/system/manager/manager.py"; do
    if [[ ! -f "$item" ]] || ! _g8_canonical_realpath "$item"; then
      echo "g8: missing/noncanonical launcher dependency: $item" >&2
      return 10
    fi
  done
  if [[ ! -x "$candidate/launch_chffrplus.sh" ||
        ! -x "$candidate/system/manager/manager.py" ]]; then
    echo "g8: required launcher or manager not executable" >&2
    return 10
  fi
  d1="$(stat -c %d -- "$active")" || return 10
  d2="$(stat -c %d -- "$root")" || return 10
  d3="$(stat -c %d -- "$candidate")" || return 10
  if [[ "$d1" != "$d2" || "$d2" != "$d3" ]]; then
    echo "g8: cross-device rename unsafe" >&2
    return 10
  fi
}

g8_activate_staged_update() {
  local active="$1" root="$2" candidate="$2/finalized" backup="$2/old_openpilot"
  local old_id cand_id
  g8_activation_preflight "$active" "$root" || return 10
  old_id="$(stat -c '%d:%i' -- "$active")" || return 10
  cand_id="$(stat -c '%d:%i' -- "$candidate")" || return 10

  # GNU --no-clobber: a concurrently created backup must never be overwritten.
  if ! mv -T -n -- "$active" "$backup"; then
    echo "g8: initial backup rename failed" >&2
    return 20
  fi
  if ! _g8_same_inode "$backup" "$old_id" || [[ -e "$active" || -L "$active" ]]; then
    echo "g8: backup rename postcondition failed (possible race); refusing promotion" >&2
    return 20
  fi

  # This is NOT atomic across both renames or durable across power loss.
  if mv -T -n -- "$candidate" "$active" &&
     _g8_same_inode "$active" "$cand_id" &&
     [[ ! -e "$candidate" && ! -L "$candidate" ]]; then
    echo "g8: candidate renamed into place, awaiting independent health validation"
    return 0
  fi

  echo "g8: activation failed; attempting immediate restoration" >&2
  if [[ ! -e "$active" && ! -L "$active" ]] &&
     _g8_same_inode "$backup" "$old_id" &&
     mv -T -n -- "$backup" "$active" &&
     _g8_same_inode "$active" "$old_id" &&
     [[ ! -e "$backup" && ! -L "$backup" ]]; then
    echo "g8: prior app restored; new candidate not activated" >&2
    return 30
  fi

  echo "g8: CRITICAL: previous app not provably restored; external recovery required" >&2
  return 40
}
