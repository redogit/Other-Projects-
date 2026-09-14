Pass 06 evidence is derived from the deterministic `audit.py` and `stress_audit.py` computations, but not every committed file is a byte-for-byte raw generator dump.

- `SUMMARY.json` is the semantic bounded-result record and must equal a fresh `audit.py` result after JSON parsing.
- `FRONTIER.json` is the selected carrier-boundary view of the full 24-cell generated frontier. It retains the eight cells `(3,4)`, `(4,1..4)`, `(5,1..2)`, and `(6,1)` because they bracket the 32/48/64-bit carrier transitions discussed in the report.
- `VERIFICATION.json` retains the fresh source hashes plus separately recorded second-pass reproduction and repair-cube checks. The second-pass block is additive audit metadata and is not emitted by the first-pass generator.
- `HARD_STRESS.json` and `HARDENING_VERIFICATION.json` are direct deterministic stress/hardening outputs and must remain byte-stable under rerun.

CI checks those relationships explicitly instead of assuming that curated evidence files must be identical to temporary full generator outputs. These records support only the declared finite implementation claims; they are not formal proof, semantic validation, or independent replication.
