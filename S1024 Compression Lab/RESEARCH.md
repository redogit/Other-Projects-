# Learning and compression: bounded research map

This document carries forward the earlier research framing. External literature was reviewed for the inherited report; it was not re-fetched for this repository-publication pass. No novelty is claimed for the established methods.

| Area | Useful question | Required boundary |
|---|---|---|
| Lossless coding | Can every source byte be reconstructed at lower total cost? | Include model, dictionary, metadata and any needed context. |
| Minimum description length | Does a model plus residual pay for itself against a declared baseline? | A coding gain is model-relative, not proof of truth. |
| Predictive compression | Does a model fitted before evaluation encode later data efficiently? | Freeze before holdout; retain drift failures and simpler comparators. |
| Task-relative representation | Which distinctions are sufficient for a protected target? | Declare target, allowed loss and omitted information. |
| Behavioral abstraction | Which states remain equivalent under every allowed continuation? | Current example agreement is insufficient; keep counterexamples and a reopening route. |
| Layer-local learning | Can local learned modules be trained above exact block summaries? | Proposed connection only here; locality does not establish objective alignment. |

A proposed compression-area record binds a byte/state range, model/decoder version, context dependencies, protected questions, allowed continuations, full measured costs, witnesses, counterexamples, source lineage, freshness and unresolved remainder. The current profiler measures byte-compressibility only; it does not infer semantic equivalence or cultural meaning.

Knowledge Decay remains a version/freshness issue: earlier regularities can fail on later data. Preserve richer source material when future obligations may need distinctions not present in an active summary. Learning a reusable pattern, preserving information and outperforming a comparator are separate claims. Human learning needs separate consented evidence of understanding or transfer.

A de Bruijn traversal or codebook address is not automatically a storage saving. An address requires its codebook; a short hash is not the original source. Expressions, translations, context and rights cannot be discarded just because two records compress to the same number of bytes.

## Inherited primary literature references

- P. Grunwald, *A tutorial introduction to the minimum description length principle*: https://arxiv.org/abs/math/0406077
- N. Tishby, F. Pereira and W. Bialek, *The information bottleneck method*: https://arxiv.org/abs/physics/0004057
- G. Deletang et al., *Language Modeling Is Compression*: https://arxiv.org/abs/2309.10668
- X. Wang, I. Dillig and R. Singh, *Program Synthesis using Abstraction Refinement*: https://arxiv.org/abs/1710.07740

The included code demonstrates neither a universal S-prime idea detector nor human cognitive idea formation. The active experiment is a deliberately constructed periodic-byte example; the alternative UTF-8-ranked framing and template-learning branch remains separate inherited work.
