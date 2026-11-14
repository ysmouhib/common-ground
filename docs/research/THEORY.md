# Theory: what Common Ground v2 reconstructs, and what it does not claim

> **Draft, 14 November 2026. Phase R, sessions 1 to 4 of 4.** This file cites nothing
> unverified. The definitions amend brief §4 in seven places ([`RESEARCH.md`](RESEARCH.md)
> §5); on 13 November 2026 the owner said to proceed on them, so they are adopted for
> drafting and remain subject to review. The terminology decision of `RESEARCH.md` §9 is
> recorded below as *proposed*. Not reviewed by the owner: CGR-5 is the owner's sign-off
> and gates all Phase 3 code.

## 1. The claim

From the reviewed statements of a camp, Common Ground reports sets of formulas that are
**verified sufficient** to generate the camp's claims, ranks them by a declared cost, and
shows where two camps' sets agree and clash. It certifies deductions, not truth, and not
belief. A reported axiom is a hypothesis that would explain the statements, never a finding
about what anyone thinks.

**Terminology (proposed, `RESEARCH.md` §9).** "Axiom", qualified by provenance: *stated*
(a reviewed claim quoted from the camp's texts) or *unstated* (a reviewed candidate with
at least one evidence quote). "Warrant" and "implicit premise" appear in documentation
only, to relate our objects to the literature.

## 2. Definitions

**Record.** After review a camp has finite sets of first-order sentences: E (endorsed),
R_firm and R_soft (rejected). E⁺ = E ∪ {¬r : r ∈ R_firm}.

**Pool.** A finite set K ⊇ E⁺ of reviewed sentences. Members outside E⁺ are *unstated
candidates*, each with at least one verbatim quote.

**Sufficient condition.** A set S is sufficient for a sentence φ when S ⊨ φ (Lin 2001,
Definitions 2–3; Doherty et al. 2001). Sufficient is not necessary.

**Axiom system.** A ⊆ K is an axiom system for the record, relative to K, when (1) A has
a model; (2) A ⊨ φ for every φ ∈ E⁺; (3) A ⊭ r for every r ∈ R_soft; (4) no proper subset
of A satisfies 2.

**Weakest sufficient condition.** Relative to the pool, the family of all minimal
sufficient subsets of K (Lin 2001).

**Cost.** cost(A) = Σ (1 − p(a)) + λ·|A| over a ∈ A, where p(a) ∈ [0,1] is an estimated
plausibility with p = 1 for stated claims, |A| is counted on a normal form that splits
conjunctions, and λ > 0. A *selected* system is a cost-minimal axiom system; ties are
reported.

**Verdicts** are properties of a check, independent of the camp's stance:

| Statement | Established only by |
|---|---|
| A ⊨ φ | a proof accepted by the Lean kernel (a solver refutation alone reads SOLVER-CHECKED) |
| A ⊭ r | an explicit finite model of A in which r is false, re-evaluated without a solver |
| A is consistent | an explicit finite model of A |
| otherwise | nothing: **no verdict** |

An entailment that was not proved is not a non-entailment.

## 3. What follows from the definitions

**F1. Existence depends on the statements alone.** An axiom system exists iff E⁺ is
consistent and entails no soft rejection; when one exists, a minimal sufficient subset of
E⁺ (the *stated system* A₀) is one. Unstated axioms are never required; they are preferred
only when they lower the cost (`RESEARCH.md` §2.4).

**F2. The stated claims are the invariant.** Every axiom system entails E⁺, so conflicts
and common ground among *stated* claims hold for every reconstruction; those found only
among reconstructed axioms are selection-relative (§2.4).

**F3. Cost-minimal systems have no idle axiom.** With λ > 0, removing an unused axiom
lowers the cost and preserves conditions 1 and 3, so condition 4 follows from
cost-minimality.

**F4. What λ means.** An unstated axiom of plausibility p replacing k stated claims is
preferred when p > 1 − (k−1)·λ: one axiom saved is worth λ units of plausibility. No
charge exceeds 1 + λ, so an axiom replacing more than 1 + 1/λ claims wins whatever its
plausibility.

**F5. Only the hull can be selected.** With u(A) = Σ (1 − p(a)), cost = u + λ·|A|; as λ
varies, the selected systems are exactly those on the lower convex hull of the points
(|A|, u(A)), each on a computable λ-interval (§3; amendment A5).

F1–F5 are elementary, derived in `RESEARCH.md` §2–§3, and are cross-checked by brute force
in the Phase 3 tests.

## 4. Hypotheses

**H1 (reconstruction precedent).** Unstated-premise reconstruction is established and
measured for single arguments, joined to a formal check; we extend the unit to a camp's
whole record and add selection, rejections, cross-camp conflict sets. *Not claimed:* that
per-argument accuracy carries over. *Sources:* Hitchcock (1985); Habernal et al. (2018);
Quan et al. (2026); Feng & Hunter (2026); David & Hunter (2025).

**H2 (formal core).** The object reconstructed is a sufficient condition for the reviewed
claims, selected from a finite pool; over the pool, the weakest sufficient condition is the
family of all minimal sufficient subsets. *Not claimed:* a first-order one exists beyond
the pool (Doherty & Szałas 2024). *Sources:* Lin (2001); Doherty et al. (2001).

**H3 (parsimony).** Cost-based selection is weighted abduction, with MDL as a converging
justification; a strategy, no evidence about the camp. *Test:* the Phase 8 holdout
(`RESEARCH.md` §14.2). *Sources:* Hobbs et al. (1993); Eiter & Gottlob (1995); Rissanen
(1978); Grünwald (2004).

**H4 (localization).** When two camps' systems are jointly inconsistent, the MUSes are the
fault lines and the MCSes the smallest concessions, dual by hitting sets, enumerated with
MARCO. *Sources:* Liffiton & Sakallah (2008); Liffiton et al. (2016).

**H5 (values as axioms — a hypothesis under test, not a premise).** Value divergence may
root cross-camp disagreement. *Test:* on the CO2 corpus, report how each camp's
load-bearing axioms divide between value-labelled and factual statements; labels stay out
of cost(A). *Sources:* Graham et al. (2009, abstract); Tetlock et al. (2000, abstract);
Schwartz (1992, record only).

**H6 (a regimentation of a justification).** A camp's texts can be given a deductive form
in which a few axioms are verified sufficient for its claims; the form is the analyst's:
constraint in a belief system is "much less logical in the classical sense than …
psychological—and less psychological than social" (Converse 1964), and the texts are
justifications constructed for conclusions (Kunda 1990). *Test:* the holdout proportion
(`RESEARCH.md` §14.2). *Not claimed:* that the system is the camp's reasoning or applies to
mass-opinion samples.

**H7 (LLMs need symbolic checks).** Proposal and decision are separated: belief bias is
documented for language models (Biesterbos et al. 2026, abstract), and entailment never
reaches the model in this design.

**H8 (the plausibility estimate is a model's judgment).** Model value judgments depend on
the model and the prompt (Abdulhai et al. 2024; Yuan et al. 2026); calibration exists for
factual answers (Tian et al. 2023), not for this judgment. The estimate is tied to quotes,
blind to camp identity, sampled as a range, attributed to a model, replaceable by a
reviewer, never called a probability (`RESEARCH.md` §15.3).

**H9 (evaluation honesty).** No benchmark grades axiom-system reconstruction against a
corpus; we build one — the CO2 golden corpus with human annotations, Wilson intervals and
exact McNemar tests, limitations published (`RESEARCH.md` §18–§19). *Sources:* Li et al.
(2025); Wachsmuth et al. (2017); Han et al. (2024).

## 5. Limits

1. **Sufficient, not necessary.** Many systems are sufficient; the statements establish E⁺ and nothing stronger.
2. **Relative to the pool and to syntax.** Size depends on the normal form, which reduces but does not remove the dependence.
3. **Induction, selected abductively.** Proposing a general unstated axiom from instances is induction (Hobbs et al. 1993, §4.1); soft rejections are its negative evidence (Muggleton & De Raedt 1994).
4. **The numbers have no established meaning.** Plausibility is a model's estimate, never a probability; λ is a setting.
5. **No charge for saying too much.** Soft rejections and the holdout test are the only checks on excess.
6. **First-order limits.** Inside the Bernays–Schönfinkel class the engine decides; outside it, "no verdict" remains possible.
7. **Faithfulness.** A provably entailed formula can still not say what the sentence meant.
8. **A regimentation, not a description** (H6).
9. **Load is not centrality** (Converse): load is deductive indispensability inside one selected system; centrality is which element yields under forced change (`RESEARCH.md` §14.1).

## 6. Open problems

- The normal form on which size is counted; whether literal count should replace axiom count.
- Linear charge against logarithmic charge; whether the plausibility estimates behave like
  probabilities at all.
- Records with no axiom system: coverage κ is defined (`RESEARCH.md` §14.3); how to present
  one system per maximal consistent subset is open.
- Whether soft rejections should hold jointly as well as separately.
- Whether an uncontested background theory, shared by all camps, should exist.
- Whether the load vector should break ties between systems of equal cost (`RESEARCH.md`
  §8.5).

## References

Verified as described in `RESEARCH.md` §1, §7, §12 and §17. Bracketed tags are the
`RESEARCH.md` tags of the copy read; section numbers there refer to the copies read.

- Abdulhai, M., Serapio-García, G., Crepy, C., Valter, D., Canny, J., & Jaques, N. (2024). Moral foundations of large language models. *Proc. EMNLP 2024*, 17737–17752. doi:10.18653/v1/2024.emnlp-main.982 [abstract]
- Biesterbos, N., Den Ouden, M., & De Rijke, J. (2026). RvH-40 at SemEval-2026 Task 11: Disentangling reasoning from belief through symbolic abstraction. *Proc. SemEval-2026*, 451–456. [abstract]
- Charniak, E., & Shimony, S. E. (1990). Probabilistic semantics for cost based abduction. *Proc. AAAI-90*. Content as reported by Hobbs et al. (1993). [not read]
- Converse, P. E. (1964). The nature of belief systems in mass publics. Republished in *Critical Review* 18(1–3), 1–74 (2006). doi:10.1080/08913810608443650 [read]
- David, V., & Hunter, A. (2025). A logic-based framework for decoding enthymemes in argument maps involving implicitness in premises and claims. *Proc. IJCAI-25*, 4445–4453. doi:10.24963/ijcai.2025/495 [read]
- Doherty, P., Łukaszewicz, W., & Szałas, A. (2001). Computing strongest necessary and weakest sufficient conditions of first-order formulas. *Proc. IJCAI-01*, 145–153. [bib]
- Doherty, P., & Szałas, A. (2024). Dual forgetting operators in the context of weakest sufficient and strongest necessary conditions. *Artificial Intelligence* 326, 104036. [bib]
- Eiter, T., & Gottlob, G. (1995). The complexity of logic-based abduction. *Journal of the ACM* 42(1), 3–42. [bib]
- Feng, X., & Hunter, A. (2026). Making implicit premises explicit in logical understanding of enthymemes. arXiv:2603.06114v3 [read]
- Graham, J., Haidt, J., & Nosek, B. A. (2009). Liberals and conservatives rely on different sets of moral foundations. *Journal of Personality and Social Psychology* 96(5), 1029–1046. doi:10.1037/a0015141 [abstract]
- Grünwald, P. (2004). A tutorial introduction to the minimum description length principle. arXiv:math/0406077. [bib]
- Habernal, I., Wachsmuth, H., Gurevych, I., & Stein, B. (2018). The argument reasoning comprehension task: Identification and reconstruction of implicit warrants. *Proc. NAACL-HLT 2018*, 1930–1940. doi:10.18653/v1/N18-1175 [abstract]
- Han, S., Schoelkopf, H., Zhao, Y., et al. (2024). FOLIO: Natural language reasoning with first-order logic. *Proc. EMNLP 2024*, 22017–22031. doi:10.18653/v1/2024.emnlp-main.1229 [bib]
- Hitchcock, D. (1985). Enthymematic arguments. *Informal Logic* 7(2–3), from p. 83. doi:10.22329/il.v7i2.2707 [read]
- Hobbs, J. R., Stickel, M. E., Appelt, D. E., & Martin, P. (1993). Interpretation as abduction. *Artificial Intelligence* 63(1–2), 69–142. [read]
- Kunda, Z. (1990). The case for motivated reasoning. *Psychological Bulletin* 108(3), 480–498. doi:10.1037/0033-2909.108.3.480 [abstract]
- Li, H., Schlegel, V., Sun, Y., Batista-Navarro, R., & Nenadic, G. (2025). Large language models in argument mining: A survey. arXiv:2506.16383 [read]
- Liffiton, M. H., & Sakallah, K. (2008). Algorithms for computing minimal unsatisfiable subsets of constraints. *Journal of Automated Reasoning* 40(1), 1–33. [bib]
- Liffiton, M. H., Previti, A., Malik, A., & Marques-Silva, J. (2016). Fast, flexible MUS enumeration. *Constraints* 21(2), 223–250. [bib]
- Lin, F. (2001). On strongest necessary and weakest sufficient conditions. *Artificial Intelligence* 128(1–2), 143–159. doi:10.1016/S0004-3702(01)00070-4 [read]
- Muggleton, S., & De Raedt, L. (1994). Inductive logic programming: Theory and methods. *Journal of Logic Programming* 19–20, 629–679. [bib]
- Quan, X., Gubelmann, R., & Freitas, A. (2026). Autoformalizing argumentative material inferences. arXiv:2609.16991v1 [read]
- Rissanen, J. (1978). Modeling by shortest data description. *Automatica* 14(5), 465–471. [bib]
- Schwartz, S. H. (1992). Universals in the content and structure of values: Theoretical advances and empirical tests in 20 countries. *Advances in Experimental Social Psychology* 25, 1–65. doi:10.1016/S0065-2601(08)60281-6 [bib]
- Tetlock, P. E., Kristel, O. V., Elson, S. B., Green, M. C., & Lerner, J. S. (2000). The psychology of the unthinkable: Taboo trade-offs, forbidden base rates, and heretical counterfactuals. *Journal of Personality and Social Psychology* 78(5), 853–870. doi:10.1037/0022-3514.78.5.853 [abstract]
- Tian, K., Mitchell, E., Zhou, A., Sharma, A., Rafailov, R., Yao, H., Finn, C., & Manning, C. (2023). Just ask for calibration: Strategies for eliciting calibrated confidence scores from language models fine-tuned with human feedback. *Proc. EMNLP 2023*, 5433–5442. [abstract]
- Wachsmuth, H., Potthast, M., Al-Khatib, K., et al. (2017). Building an argument search engine for the web. *Proc. 4th Workshop on Argument Mining (ArgMining @ ACL 2017)*, 49–59. doi:10.18653/v1/W17-5106 [abstract]
- Yuan, C., Ma, B., Zhang, Z., Prenkaj, B., Kreuter, F., & Kasneci, G. (2026). Moral lenses, political coordinates: Towards ideological positioning of morally conditioned LLMs. *Proc. EMNLP 2026*, 5950–5984. [abstract]
