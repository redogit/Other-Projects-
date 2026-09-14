# Research grounding for Pass 09 fast BOM search

This note records external literature checked through SciSpace on 2026-09-14. The literature motivates search ordering and targeted questions; it does **not** certify this implementation or raise its claim ceiling.

## Learned search ordering

- Caelan Reed Garrett, Leslie Pack Kaelbling, Tomás Lozano-Pérez, **Learning to Rank for Synthesizing Planning Heuristics**, IJCAI 2016 / arXiv:1608.01302. The paper explicitly treats induced search ordering, rather than ordinary regression error, as the relevant learning target for planner performance. This supports our choice to learn ordering only.
- Tianyu Zhang, Amin Banitalebi-Dehkordi, Yong Zhang, **Deep Reinforcement Learning for Exact Combinatorial Optimization: Learning to Branch**, ICPR 2022, DOI `10.1109/ICPR56361.2022.9956256`. This is relevant evidence that learned branching can accelerate exact combinatorial search while the exact solver remains responsible for correctness.

## Targeted questions / active learning

- Celeste Barnaby, Ramya Ramalingam, Osbert Bastani, Isil Dillig, **Active Learning for Neurosymbolic Program Synthesis**, DOI `10.1145/3763102` (2025). The work uses targeted questions while retaining a formal synthesis/verification foundation. This is relevant to our separation between question ranking and exact obligation verification.

## How this affects the implementation

The literature check supports a conservative architecture:

1. learned models rank branches/questions;
2. exact symbolic or enumerative solvers decide validity and final answers;
3. held-out performance and exact-answer invariance gate promotion;
4. learned heuristics can always be disabled without changing the semantics of the solver.

We intentionally do **not** import RankSVM, deep RL, or neural components in Pass 09. The bounded deterministic integer ranker is easier to audit and is sufficient to test whether learned ordering helps this specific BOM field. A more complex learned model would require a new evidence decision, not merely a larger model.
