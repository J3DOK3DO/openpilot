# Accord 11G Release A: installation and rollback procedure (not executed in this campaign)

Status: **procedure only.** Nothing below was run on the comma. Read `TRACKAB_FINAL_VERDICTS_20261101.md` first:
install only if the owner accepts the verdicts recorded there.

## What changes on the car

- Source: installed Dom `5b0f81ca` + Track A (`accord_mvl_stock.py`: a partially queued synthetic LKAS press is
  cancelled on brake, PCM off, `LKAS_READY` low, disengage, cancel or resume) + tests/docs/research code.
- Unchanged: every native source, committed binary and Panda firmware (`panda/` tree identical to `5b0f81ca`), the
  Panda safety word (80/81), stock ACC ownership, steering limits and tuning.
- Not active: all Track B code (`tools/trackb_research/`), which no runtime module imports.

## Preconditions (owner checks on the day)

1. Car off/parked, comma offroad, on a known network; SSH works with the trusted ED25519 key.
2. `cat /VERSION` is `19.8.1`; `git -C /data/openpilot rev-parse HEAD` is still `5b0f81ca…` (or `195b7000…` if the
   staged Dom update was applied by a reboot — see "Pending update" below).
3. `/data` has ≥ 2 GB free. Do not clean `/` (94 % used, read-only).
4. The private Params backup from 2026-11-01 exists and its SHA-256 still matches its `.sha256` file.

## Install paths

The comma's updater only follows branches on its `origin` (`StarPilotHQ/openpilot`), so the in-app branch switch
cannot reach `J3DOK3DO/openpilot`. Two paths exist:

- **A. comma installer (supported for forks):** on the device, uninstall/reinstall with the custom URL
  `installer.comma.ai/J3DOK3DO/accord11g-dom7-trackab-native-candidate-20261101`. This replaces
  `/data/openpilot` with a fresh clone; `/data/params` is kept. Afterwards the updater follows that branch.
- **B. manual (SSH, keeps the existing checkout):**

```bash
cd /data/openpilot && git fetch https://github.com/J3DOK3DO/openpilot.git accord11g-dom7-trackab-native-candidate-20261101
```

```bash
cd /data/openpilot && git checkout --detach FETCH_HEAD && git rev-parse HEAD
```

  Then reboot. The tracked `prebuilt` marker means no on-device build runs. Expected HEAD is the published SHA in
  the final verdicts.

StarPilot Fast Update is **not** an install path for this candidate: it requires a `prebuilt.json` receipt produced
by a verified native build of that exact tree. The branch deliberately keeps installed Dom's binaries and Panda
firmware (all 93 identical) and does not fabricate a receipt; see the packaging section of the final verdicts.

## Post-install checks (read-only)

1. Expected HEAD; `git status --porcelain` empty.
2. swaglog `pandad` line shows `signature 510ed0d6c7a8d322, expected 510ed0d6c7a8d322` (no reflash expected,
   because `panda/board/obj` is unchanged). Any reflash means the firmware differs: stop and roll back.
3. Onroad in a safe location: stock ACC engages/cancels as before; lateral engages; LKAS button behaviour unchanged.

## Rollback

- Path A install: reinstall Dom with `installer.comma.ai/StarPilotHQ/Dom`, or use path B below to check out
  `5b0f81ca` (the object stays on the device).
- Path B install:

```bash
cd /data/openpilot && git checkout Dom && git reset --hard 5b0f81caa120a6e48b41ba7b271b9afa61733205
```

  then reboot. Restore Params from the private backup only if a setting was changed (stop manager first; the
  backup is a tar of `/data/params/d`).

## Pending update on the device

As of 2026-11-01T08:30Z the comma has Dom `195b7000` downloaded and finalized (`UpdateAvailable=1`). A normal reboot
will most likely switch the car to `195b7000`, which still lacks Track A. `5b0f81ca..195b7000` touches no file in the
candidate delta and nothing Honda-specific; the candidate's patch series applies to it without conflict.
