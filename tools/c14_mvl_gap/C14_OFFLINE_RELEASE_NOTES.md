# C14 — Honda Accord 11G MVL Boston pinned-tune gap verification

**SOURCE-ONLY OFFLINE PRE-RELEASE — NOT AN INSTALLER; NO VEHICLE / ROAD AUTHORIZATION.**

This C14 branch follows the published C13 control source **without altering any driving-control implementation**. C14 contributes a read-only, standard-library Python source comparison, seven deterministic synthetic/identity tests and a prioritized porting-gap matrix based on the earlier C9 research.

The checker compared Dom C13 with **MVL's actual pinned opendbc commit**, not the later mutable opendbc checkout. Steering PID Kp **0.115**, Ki **0.052**, feed-forward **0.000035**, and actuator delay **0.30 s** matched exactly. This means those numerical parameters need no new import. It does not mean every controller/state machine acts identically.

**Not included:** new lane-centering gain, motor torque calibration, low-speed steering override, automated stock-ACC set-speed commands, Bosch alpha-long radar cutover, BSM/nudgeless lane change, Panda safety changes, custom HUD change, firmware, Qualcomm runtime artifact or installation package.

The full C9 replay work remains in its local branch and has **not** been silently merged into C14. Route-derived evidence has been deliberately excluded from public packaging.

C11 offline ARM64 product compilation and Honda tests remain prior evidence for the unchanged control source; **C14 has no fresh native product build or prebuilt release receipt**. Firmware, GPU, hardware CAN2/`controlsMismatch` and physical engagement qualification are still required before a separate operational release.

### Read-only checker

From repo root on a host that contains the pinned MVL opendbc Git object:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/c14_mvl_gap -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 tools/c14_mvl_gap/read_only_tuning.py --mvl /path/to/mvl/opendbc-repo
```

The checker reads only Git committed `interface.py` content and never imports or executes steering-control code. Without the MVL pinned object it fails rather than claiming parity. One test skips (rather than passes) when the reference pin is missing.

GitHub's automatic source ZIP/TAR includes the wider repository, which may contain historical binaries or a prebuilt marker. **Those are not qualified C14 installation artifacts.** Do not install C14 on the Comma or engage vehicle controls.
