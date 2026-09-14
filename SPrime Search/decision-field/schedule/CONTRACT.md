# Schedule Field Pass 07 — execution contract

Date: 2026-09-14. This is a bounded successor to Pass 06. It does not change D2, ANF coordinates, the T4 payload contract, or the Human Expression Archive.

## Question
Pass 06 showed that each fixed context can be locally stable while a changing context schedule creates a cycle. Pass 07 asks how much temporal structure must be represented to analyze arbitrary finite schedule words, periodic schedules, adversarial switching, and finite-memory history-dependent schedulers.

## Exact objects
- Plant: one canonical T4 rank, four plant states, four context symbols.
- Local context map: a total function `{0,1,2,3}->{0,1,2,3}`, encoded by one byte.
- Finite schedule word: a tuple over contexts 0..3, applied left-to-right.
- Schedule transformation: the composed four-state map induced by a word.
- Open-loop schedule semigroup: closure of the four generators under composition. Because the full transformation monoid on four states contains only `4^4=256` maps, closure terminates and exactly represents every finite schedule word by its induced transformation.
- Periodic schedule: repeat one nonempty finite block forever; its block map determines dynamics at block boundaries.
- Adversarial switching: at each step an adversary chooses any allowed context; safety/reachability sets are exact greatest/least fixed points on the four plant states.
- History-dependent scheduler: a Moore machine whose memory emits a context and updates after observing the new plant state. Scheduler minimization preserves emitted-context behavior for every possible observation history; it does not claim plant-specific optimality.

## Hard checks
1. Exhaust all 256 four-state maps for composition identity and associativity with an independent native oracle.
2. Exhaust finite schedule words through length six on multiple plants and compare direct state-by-state execution with semigroup representatives. The finite semigroup closure then covers all longer finite words for final-map obligations.
3. Reproduce the Pass 06 counterexample `T4AAAAgF`: contexts 0 and 1 each have unique fixed-point attractors but block `(0,1)` has a two-cycle.
4. Verify periodic words against direct repeated execution and block-map powers.
5. Verify adversarial/controllable safety and reachability against independent finite-domain oracles.
6. Verify Moore minimization against exact pair-product distinguishability, including all two-state schedulers plus larger deterministic samples.
7. Negative controls reject malformed ranks, states, contexts, empty periodic blocks, malformed schedulers, and ambiguous string/byte schedule inputs.

## Interpretation limits
A finite schedule word and another word with the same induced map are equivalent only for the declared plant state transition at the end of the word. They can differ in intermediate states, emitted contexts, costs, observations, or external consequences. Semigroup equivalence must not be promoted to general semantic equivalence.

Periodic block analysis concerns block-boundary dynamics; intra-block unsafe states require stepwise analysis. Memory minimization concerns scheduler output behavior over all observation histories, not minimal memory for every control objective. Adversarial fixed points assume the allowed context set is correct and do not infer real-world authority to choose a context.

No universal switched-systems theorem, human-cognition claim, natural-language semantics, or proof of optimal control is asserted.
