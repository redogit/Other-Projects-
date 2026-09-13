# S1024 Compression Lab

**Home:** `redogit/Other-Projects- / S1024 Compression Lab`  
**Included transport:** `SP1024-1`  
**Runtime:** Python 3.10+, standard library only.

## Run

```sh
python "S1024 Compression Lab/demo.py"
python -m unittest discover -s "S1024 Compression Lab/tests" -v
python "S1024 Compression Lab/sections1024.py" pack INPUT.txt FRAME.json
python "S1024 Compression Lab/sections1024.py" unpack FRAME.json RESTORED.txt
python "S1024 Compression Lab/sections1024.py" profile INPUT.txt AREAS.json
```

`pack --raw` admits arbitrary bytes; the default requires a complete UTF-8 stream. Both retain exact 1,024-byte cuts and a possibly shorter final section. A character crossing a cut remains valid through explicit entering/exiting parser states. Do not perform arithmetic on encoded float carriers.

A full raw section takes 133 selected finite binary64 values, or 1,064 binary payload bytes before framing. **This is transport expansion, not arbitrary-data compression.** The JSON hex representation has additional overhead. SHA-256 checks integrity, not authenticity or historical truth.

`UTF8Space` separately ranks/unranks complete strict UTF-8 strings through 1,024 bytes with exact integer counts. The exact-length 1,024-byte rank needs 7,348 bits. That syntax result neither makes every section independently complete nor verifies the meaning of text.

`solve` classifies protected/required bit constraints through width 8,192 and returns the unique minimum-Hamming repair when consistent. It does not enforce arbitrary language, program, cultural, causal or cross-bit semantic constraints. `literal_offsets` preserves matching state across section cuts.

## Frozen-period example

The learner selects a periodic-byte pattern from one training section, freezes it, and tests separate synthetic sections. The related one-exception section uses a 16-byte standalone model/exception record. A seeded distribution-shift control falls back to a 1,025-byte raw record. Pattern and exception costs are included; the shared decoder, outer frame, integrity and engineering costs remain additional.

No archive records are used for training. This is a narrow demonstration of recoverable structure and a failure boundary, not a language model, a new learning theorem, or a claim to beat general compressors.

## Do not merge the branches

The separately reported `S1024V1` UTF-8-boundary-conditioned ranked frame (117 carriers / 936 payload bytes in its declared complete-section example) is **not this format** and is not ported or rerun here. Its 1,030-byte standalone framed figure must not be substituted for SP1024-1. The other template-learning experiment is likewise not the included periodic model.

`sections1024.py` and `learning_probe.py` preserve the inherited SP1024-1 branch's code bytes. New demos/tests are publication additions. See [research](RESEARCH.md) and the repository's publication evidence for scopes and provenance.
