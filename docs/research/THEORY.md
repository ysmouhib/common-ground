# Theory: what Common Ground v2 reconstructs, and what it does not claim

> **Draft, 13 November 2026. Phase R, session 1 of 4.** Written so far: the
> definitions, the facts that follow from them, and hypotheses H2 to H4. Not written:
> H1 and H5 to H9, and the limits that rest on the psychology literature (Converse,
> motivated reasoning, value bias in language models). Their sources are not verified
> yet and this file cites nothing unverified. The definitions amend brief §4 in seven
> places ([`RESEARCH.md`](RESEARCH.md) §5). On 13 November 2026 the owner said to proceed
> on those amendments, so they are adopted for drafting and still subject to review. Not
> reviewed by the owner. A review on the strong
> model is required before Phase 3 (CLAUDE.md).

## 1. The claim

From the reviewed statements of a camp, Common Ground reports sets of formulas that
are **verified sufficient** to generate the camp's claims, ranks them by a declared
cost, and shows where two camps' sets agree and clash. It certifies deductions, not
truth, and not belief. A reported axiom is a hypothesis that would explain the
statements, never a finding about what anyone thinks.

## 2. Definitions

**Record.** After review a camp has finite sets of first-order sentences: E (endorsed),
R_firm and R_soft (rejected). E⁺ = E ∪ {¬r : r ∈ R_firm}.

**Pool.** A finite set K ⊇ E⁺ of reviewed sentences. Members outside E⁺ are *unstated
candidates*, each with at least one verbatim quote.

**Sufficient condition.** A set S is sufficient for a sentence φ when S ⊨ φ (Lin 2001,
Definitions 2 and 3; for first-order formulas, Doherty et al. 2001). The claims do not
entail a set that is sufficient for them: sufficient is not necessary.

**Axiom system.** A ⊆ K is an axiom system for the record, relative to K, when

1. A has a model;
2. A ⊨ φ for every φ ∈ E⁺;
3. A ⊭ r for every r ∈ R_soft;
4. no proper subset of A satisfies 2.

**Weakest sufficient condition.** The sufficient condition entailed by every other
(Lin 2001). Relative to the pool it is the statement "at least one minimal sufficient
subset of K is accepted", that is, the family of all minimal sufficient subsets. Each
axiom system is one member of that family.

**Cost.** cost(A) = Σ (1 − p(a)) + λ·|A| over a ∈ A, where p(a) ∈ [0, 1] is an
estimated plausibility with p = 1 for reviewed stated claims, |A| is counted on a
normal form in which conjunctions are split, and λ > 0. Each axiom carries the charge
(1 − p(a)) + λ. A *selected* system is a cost-minimal axiom system; ties are reported.

**Firm and soft rejection.** A property of the camp's stance. Firm: the camp asserts
¬r, and the system must entail ¬r. Soft: the camp declines r, and the system must not
entail r.

**Verdicts.** A property of a check, independent of the stance.

| Statement | Established only by |
|---|---|
| A ⊨ φ | a proof accepted by the Lean kernel (a solver refutation alone reads SOLVER-CHECKED) |
| A ⊭ r | an explicit finite model of A in which r is false, re-evaluated without a solver |
| A is consistent | an explicit finite model of A |
| otherwise | nothing: **no verdict** |

An entailment that was not proved is not a non-entailment.

## 3. What follows from the definitions

**F1. Existence depends on the statements alone.** An axiom system exists if and only
if E⁺ is consistent and entails no soft rejection. When one exists, some subset of the
stated claims is one (the *stated system*). Unstated axioms are never required; they
are preferred only when they lower the cost.

**F2. The stated claims are the invariant.** Every axiom system entails E⁺. So a
conflict between two camps' stated claims is a conflict between any two of their
systems, and a statement entailed by both camps' stated claims is entailed by both
systems. Conflict or agreement found only between reconstructed axioms holds for the
selected systems and may change with the selection.

**F3. Cost-minimal systems have no idle axiom.** With λ > 0, removing an unused axiom
lowers the cost and preserves conditions 1 and 3, so condition 4 follows from
cost-minimality.

**F4. What λ means.** An unstated axiom with plausibility p that makes k stated claims
derivable is preferred to stating them when p > 1 − (k − 1)·λ. One axiom saved is
worth λ units of plausibility. Since no charge exceeds 1 + λ, an axiom that replaces
more than 1 + 1/λ claims is preferred whatever its plausibility.

**F5. Only the hull can be selected.** With u(A) = Σ (1 − p(a)), cost = u + λ·|A|. As λ
varies, the selected systems are those on the lower convex hull of the points
(|A|, u(A)), each on an interval of λ that can be computed exactly.

F1 to F5 are elementary and derived in RESEARCH.md §2 to §3. The pool-relative form of
the weakest sufficient condition is derived there too; none of these is quoted from a
source, and each is to be cross-checked by brute force in the Phase 3 tests.

## 4. Hypotheses

Numbering follows the source pack. H1 and H5 to H9 will be added when their sources
are verified.

**H2 (formal core).** The object reconstructed for a camp is a sufficient condition
for its reviewed claims, selected from a finite pool. The weakest sufficient condition
over the pool is what all candidate systems share; a selected system says more than
it. *Sources:* Lin (2001); Doherty et al. (2001). *Not claimed:* that a first-order
weakest sufficient condition exists beyond the pool; both sources expect it not to be
first-order expressible in general, and Doherty and Szałas (2024) confirm that
computing it must fail on some inputs.

**H3 (parsimony).** Preferring the cheapest sufficient set under an additive cost is an
established way to select an explanation (Hobbs et al. 1993; Eiter and Gottlob 1995).
Its principled reading is a negative log probability (Charniak and Shimony 1990, as
reported by Hobbs et al. 1993, §8.3), which is also a description length (Rissanen
1978; Grünwald 2004). It is a strategy and carries no evidence that the selected
system is the one the camp holds. *Test:* in the Phase 8 holdout, the selected system
derives withheld endorsed statements that the stated system built from the retained
statements does not, without deriving withheld rejected ones. *Not claimed:* any
standard value of λ; the authors of weighted abduction call their own numbers ad hoc.

**H4 (localization).** When two camps' systems are jointly inconsistent, the minimal
unsatisfiable subsets are the fault lines and the minimal correction subsets are the
smallest concessions; each family determines the other by hitting-set duality (Liffiton
and Sakallah 2008). Both are enumerated with MARCO (Liffiton et al. 2016). By F2, fault
lines among stated claims are invariant and fault lines among reconstructed axioms are
relative to the selection.

## 5. Limits established so far

1. **Sufficient, not necessary.** Many systems are sufficient. The statements
   establish E⁺ and nothing stronger.
2. **Relative to the pool and to syntax.** An axiom nobody proposed is not found.
   Size depends on how formulas are written; the normal form reduces this and does not
   remove it (Grünwald 2004, §1.4, on the length of a hypothesis).
3. **Induction, selected abductively.** Proposing a general warrant from instances is
   induction in the classification of Hobbs et al. (1993, §4.1). Their scheme assumes a
   shared rule base; a camp's texts supply none. The nearer formal precedent is
   induction with negative evidence (Muggleton and De Raedt 1994), in which soft
   rejections play the part of the negative evidence.
4. **The numbers have no established meaning.** Plausibility is an estimate by a
   language model, not a measured probability, and λ is a setting.
5. **No charge for saying too much.** A system that entails the claims and much else
   pays nothing for the excess. Soft rejections and the holdout test are the only
   checks on it.
6. **First-order limits.** Entailment is undecidable in general. Inside the
   Bernays–Schönfinkel class the engine decides; outside it, "no verdict" remains
   possible, and a true non-entailment may have no finite model to show.
7. **Faithfulness.** A formula can be provably entailed and still not say what the
   sentence meant (README).

## 6. Open problems

- The normal form on which size is counted, and whether literal count should replace
  axiom count.
- Linear charge against logarithmic charge, and whether the plausibility estimates
  behave like probabilities at all.
- Records for which no axiom system exists: partial systems on maximal consistent
  subsets, and a coverage measure.
- Whether soft rejections should hold jointly as well as separately.
- Whether an uncontested background theory, shared by all camps, should exist.
- Economy against explanatory coherence as the selection principle; only one side of
  that exchange has been read.

## References

Verified as described in RESEARCH.md §1. Section numbers refer to the copies read.

- Charniak, E., & Shimony, S. E. (1990). Probabilistic semantics for cost based
  abduction. *Proc. AAAI-90*. Content as reported by Hobbs et al. (1993).
- Doherty, P., Łukaszewicz, W., & Szałas, A. (2001). Computing strongest necessary and
  weakest sufficient conditions of first-order formulas. *Proc. IJCAI-01*.
- Doherty, P., & Szałas, A. (2024). Dual forgetting operators in the context of weakest
  sufficient and strongest necessary conditions. *Artificial Intelligence* 326, 104036.
- Eiter, T., & Gottlob, G. (1995). The complexity of logic-based abduction. *Journal of
  the ACM* 42(1), 3–42.
- Grünwald, P. (2004). A tutorial introduction to the minimum description length
  principle. arXiv:math/0406077.
- Hobbs, J. R., Stickel, M. E., Appelt, D. E., & Martin, P. (1993). Interpretation as
  abduction. *Artificial Intelligence* 63(1–2), 69–142.
- Liffiton, M. H., Previti, A., Malik, A., & Marques-Silva, J. (2016). Fast, flexible
  MUS enumeration. *Constraints* 21(2), 223–250.
- Liffiton, M. H., & Sakallah, K. A. (2008). Algorithms for computing minimal
  unsatisfiable subsets of constraints. *Journal of Automated Reasoning* 40(1), 1–33.
- Lin, F. (2001). On strongest necessary and weakest sufficient conditions. *Artificial
  Intelligence* 128(1–2), 143–159.
- Muggleton, S., & De Raedt, L. (1994). Inductive logic programming: Theory and
  methods. *Journal of Logic Programming* 19–20, 629–679.
- Rissanen, J. (1978). Modeling by shortest data description. *Automatica* 14(5),
  465–471.
