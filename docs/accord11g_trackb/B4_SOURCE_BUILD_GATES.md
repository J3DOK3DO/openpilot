# B4 source/build gates — not a device qualification

## Immutable source and image pins

The source pin is `b088da2780e3a168193bfc1ce62e5df811a69867`, branch `accord11g-dom7-trackb-b1-b4-discovery-20261030`, with parent `5fa8b2ed8c4b397e1235a3acae0bb4030b35a804`. The current source AGNOS manifest blob is `b3a23b4c28269fef31ae94f5560c876ce8c1acba` at `openpilot/common/hardware/comma/agnos.json`. Its `system` entry pins the **decompressed sparse stream** hash `9c753bdd90e6079b2cf525659d7523d0ebc0a375bd61e61cca628f1db3832cfd`; the separately supplied compressed XZ artifact SHA-256 is `83b15de…` (not a manifest verification result); sparse expansion/raw hash is `98e15de07c39a19b5fa17c96a67e66d4362f9ebaf7827b640f4127e3b6417da8`; and on-device hash is `9625ec32df735b26ea6b0b62834addc8b522108d5f5c4a2aebcb98fc2b94f4e9`.

These are source/artifact pins, not target evidence. No comma device is accessible; target architecture/slot, installed AGNOS version, measured partition hash, Panda RELEASE firmware hash, device build provenance, and target device comparison are unavailable and unclaimed. A freshly built ARM64 container image and independently running sysroot extraction are likewise not device evidence, so B4 remains UNVERIFIED.

## Static gates before any later separately authorized work

| Gate | Required record | Present state |
| --- | --- | --- |
| Source identity | Exact commit, clean-tree record, reviewed diff, source manifest/blob pins | Source pin stated; live device comparison absent. |
| Source isolation | New modules are unimported by live runtime; no protected driving, firmware, manager, pandad, Params, vehicle runtime, or AGNOS modification | Required diff inspection and static import/reference scan. |
| Native host tests | Current `./dev pytest` for new synthetic/release tests and prior 11G stock-ownership/release tests | Must be run and recorded independently; do not infer from this document. |
| Lint | `./dev ruff check` for the new Python files | Must be run and recorded independently. |
| Image provenance | Exact AGNOS partitions plus target architecture/slot and measured installed values bind to the source record | Absent; current manifest is no target proof. |
| Panda RELEASE | Exact target firmware binary hash, build provenance, and independently reviewed physical compatibility evidence | Absent; B3 has no actual Panda RELEASE authorization. |
| B1/B2 | Authoritative OEM/protocol evidence and a separately approved non-actuating contract/controller scope | B1 STOP; no B2 controller. |

Suggested static gate commands (not run claims):

```sh
git diff --name-only b088da2780e3a168193bfc1ce62e5df811a69867 -- \
  opendbc_repo/opendbc/car opendbc_repo/opendbc/safety/modes openpilot/selfdrive openpilot/system
rg -n 'shadow_synthetic|trackb_research' openpilot opendbc_repo --glob '!**/tests/**'
git status --short
```

Do not treat a clean host build, a manifest text hash, or a host RELEASE negative test as authorization to flash firmware, touch a device, transmit CAN, replace factory ACC, or qualify B4. B4 remains source/build-gated only.
