# Human Expression Archive

**Home:** `redogit/Other-Projects- / Human Expression Archive`  
**Accession:** `HEA-2026-09-13-01`  
**Status:** bounded public source-and-data publication; historical reviews are inherited.

The archive preserves 91 records from 81 distinct source URLs: 52 short saying excerpts and 39 recording, performance, tradition, practice, narrative, visual-work, documented-falsehood and archive-gateway records. Nine gateways point to further collections; those holdings have not been imported. Thirteen qualified relations and ten explicit gaps accompany the records.

## Use

From the repository root:

```sh
python "Human Expression Archive/build.py"
python -m unittest discover -s "Human Expression Archive/tests" -v
```

Open `Human Expression Archive/public/index.html`. Search works without a server or network connection, including native-script queries. With JavaScript disabled, all records remain available to browser Find. Sensitive wording has labelled disclosure controls. Source wording, editorial English glosses, reported dates, uncertain origins, claim treatment and rights remain separate.

`build.py --out DIRECTORY` creates an alternative output. Different existing files are protected unless `--overwrite` is explicit.

## What is actually committed

The five original public data files are packed in four `data/accession-01.zip.xz.b64.01` through `.04` parts. Concatenated in order, these form a text-safe lossless distribution carrier, not an opaque executable: base64 -> XZ -> ZIP -> five allowlisted UTF-8 files. `data/manifest.json` fixes their exact lengths and SHA-256 digests. The builder validates bounded expansion, member names, lengths and hashes before writing ordinary JSON/JSONL. Nothing is downloaded or evaluated as code.

The reconstructed `records.jsonl` is exactly 156,714 bytes, with SHA-256:

```text
2094c0b82ad19f0d3615d351ea210aa90ed4cb7ec774d86569dd8a88b502f14b
```

The original data is not rewritten to fit this publication. The offline page is a newly generated view, not the predecessor report. For example, the known impossible February 29, 2013 fieldnote date remains unresolved rather than being silently corrected.

## Source and human boundaries

The source reviews were performed for the prior accession and were not repeated here. Public availability is not community endorsement or blanket redistribution/training permission. All source-specific flags remain in the reconstructed records. No full song lyrics, recording, restricted media, private Library document or personal research-history dump is included.

The historical archive may contain falsehoods and harmful expressions as documented evidence; they do not become advice or executable instructions. No culture receives a global good/bad score. A translated saying is not a community-certified translation or proof of common historical origin.

See [rights](RIGHTS.md), the reconstructed `public/data/remainder.json`, and the [separate compression lab](../S1024%20Compression%20Lab/README.md). Byte checks and structural HTML checks are not an accessibility certification or independent cultural review.
