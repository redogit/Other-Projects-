# Documentation-only source correction

`repair_pre_doc_fix.py` preserves the exact source used by `run-001` and `macro-001`. Its first complexity comment omitted empty-clause overhead. The current `repair.py` corrects that comment; executable statements are unchanged. Earlier manifests and output bytes remain unchanged. The current-source runs are `run-002` and `macro-002`.

To reconstruct the earlier input tree for its manifest, copy the current project to a separate temporary directory and replace only `mutation/repair.py` with this snapshot. All other declared inputs remain identical. Validate the original manifest against that reconstructed root. Do not overwrite the active source merely to validate a historical run.
