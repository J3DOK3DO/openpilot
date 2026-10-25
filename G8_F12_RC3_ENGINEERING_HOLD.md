# G8-F12 RC3 — Honda-only offline qualification snapshot

**NON-INSTALLABLE / NOT FOR VEHICLE USE.** This is an engineering-only source freeze, not a production release or installer URL.

Source parent RC2: ac670c9555c1f00d7c1e7f5424cfdd375d4a15ca

Fourteen AArch64 source-built ELF components and the 126,302,979-byte model retain their verified RC2 bytes. No new Honda driving-control logic has been added. The launcher immediately exits 78 before any initialization.

AGNOS system content is byte-reconciled except two background image assets and filesystem metadata/journal, but OEM verified boot/root trust is UNPROVEN. The old early abctl --set_success beneath the launcher guard is NOT fixed.

A trusted and independently attested boot-health service, physical A/B rollback proof, complete hardware startup, Honda CAN/Panda bench safety review, and human approval are mandatory before a separate deployable RC is prepared.
