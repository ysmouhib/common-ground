# Research notes for Common Ground v2 (Phase R)

**Status, 14 November 2026.** Sessions 1 and 2 of 4 are complete: RQ1 and RQ3 (formal
core, sections 2–3) and RQ2 with the terminology decision and the novelty search
(reconstruction precedent, sections 7–10) have draft answers. RQ4, RQ5 and RQ6 are not
started. Nothing below has been reviewed by the owner. The input to this file is the source pack, [`sources.md`](sources.md);
section 4 lists where this file contradicts it and why.

## 0. Verification tags

| Tag | Meaning |
|---|---|
| `[read]` | Full text read in this session. The entry names the copy and the sections. |
| `[abstract]` | Bibliographic data checked against Crossref or the publisher; abstract or opening pages read. |
| `[bib]` | Bibliographic data checked; content not read. Anything said about the content is attributed to a source that was read. |
| `[unverified]` | Not checked. Excluded from `THEORY.md`. |

Checks used the Crossref REST API and publisher, proceedings or author pages on 13 and
14 November 2026.
For the three core papers the copy read is the authors' preprint, so passages are
located by section, never by journal page.

## 1. Sources verified in Session 1

### 1.1 The three core papers

**Lin, F. (2001). On strongest necessary and weakest sufficient conditions.
*Artificial Intelligence* 128(1–2), 143–159. doi:10.1016/S0004-3702(01)00070-4.**
`[read]` All 17 pages of the author's preprint of the journal version
(`http://www.cs.ust.hk/faculty/flin/papers/snc-aij.ps`).

*What it says.* The setting is propositional. Fix a theory T, a proposition q and a
set P of propositions, the vocabulary an answer may use. A formula φ of P is a
*sufficient condition* of q on P under T if T ⊨ φ ⊃ q, and a *weakest sufficient
condition* (WSC) if every sufficient condition ψ satisfies T ⊨ ψ ⊃ φ (Definition 2).
The *strongest necessary condition* (SNC) is the dual (Definition 1, Proposition 5).
Both always exist and are unique up to equivalence under T (§1, Proposition 1). They
extend from propositions to formulas (Definition 3, Proposition 3). The WSC of a
conjunction is the conjunction of the WSCs (Proposition 7); the SNC of a disjunction
is the disjunction of the SNCs (Proposition 6). The WSC can be computed by forgetting
the propositions outside P (Theorem 2), at a cost exponential in their number, or read
off the prime implicates (Proposition 8), which makes it the disjunction of the
negations of the minimal support clauses of Reiter and de Kleer's ATMS (§5). In §6 Lin
separates his notion from the abduction literature: he wants formulas that "capture
all possible explanations", where abduction and diagnosis are "mainly concerned with
computing parsimonious and minimal explanations". In §7 he calls the first-order case
"a difficult task" and expects that these conditions "cannot in general be expressible
in first-order logic".

*Implication for the design.* Lin gives the vocabulary (sufficient, weakest sufficient,
"on P under T") and one exact tool. He does not give the axiom system. An axiom system
is one sufficient condition among many, chosen by cost; the WSC is what all of them
have in common. See RQ1.

**Hobbs, J. R., Stickel, M. E., Appelt, D. E., & Martin, P. (1993). Interpretation as
abduction. *Artificial Intelligence* 63(1–2), 69–142. doi:10.1016/0004-3702(93)90015-4.**
`[read]` §1, §4, §7 (all but about a page in the middle of §7.3), §8.3 and §9 of the
authors' preprint (`interp-abduct-ai.ps`, linked from Hobbs's publications page at
isi.edu). Not read: §2–3, §5–6 and §8.1–8.2, which apply the scheme to reference
resolution, syntax and efficiency. The pack marks this paper "must read in full"; the
unread sections do not bear on the cost function, but that is a judgement made from
their headings.

*What it says.* To interpret a text is to find the cheapest proof of its logical form
from a knowledge base both parties share, where a literal that cannot be proved may be
assumed at a cost (§1). The scheme (§4.1) has three parts: an assumability cost on each
goal literal; weights on rule antecedents (in P1^w1 ∧ P2^w2 ⊃ Q, assuming Pi costs
wi·c when assuming Q costs c); and *factoring*, which unifies two goals and charges the
smaller cost once. Weights that sum to less than 1 favour "most-specific" abduction,
more than 1 "least-specific"; factoring lets a shared assumption pay for itself. The
criteria behind it are consistency, and Thagard's simplicity and consilience ("more
bang for the buck"). The authors name the trade-off: specific assumptions are more
informative, unspecific ones more likely to be correct. The scheme is credited to
Stickel (footnote 9). §4.1 also draws the line that matters to us: concluding
(∀x) p(x) ⊃ q(x) from instances is *induction*; abduction concludes p(A) from that rule
and q(A).

On the numbers the paper is candid. How to assign them "is a matter of continuing
research" (§4.1). The numeric component "is highly ad hoc" (§8.3). Which
interpretation wins is sensitive to whether weights sum above or below one, and
otherwise "fairly impervious to small changes" (§4.1). Charniak and Shimony (1990)
gave a probabilistic semantics for a restricted propositional case: costs are negative
logarithms of prior probabilities, and the minimum-cost assignment is the most
probable one in a Bayesian network (§8.3). Hobbs et al. add that their own costs also
encode the *disutility* of leaving something unexplained, not only improbability. The
scheme does not measure how decisively the winner beats its rivals, "a clear
shortcoming" (§8.3). In practice weights are set by intuition and refined "by
successive approximation on a representative sample of the corpus" (§8.3). Counting
assumptions "is not, by itself, adequate" (§7.3); Ng and Mooney's (1990) coherence
criterion is discussed there and disputed. §7.1 quotes Peirce: a hypothesis is accepted
only "as an interrogation", and choosing among hypotheses is "a question of economy".

*Implication for the design.* The form of cost(A), an additive charge per assumption
with the cheapest sufficient set preferred, has this paper as precedent. The values do
not. Two differences limit the analogy: Hobbs et al. assume a fixed shared rule base
and abduce facts, while we hypothesize the rules themselves; and their costs flow
through rule weights, while ours are fixed per axiom. See RQ3.

**Liffiton, M. H., & Sakallah, K. A. (2008). Algorithms for computing minimal
unsatisfiable subsets of constraints. *Journal of Automated Reasoning* 40(1), 1–33.
doi:10.1007/s10817-007-9084-z.** Published online in 2007; the issue is January 2008.
`[read]` §1–6, the opening of §7.1, §7.2, §9 and §10 of the authors' preprint
(`jar_liffiton_CAMUS.pdf`, author's page at iwu.edu). Not read: the rest of §7.1 and
§8 (experiments).

*What it says.* For an unsatisfiable set of constraints it defines the minimal
unsatisfiable subsets (MUS), the minimal correction subsets (MCS) and the maximal
satisfiable subsets (MSS, the complements of the MCSes) (Definitions 2–4). Theorem 1:
the MUSes are exactly the irreducible hitting sets of the MCSes, and conversely. The
paper credits this duality to Bailey and Stuckey (2005), Birnbaum and Lozinskii (2003)
and Liffiton et al. (2005), and takes the proof from Birnbaum and Lozinskii. Its
algorithm, **CAMUS**, has two phases: enumerate every MCS with an incremental SAT
solver, one selector variable per clause and a cardinality bound, smallest first; then
compute the MUSes as hitting sets. Both collections can be exponential, phase 1 must
finish before any MUS is output, and a partial MCS collection is useless for MUSes:
"Hitting sets of any proper subset of the collection of MCSes may not be
unsatisfiable" (§7.1). §7.2 gives one selector to a whole high-level statement, so the
MUSes are sets of statements. The authors say the ideas apply to any constraint
system. One MUS does not explain an infeasibility; it is "a single hole" in a sieve (§1).

*Implication for the design.* This is the right citation for the definitions and for
the hitting-set duality that `argmap.py`'s tests check. It is not the citation for the
algorithm `argmap.py` runs (see the next entry). §7.2 is the precedent for treating a
first-order statement as one unit of conflict.

### 1.2 Supporting sources

**Liffiton, M. H., Previti, A., Malik, A., & Marques-Silva, J. (2016). Fast, flexible
MUS enumeration. *Constraints* 21(2), 223–250. doi:10.1007/s10601-015-9183-0.** Online
22 March 2015. `[abstract]` plus the author's project page, which names the algorithm
MARCO and says it outputs MUSes earlier and more steadily than CAMUS. The abstract
states that it unifies Liffiton and Malik (2013) and Previti and Marques-Silva (2013).
*Implication:* this is the citation for the enumeration in `argmap.py`.

**Liffiton, M. H., & Malik, A. (2013). Enumerating infeasibility: Finding multiple
MUSes quickly. CPAIOR 2013, LNCS, 160–175. doi:10.1007/978-3-642-38171-3_11.** `[bib]`
**Previti, A., & Marques-Silva, J. (2013). Partial MUS enumeration. *Proc. AAAI* 27(1),
818–825. doi:10.1609/aaai.v27i1.8657.** `[bib]` The two independent origins of MARCO,
per the abstract above.

**Liffiton, M. H., Mneimneh, M. N., Lynce, I., Andraus, Z. S., Marques-Silva, J., &
Sakallah, K. A. (2009). A branch and bound algorithm for extracting smallest minimal
unsatisfiable subformulas. *Constraints* 14(4), 415–442. doi:10.1007/s10601-008-9058-8.**
`[bib]` Title only. *Implication:* a pointer for the Phase 3 design document; a
cost-minimal sufficient subset is a weighted version of a smallest MUS.

**Bailey, J., & Stuckey, P. J. (2005). Discovery of minimal unsatisfiable subsets of
constraints using hitting set dualization. PADL 2005, LNCS 3350, 174–186.
doi:10.1007/978-3-540-30557-6_14.** `[bib]`
**Birnbaum, E., & Lozinskii, E. L. (2003). Consistent subsets of inconsistent systems:
structure and behaviour. *J. Experimental & Theoretical Artificial Intelligence* 15(1),
25–46. doi:10.1080/0952813021000026795.** `[bib]` Origins of the duality, as credited by
Liffiton and Sakallah (§3).

**Doherty, P., Łukaszewicz, W., & Szałas, A. (2001). Computing strongest necessary and
weakest sufficient conditions of first-order formulas. *Proc. IJCAI-01*, Seattle,
145–153.** Pages from the proceedings index at ijcai.org (Session 2).
`[read]` Abstract and §1 of the copy on the authors' institutional site; the rest
skimmed. It restates Lin's definitions for first-order formulas, relative to a set P of
relation symbols (Definitions 1.1, 1.2), and computes the conditions by second-order
quantifier elimination. It agrees with Lin that they are "not always expressible in
first-order logic" and says the method may return a first-order formula, a fixpoint
formula, or fail. It presents the WSC as the basis of an explanation that is "minimal
in the sense of not being overly specific". *Implication:* the first-order definition
we can cite, with no existence guarantee.

**Doherty, P., & Szałas, A. (2024). Dual forgetting operators in the context of weakest
sufficient and strongest necessary conditions. *Artificial Intelligence* 326, 104036.
doi:10.1016/j.artint.2023.104036.** `[read]` Abstract, §1 and passages of §6–7 of the
arXiv preprint (2305.07233v1). The current treatment by the same group. It ties the WSC
to a "weak forgetting" operator and repeats that deciding whether the second-order
formula has a first-order equivalent "is highly undecidable", so elimination
algorithms "have to fail for some input formulas". *Implication:* supersedes nothing
in Lin; confirms that a general first-order WSC is not something to promise.

**Stickel, M. E. (1991). A Prolog-like inference system for computing minimum-cost
abductive explanations in natural-language interpretation. *Annals of Mathematics and
Artificial Intelligence* 4(1–2), 89–105. doi:10.1007/BF01531174.** `[bib]` Hobbs et al.
(footnote 9) credit the scheme to Stickel and cite an earlier chapter, also checked:
Stickel (1990), in *Natural Language and Logic*, LNAI 459, 233–252,
doi:10.1007/3-540-53082-7_26.

**Charniak, E., & Shimony, S. E. (1990). Probabilistic semantics for cost based
abduction. *Proc. AAAI-90*, 106–111.** `[bib]` Pages from a secondary index; Hobbs et
al. cite the Brown technical report CS-90-02. Content as summarized by Hobbs et al.
(§8.3). The journal follow-up, **Charniak & Shimony (1994), Cost-based abduction and
MAP explanation, *Artificial Intelligence* 66(2), 345–374, doi:10.1016/0004-3702(94)90030-2**,
is `[bib]`. *Implication:* the only principled reading of an assumption cost found so
far is a negative log probability.

**Eiter, T., & Gottlob, G. (1995). The complexity of logic-based abduction. *Journal of
the ACM* 42(1), 3–42. doi:10.1145/200836.200838.** `[abstract]` Lists the usual
preference criteria for abductive explanations as "subset-minimality, minimal
cardinality, minimal weight, or minimality under prioritization", and places the basic
decision problems for propositional abduction at the second level of the polynomial
hierarchy. *Implication:* minimal weight is one accepted criterion among four, and
the search is hard even without quantifiers.

**Muggleton, S., & De Raedt, L. (1994). Inductive logic programming: Theory and methods.
*Journal of Logic Programming* 19–20, 629–679. doi:10.1016/0743-1066(94)90035-3.**
`[read]` Abstract, §2.1 and Definitions 3.1–3.2 of the first author's copy. For
background B, hypothesis H, positive evidence E⁺ and negative evidence E⁻, the "normal
semantics" requires B ∧ H ⊨ E⁺ (posterior sufficiency) and B ∧ H ∧ E⁻ ⊭ □ (posterior
satisfiability, "consistency with the negative evidence"), with a syntactic bias on
hypotheses that is "omni-present". *Implication:* our definition has the shape of an
induction problem with negative evidence; soft rejections are the negative evidence.

**Grünwald, P. (2004). A tutorial introduction to the minimum description length
principle. arXiv:math/0406077.** `[read]` §1.3, §1.4, §1.6 and the opening of §1.7.
Two-part MDL picks the hypothesis H minimizing L(H) + L(D|H). The length of the
hypothesis is the weak point: it "can be very large under one code, but quite short
under another", so the procedure "is in danger of becoming arbitrary". A code with
lengths −log P exists for every distribution P and conversely (§2.2). MDL is "a
strategy for inferring models from data", not a claim that simple models are more
likely true. It dates the principle from Rissanen (1978).
**Rissanen, J. (1978). Modeling by shortest data description. *Automatica* 14(5),
465–471. doi:10.1016/0005-1098(78)90005-5.** `[bib]`

**Thagard, P. R. (1978). The best explanation: Criteria for theory choice. *The Journal
of Philosophy* 75(2), 76–92. doi:10.2307/2025686.** `[bib]` Source of "simplicity" and
"consilience" as used by Hobbs et al. (§4.1).

**Ng, H. T., & Mooney, R. J. (1990). On the role of coherence in abductive explanation.
*Proc. AAAI-90*, 337–342.** `[read]` in Session 2 (abstract, §1, §2, opening of §3.1,
the coherence metric); see section 8.5. Hobbs et al. cite a different item by the same
authors and year, "The role of coherence in constructing and evaluating abductive
explanations", Working Notes, AAAI Spring Symposium on Automated Abduction, which is
`[bib]` from their reference list only.

**Reiter, R., & de Kleer, J. (1987). Foundations of assumption-based truth maintenance
systems: Preliminary report. *Proc. AAAI-87*, 183–188.** `[abstract]` in Session 2, from
AAAI's own copy. Cited by Lin (§5). **de Kleer, J. (1986). An assumption-based TMS. *Artificial
Intelligence* 28(2), 127–162. doi:10.1016/0004-3702(86)90080-9** is `[bib]`.

## 2. RQ1. What is an axiom system, and what does sufficiency mean?

**Short answer.** An axiom system for a camp is a *sufficient condition* for the camp's
reviewed claims, in Lin's sense, drawn from a finite pool of reviewed candidates, that
is consistent, respects the camp's rejections and has no idle member. It is one of
possibly many such sets. It is not the weakest sufficient condition, and nothing makes
it necessary: the claims do not entail it.

### 2.1 Objects

*Language.* The engine's first-order language (`fol.py`): one sort, no arithmetic.

*Record.* After human review a camp has a finite set E of endorsed sentences and two
finite sets of rejected sentences, R_firm and R_soft (brief §4). Write
E⁺ = E ∪ {¬r : r ∈ R_firm}. A firm rejection is an endorsement of a negation, so it
needs no separate machinery.

*Pool.* A finite set K ⊇ E⁺ of sentences approved in review. Its members outside E⁺
are the *unstated candidates* proposed by the model or by a person.

### 2.2 Definition

A set A ⊆ K is an **axiom system** for the record, relative to K, when

- (S1) *consistent*: A has a model;
- (S2) *sufficient*: A ⊨ φ for every φ ∈ E⁺;
- (S3) *restrained*: A ⊭ r for every r ∈ R_soft;
- (S4) *no idle axiom*: no proper subset of A satisfies (S2).

Three differences from brief §4, each proposed as an amendment in section 5:

1. (S4) replaces "no axiom in A is entailed by the others". The brief's condition lets
   an axiom stay that nothing uses: with E = {p}, the set {p, q} passes it. (S4) rules
   that out and implies the brief's condition. Subset-minimality is also the standard
   notion in both literatures we lean on (Eiter & Gottlob 1995, abstract; Liffiton &
   Sakallah 2008, Definition 2).
2. The pool K is in the definition. The engine can only search what was proposed and
   approved, so every "minimal" below means minimal among subsets of K.
3. Firm rejections are folded into E⁺.

### 2.3 Sufficiency, after Lin

(S2) is Lin's "sufficient condition" with an empty background theory and the whole
language as vocabulary (Lin 2001, Definitions 2–3; Doherty et al. 2001 for first-order
formulas). Lin's own example shows what the word does and does not carry. Under
{rain ⊃ grassWet, sprinklerOn ⊃ grassWet}, the sufficient conditions of grassWet
include rain, sprinklerOn, rain ∨ sprinklerOn, and grassWet itself, which Lin calls
trivial. Sufficient conditions are many; observing wet grass entails none of the
informative ones.

Four consequences for us.

**(a) The WSC is not the axiom system.** The WSC is the *least* committal sufficient
condition: rain ∨ sprinklerOn in the example, "the most general abduction" in Lin's
abstract. With no background theory and no restriction on vocabulary, the WSC of a
camp's claims is the conjunction of the claims. So the WSC never produces an unstated
axiom, and a system that states a general warrant is logically *stronger* than the WSC,
not an approximation of it. Lin says as much (§6): his formula captures all
explanations, while abduction selects parsimonious ones. Selection is by cost (RQ3),
which is a different order from logical weakness. The pack's sentence "as weak/general
as the cost function allows" uses "general" in two opposite senses: Lin's (true in more
situations, hence weaker) and ours (a universal law, hence stronger).

**(b) The WSC does have an exact place in the system.** Give each pool member k a fresh
proposition s_k meaning "k is accepted", and let T* = {s_k ⊃ k : k ∈ K}. For a target
φ, let W be the disjunction, over the minimal subsets S ⊆ K with S ⊨ φ, of the
conjunction of the s_k for k ∈ S. Then W is the weakest sufficient condition of φ on
the vocabulary {s_k} under T*. *Proof sketch.* W is sufficient because each disjunct
switches on a subset that entails φ. Let ψ be any sufficient condition over the s_k and
let M be a model of T* and ψ; let S be the set of k with s_k true in M. If S ⊭ φ, take
a structure in which S holds and φ fails, set the s_k as in M, and obtain a model of T*
and ψ in which φ fails, a contradiction. So S ⊨ φ, M satisfies a disjunct of W, and
T* ⊨ ψ ⊃ W. ∎ This is the pool-level form of Lin's remark that the WSC is the
disjunction of the negated minimal support clauses (§5). It holds for a first-order T*
because the vocabulary is a finite set of propositions. In plain terms: **the family of
all minimal premise sets that `argmap.py` enumerates is the weakest sufficient
condition, written out**, and each axiom system is one of its disjuncts. This is my
derivation, not a result stated in a source; it should be cross-checked by brute force
on small pools in the Phase 3 tests.

**(c) Lin's two notions map onto two product views.** The WSC of a claim, taken *under
a camp's certified system as background theory*, is the weakest thing the camp would
have to add for the claim to follow: the "what you would have to accept" view of brief
§6. The SNC is the dual: with A₁ and A₂ the two camps' systems, a statement in a shared
vocabulary is entailed by both exactly when it is a necessary condition of A₁ ∨ A₂, so
the provable common ground is, when it can be written as one formula, the strongest
necessary condition of A₁ ∨ A₂ (from Lin's Definition 3; not a claim Lin makes).

**(d) First-order caveat.** Lin's existence and computation results are propositional.
For first-order theories neither condition need be expressible in first-order logic
(Lin 2001 §7; Doherty et al. 2001 §1; Doherty & Szałas 2024). We therefore promise the
pool-relative construction of (b), which always exists, and nothing more general.

### 2.4 Facts that follow from the definition

**Existence.** An axiom system exists if and only if E⁺ is consistent and E⁺ ⊭ r for
every soft rejection r. If A is an axiom system then A ⊨ E⁺, so a model of A is a model
of E⁺, and E⁺ ⊨ r would give A ⊨ r. Conversely E⁺ itself meets (S1)–(S3), and a minimal
subset of E⁺ that still entails E⁺ meets (S4). So **whether any axiom system exists is a
property of the reviewed statements alone**, and when one exists, a subset of the stated
claims is always one. Call it the *stated system* A₀. Unstated axioms are never needed
for existence; they can only be preferred, by cost.

**Invariants.** Every axiom system entails E⁺. Hence, across all admissible systems of
two camps: if E⁺₁ ∪ E⁺₂ is inconsistent then A₁ ∪ A₂ is inconsistent, and anything
entailed by both E⁺₁ and E⁺₂ is entailed by both A₁ and A₂. Conflicts and common ground
found among *stated* claims hold for every reconstruction. Conflicts and common ground
that appear only between reconstructed axioms depend on which systems were selected.
Reconstruction can add agreement and add conflict; it cannot remove either.

**Load.** By monotonicity, "every minimal premise set for e inside A contains a" is
equivalent to A ∖ {a} ⊭ e. The load of brief §4 needs |A|·|E| entailment checks, not an
enumeration.

### 2.5 Firm and soft rejections, and what a verdict licenses

The pack mixes two things (its §I.6 and the note under D1): how strongly a camp
rejects a claim, and whether the engine established something. They are independent.

| Requirement | Established by | The interface may say |
|---|---|---|
| A ⊨ e, e endorsed | a proof accepted by the Lean kernel; a solver refutation alone is labelled SOLVER-CHECKED | "This claim follows from these axioms." |
| A ⊨ ¬r, r firmly rejected | the same, for ¬r | "The negation of this claim follows from these axioms." |
| A ⊭ r, r softly rejected | an explicit finite model of A in which r is false, re-checked by the solver-free evaluator | "This claim does not follow from these axioms. Here is a situation in which every axiom holds and the claim fails." |
| A consistent | an explicit finite model of A | "These axioms can all hold together." |
| none of these | nothing | "No verdict." |

"Soft" is a property of the camp's stance. "No verdict" is a property of the check.
An unproved entailment is never a non-entailment: the engine reports a failed or
timed-out Lean run as no verdict already (README), and outside the Bernays–Schönfinkel
class a true non-entailment may have no finite model to show. A soft rejection is
*satisfied* only by a countermodel.

One design choice hides in (S3). The brief asks for each soft rejection separately. The
induction literature asks for more: the hypothesis must be consistent with all the
negative evidence at once (Muggleton & De Raedt 1994, Definition 3.1), which here would
read "A together with the negations of all soft rejections has a model". The two
differ when A entails r₁ ∨ r₂ without entailing either. The separate version matches
"the camp does not assert r" and should stay the requirement; a failure of the joint
version should be reported, because it means the system commits the camp to at least
one of the things it declined.

### 2.6 What the definition does not give

- *Uniqueness.* Several systems usually qualify. What the reviewed statements
  establish is E⁺; everything beyond is selected.
- *Reach beyond the pool.* An axiom nobody proposed cannot be found.
- *Decidability.* First-order entailment is undecidable; inside the
  Bernays–Schönfinkel class the engine decides, outside it "no verdict" stays possible.
- *Faithfulness.* Sufficiency relates formulas. Whether a formula says what a sentence
  meant is a separate question with separate evidence (README).

## 3. RQ3. Why parsimony, and how is cost(A) justified?

**Short answer.** The literature supports choosing among sufficient explanations by an
additive cost over the assumptions made. It does not support particular numbers, and it
does not say the cheapest explanation is the true one. Two features of our problem lie
outside the classical scheme: we hypothesize rules and not only facts, and our cost has
no term for how tightly a system fits. cost(A) is defensible as a declared selection
strategy whose parameter has a stated meaning. It needs three repairs before Phase 3.

### 3.1 What the sources establish

1. *Selection is needed and is a matter of economy.* Sufficient explanations are many
   and the inference to any one is not valid (Hobbs et al. §4.1; Lin §1). Hobbs et al.
   name consistency, simplicity and consilience as criteria and quote Peirce on
   economy (§4.1, §7.1).
2. *An additive cost over assumptions is an established form.* Weighted abduction
   charges each assumed literal and prefers the cheapest proof (Stickel's scheme; Hobbs
   et al. §4.1). "Minimal weight" stands beside subset-minimality, cardinality and
   prioritization as a standard preference (Eiter & Gottlob 1995, abstract).
3. *A shared assumption is paid once.* That is the purpose of factoring: an assumption
   that explains several goals costs what it costs for one, and this is how redundancy
   in a text is turned into a cheaper explanation (Hobbs et al. §4.1). In our setting
   the same effect is automatic: an axiom is counted once however many claims it
   derives.
4. *The one principled reading of a cost is a negative log probability.* Under
   restrictions, minimum cost equals maximum posterior probability (Charniak & Shimony
   1990, as summarized by Hobbs et al. §8.3). Since a code with lengths −log P exists
   for every distribution (Grünwald §2.2), this is also the two-part MDL reading with
   the cost as the description length of the hypothesis. The two justifications the
   pack lists are one justification seen twice, which is weaker support than two
   independent ones.
5. *Simplicity is a strategy, not a truth claim.* MDL "is a strategy for inferring
   models from data", not the statement that simple models are more likely true
   (Grünwald §1.6). Peirce, via Hobbs et al., accepts a hypothesis only "as an
   interrogation".

### 3.2 What our function is

cost(A) = Σ (1 − p(a)) + λ·|A| is a sum of a fixed charge per axiom,
c(a) = (1 − p(a)) + λ, between λ and 1 + λ. In the terms of the literature it is
cost-based abduction with intrinsic costs, the Charniak–Shimony form, and not the
propagated weights of Hobbs et al. The λ·|A| term is not a second principle; it is the
part of each charge that does not depend on plausibility.

Fix p(e) = 1 for reviewed stated claims (section 5, A4). Write u(A) = Σ (1 − p(a)) for
the total implausibility and n(A) = |A|. Then cost = u + λ·n, and:

**P1. Cost-minimal implies no idle axiom.** If λ > 0, dropping an unused axiom lowers
the cost and keeps (S1) and (S3), so a cost-minimal set satisfies (S4).

**P2. What λ means.** The stated system A₀ costs λ·n(A₀). An unstated axiom of
plausibility p that lets k stated claims be derived instead of assumed lowers the cost
exactly when p > 1 − (k − 1)·λ. So λ is an exchange rate: one axiom saved is worth λ
units of plausibility. With λ = 0.3, an unstated axiom must reach 0.7 to replace two
claims, 0.4 to replace three, 0.1 to replace four.

**P3. The charge is bounded, so compression can buy anything.** No axiom costs more
than 1 + λ. An axiom that replaces more than 1 + 1/λ stated claims is preferred
*whatever its plausibility*: with λ = 0.3, replacing five claims suffices even at p = 0. Under the
logarithmic reading the charge is −ln p, which is at least 1 − p everywhere and
unbounded near 0. The linear form is the first-order approximation of the principled
one near p = 1 and is more permissive everywhere else.

**P4. Counting axioms can be gamed by conjunction.** The single axiom e₁ ∧ … ∧ eₙ is
consistent, sufficient, restrained and has no idle part, and it has size 1. If its
plausibility is judged high, as it will be when every conjunct is quoted from the
text, it costs about λ and beats every honest system. This is the general weakness of
two-part codes, where the length of a hypothesis depends on the code (Grünwald §1.4),
in our notation.

**P5. Only some systems can ever win.** As λ varies, the minimizer of u + λ·n runs over
the lower convex hull of the points (n(A), u(A)). The systems on that hull, and the
interval of λ on which each is optimal, can be computed exactly from the list of
certified systems. A system that is optimal only on a sliver of λ is a fragile choice.

### 3.3 What the sources do not establish

- *The numbers.* No source gives a standard value for a size penalty. The authors of
  weighted abduction call their numbers ad hoc and report tuning them on a corpus
  (Hobbs et al. §4.1, §8.3). The pack's phrase "the standard abduction/MDL trade-off"
  for λ ≈ 0.3 has no support in what I read; 0.3 is an initial setting.
- *That plausibility is a probability.* The logarithmic reading needs p(a) to behave
  like one. An estimate produced by a language model has not been shown to; that is
  Session 3 material (RQ5).
- *That hypothesizing rules is abduction.* By Hobbs et al.'s own division (§4.1),
  proposing (∀x) p(x) ⊃ q(x) is induction, and their scheme takes the rules as given
  and mutually known. We have no shared rule base. The nearer formal precedent for the
  whole problem is induction with positive and negative evidence (Muggleton & De Raedt
  1994), where a restriction on the hypothesis language is treated as unavoidable.
- *That fit is accounted for.* Two-part MDL has a second term, L(D|H), that penalizes a
  hypothesis for allowing much more than was observed. Our cost has none: a system
  that entails E⁺ and a great deal besides pays nothing for the excess. The specificity
  trade-off of Hobbs et al. ("the less specific … the more likely … correct") is the
  same concern. Soft rejections are the only brake, and the Phase 8 holdout test is the
  only measurement of whether the excess is predictive.
- *That the winner is decisive.* Hobbs et al. flag as a shortcoming that their score
  ignores how far the best explanation is ahead (§8.3).
- *That economy beats coherence.* Ng and Mooney (1990) argued for an explanatory
  coherence criterion; Hobbs et al. dispute it (§7.3). Session 1 had read only the
  latter's account. Session 2 read Ng and Mooney; see section 8.5, item 4.

### 3.4 Recommendations

1. Keep the additive form and call it what it is: a cost-based selection strategy, with
   weighted abduction as precedent for the form and no precedent for the values.
2. Repair P4 before any search is written: count size on a normal form in which a
   conjunction cannot hide (split conjunctions, at the top level and under universal
   quantifiers, after negation normal form), and report literal count as a secondary
   measure. The exact normal form belongs in the Phase 3 design document.
3. Contain P3: require a minimum plausibility for unstated axioms, or use −ln p, and in
   either case report results under both the linear and the logarithmic charge.
4. Replace "λ ≈ 0.3" as a single setting by the report of P5: the hull, the λ-interval
   of each reported system, and the margin to the runner-up. Calibrate a default on the
   golden corpus in Phase 7 as the value whose selected system agrees best with the
   hand-worked reconstruction, and publish the agreement over a grid of λ. This follows
   the practice Hobbs et al. describe and addresses their decisiveness shortcoming.
5. Show the excess. For each reported system list the pool statements it entails that
   the camp never endorsed, and include withheld *rejections*, not only withheld
   endorsements, in the Phase 8 holdout test, so that over-generation is measured.
6. Say in `THEORY.md` that proposing warrants is induction selected by an abductive
   cost, and that the selected system is a hypothesis in Peirce's sense.

## 4. Critique of the source pack (Session 1 scope: B1, B2, B5, C2, H2–H4, I.4, I.6)

| Entry | Finding |
|---|---|
| Pack protocol | B1 and C2 were tagged "web-verified" and both carried errors. The tag confirms that a paper exists, not that the entry is right. Treat every entry as unverified until re-checked. |
| B1 Lin 2001 | **Wrong pages.** 128(1–2), 143–159, not 128(2), 249–261. |
| B1 | **Overstated.** Lin defines the conditions for a proposition under a theory on a restricted vocabulary, in propositional logic; not "for a formula φ" in general, and not for first-order theories, where he expects them not to be expressible. |
| B1 | **Not in the paper.** "Abduction is characterized as computing approximations of these." Lin calls the WSC the most general abduction and contrasts it with the parsimonious explanations abduction usually computes. |
| B1 | **Wrong design implication.** "A should approximate the WSC … as weak/general as the cost function allows." Cost pushes towards fewer and stronger axioms; the WSC is the weakest. See RQ1 (a). |
| B2 Hobbs 1993 | **Wrong pages.** 63(1–2), 69–142, not 319–350. |
| B2 | **Partly right.** The additive, minimum-cost form is theirs. The claim that λ ≈ 0.3 is "the standard abduction/MDL trade-off" is unsupported. Our function is closer to Charniak and Shimony's cost-based abduction, which the pack omits. |
| B5 Rissanen 1978 | Bibliographic data correct. Add the caveat that hypothesis length is code-dependent (Grünwald), which is exactly our P4. |
| C2 Liffiton & Sakallah | **Wrong attribution.** The 2008 paper is CAMUS. MARCO is Liffiton, Previti, Malik and Marques-Silva (2016), from Liffiton and Malik (2013) and Previti and Marques-Silva (2013). `argmap.py` implements MARCO, so the pack's citation for it is wrong; the 2008 paper remains right for the definitions and the duality. |
| C2 | "MUS relaxation explanation style" is not a term of the paper. What it offers for explanation is the MCS, the smallest set to give up, and grouping by statement (§7.2). |
| H2 | Restate: A is a sufficient condition; the WSC is the invariant shared by all sufficient conditions in a vocabulary; selection is by cost, not weakness. |
| H3 | Restate: the form is weighted or cost-based abduction; MDL is the same justification in other words, and adds a caveat; λ trades plausibility against count and its value is not grounded. |
| H4 | The MUS part stands on Liffiton and Sakallah. Add the two tiers of RQ1 §2.4: conflicts among stated claims are invariant, conflicts among reconstructed axioms are system-relative. C1 and C3 are not yet verified. |
| I.4 | Answered in RQ3 §3.4, item 4. |
| I.6 and D1 note | **Conflation.** Firm and soft are strengths of a camp's rejection (brief §4), not "prover says no" against "unproven". Both can be certified, by a proof and by a countermodel; "unproven" is no verdict. See RQ1 §2.5. |

Sources the pack lacks for Themes B and C, all in section 1: Doherty et al. (2001) and
Doherty and Szałas (2024) for the first-order case; Stickel (1991) and Charniak and
Shimony (1990, 1994) for the origin and the semantics of costs; Eiter and Gottlob
(1995) for the place of minimal weight among preference criteria; Muggleton and De
Raedt (1994) for negative evidence; Liffiton et al. (2016) for MARCO; Grünwald (2004)
for a readable statement of MDL and its limits.

## 5. Amendments to brief §4 proposed for the owner's decision

The brief allows changes to its definitions "only with a written rationale in
`THEORY.md`". On 13 November 2026 the owner said to proceed on them ("following the
upgrade decisions"). They are adopted for drafting and remain subject to the owner's
review of the finished `THEORY.md`; none is applied anywhere but in the drafts.

| # | Amendment | Rationale |
|---|---|---|
| A1 | Minimality means no proper subset is sufficient. | RQ1 §2.2. |
| A2 | The definition and the interface name the pool: "cost-minimal among the reviewed candidates". | RQ1 §2.2. |
| A3 | Size is counted on a normal form that splits conjunctions. | RQ3 P4. |
| A4 | Stated, reviewed claims have plausibility 1. Unstated axioms need a quote and a minimum plausibility, or a logarithmic charge. | RQ3 P2, P3. |
| A5 | Reports give the hull of (size, implausibility), each system's λ-interval and the margin to the runner-up, not one λ. | RQ3 P5. |
| A6 | Soft rejections are required separately; joint failure is reported. | RQ1 §2.5. |
| A7 | Conflicts and common ground are reported in two tiers: among stated claims, and among reconstructed axioms. | RQ1 §2.4. |

## 6. Carried to later sessions

Done in Session 2 (sections 7–10): RQ2, the terminology decision, the novelty search,
Ng and Mooney (1990), the page range of Doherty et al. (2001), the Reiter and de Kleer
(1987) record. Still open from this list:

- Read Charniak and Shimony (1994) itself (section 7.3).
- The coverage metric for records with no axiom system (pack §I.1): Session 3, with
  Converse. The existence fact in RQ1 §2.4 is its formal starting point.
- Whether a language model's plausibility estimate can be read as a probability, and
  the elicitation protocol (pack §I.5): Session 3.

## 7. Session 2: sources (14 November 2026)

Session 2 was started on 13 November, stopped, and finished on 14 November 2026. The
tables below replace the interim state recorded on the 13th. Tags are those of
section 0; "S2" marks what was checked in this session.

### 7.1 Classic entries of Themes A, B and C

| Entry | Result |
|---|---|
| A1 Toulmin (1958), *The Uses of Argument*, Cambridge University Press | `[bib]` Confirmed through two contemporary reviews indexed by Crossref (*Philosophy* 34(130), 244–245; *The Cambridge Law Journal* 16(2), 251–252), which give publisher, year and "viii + 264" pages. **Not read.** Everything said about Toulmin below is attributed to a source that was read. |
| A2 Walton, Reed & Macagno (2008), *Argumentation Schemes*, Cambridge University Press | `[bib]` doi:10.1017/CBO9780511802034. Not read. |
| B3 Alchourrón, Gärdenfors & Makinson (1985) | `[bib]` **Pack errors:** the second author is P. Gärdenfors, and the title continues ": Partial meet contraction and revision functions". *Journal of Symbolic Logic* 50(2), 510–530, doi:10.2307/2274239. |
| B4 Nebel (1991) | `[abstract]` S2. **Pack error:** the paper is not in *Artificial Intelligence*. It is Nebel, B. (1991), "Belief revision and default reasoning: Syntax-based approaches", in Allen, Fikes & Sandewall (eds.), *Proc. KR'91*, Morgan Kaufmann, 417–428 (header and abstract of the author's copy, `nebel-kr91.pdf` at uni-freiburg.de). A revised version is Nebel (1992), "Syntax based approaches to belief revision", in *Belief Revision* (Cambridge University Press), 52–88, doi:10.1017/CBO9780511526664.003 `[bib]`. Not used in any argument below. |
| C1 Baader & Suntisrivaraporn (2008), "Debugging SNOMED CT using axiom pinpointing in the description logic EL+", *Proc. KR-MED 2008*, CEUR-WS Vol-410 | `[abstract]` S2. Listed in the volume's table of contents at ceur-ws.org; abstract, the passage defining the task and the conclusions read in the authors' copy. The task: for a consequence, compute "a minimal subset (all minimal subsets) of the ontology that have this consequence", called MinAs. |
| C1 Schlobach & Cornet (2003) | `[bib]` "Non-standard reasoning services for the debugging of description logic terminologies", *Proc. IJCAI-03*, 355–362 (pages from a secondary index). Journal follow-up: Schlobach, Huang, Cornet & van Harmelen (2007), "Debugging incoherent terminologies", *Journal of Automated Reasoning* 39(3), 317–349, doi:10.1007/s10817-007-9076-z. Baader & Suntisrivaraporn cite the 2003 paper among the early work on pinpointing; **whether it coined the term is not established** by anything read, so the pack's "coined by" is not repeated. |
| C1 Peñaloza, "Explaining axiom pinpointing" | `[bib]` Peñaloza, R. (2019), LNCS, 475–496, doi:10.1007/978-3-030-22102-7_22. The pack's title adds "in description logics". Related records seen on Crossref in S2: Baader, Peñaloza & Suntisrivaraporn (2007), "Pinpointing in the description logic EL+", KI 2007, LNCS, 52–67, doi:10.1007/978-3-540-74565-5_7; Baader & Peñaloza (2010), "Axiom pinpointing in general tableaux", *Journal of Logic and Computation* 20(1), 5–34, doi:10.1093/logcom/exn058. Both `[bib]`. |
| C3 Reiter (1987) | `[bib]` **Pack error:** pages are 57–95, not 1–32. *Artificial Intelligence* 32(1), doi:10.1016/0004-3702(87)90062-2. |

### 7.2 Theme A and the terminology sources

| Entry | Result |
|---|---|
| A3 Sviridova, Cabrio & Villata, "Mining implicit arguments for reasoning: A survey" | `[abstract]` *Argument & Computation* 17(1), 3–27, doi:10.1177/19462174251344764. Crossref dates it 2025; the pack says 2026 and names the publisher where the journal belongs. **Full text not read:** the HAL copy and the publisher's page refuse automated access, and such refusals are not worked around. The pack's account of what the survey says is unconfirmed, and RQ2 does not rest on it. A copy from the owner would let Session 4 close this. |
| A4 Saadat-Yazdi & Wagemans (2025), "Finding the missing link: An algorithmic approach to reconstructing enthymemes" | `[abstract]` plus the opening of each section (read on 13 November). **Pack error:** the pack names Wagemans as first author. *Argumentation*, online first 30 October 2025, doi:10.1007/s10503-025-09682-z. A procedure for a human analyst built on the Periodic Table of Arguments; the abstract says it "can function as a guideline for human annotation" and is "suitable for implementation" in annotation software. The publisher's page refused the S2 request, so the read-through planned for this session was not done. |
| A5 Lawrence & Reed, "Argument mining: A survey" | `[bib]` *Computational Linguistics* 45(4), 765–818, doi:10.1162/coli_a_00364 (Crossref dates it 2020). Not read. |
| A6 Li, Schlegel, Sun, Batista-Navarro & Nenadic (2025), "Large language models in argument mining: A survey" | `[abstract]` arXiv:2506.16383. The finding the pack quotes from it is Session 4 material (RQ6) and is not confirmed. |
| Hitchcock, D. (1985). Enthymematic arguments. *Informal Logic* 7(2–3), from p. 83. doi:10.22329/il.v7i2.2707 | `[read]` S2: the opening pages, the passage stating the thesis (pp. 87–88) and the closing page, in the journal's open PDF. Added in S2. |
| Habernal, Wachsmuth, Gurevych & Stein (2018). The argument reasoning comprehension task: Identification and reconstruction of implicit warrants. *Proc. NAACL-HLT 2018*, 1930–1940. doi:10.18653/v1/N18-1175 | `[abstract]` S2. Added in S2: the dataset (ARCT) on which two of the systems below are evaluated. |
| Ennis, R. H. (1982), "Identifying implicit assumptions", *Synthese* 51(1), 61–86, doi:10.1007/BF00413849 | `[bib]` Not read, and therefore not used in the terminology decision. |

### 7.3 Carried items from Session 1

| Item | Result |
|---|---|
| Doherty, Łukaszewicz & Szałas (2001), page range | **Resolved:** 145–153, per the proceedings index of IJCAI-01 at ijcai.org. The two ranges seen in Session 1 (145–154, 145–151) are both wrong. Section 1.2 is corrected. |
| Reiter & de Kleer (1987) | `[abstract]` Reiter, R., & de Kleer, J. (1987). Foundations of assumption-based truth maintenance systems: Preliminary report. *Proc. AAAI-87*, 183–188 (page numbers printed in AAAI's own copy, six pages). The abstract defines a clause management system as a generalization of de Kleer's ATMS and characterizes its computation by prime implicants, which is what Lin (§5) cites it for. Section 1.2 is corrected. |
| Ng & Mooney (1990) | `[read]` Ng, H. T., & Mooney, R. J. (1990). On the role of coherence in abductive explanation. *Proc. AAAI-90*, 337–342. Abstract, §1, §2, the opening of §3.1 and the definition of the metric, in AAAI's own copy. See section 8.5. |
| Charniak & Shimony (1994) | `[bib]` **Still not read.** The publisher refuses automated access and no open copy was looked for in S2. RQ3's statement about the probabilistic reading of costs therefore still rests on Hobbs et al.'s summary (§8.3). |

### 7.4 Systems found in the novelty search

*Scope of the search.* (1) Fifteen keyword queries on the public arXiv API, submissions
since June 2024, and title lookups for eight earlier systems (13 November). (2) The
tables of contents of the ArgMining workshops of 2025 (39 papers) and 2026 (17 papers)
in the ACL Anthology, read by title. (3) Seven web searches aimed at ACL, EMNLP, AAAI,
COMMA and KR in 2025–2026, which led to one IJCAI 2025 paper, one KR 2026 paper and one
arXiv system. *Not covered:* the full proceedings of ACL, EMNLP and AAAI 2026 were not
read through, and no programme or proceedings of COMMA 2026 was located.

| Work | Tag | What it does (from the parts read) | Unit of analysis; what certifies |
|---|---|---|---|
| Quan, X., Gubelmann, R., & Freitas, A. (2026). Autoformalizing argumentative material inferences. arXiv:2609.16991v1 | `[read]` abstract, introduction, problem definition, Figure 1, conclusion. Not read: method details, experiments, appendices. | GUARD. For a premise–claim pair (T, C) it builds a "strengthened context" of assumptions, definitions and exception conditions, selects a guard set G with G ∪ {T} ⊨ C, and has Isabelle/HOL check the theory, feeding failed proof steps back. A proved completion is accepted only if it also survives two contrastive tests: with the premise replaced by one that should not support the claim, and with the claim replaced by one the premise does not warrant, the theory must become unprovable. Otherwise the system rejects it as leaky or abstains. Evaluated on Debatepedia and ARCT with four language models; the authors attribute 63.5 to 74.3 percent of abstentions to missing guards. | One premise–claim pair. A proof assistant, plus contrastive tests. No human review step appears in the parts read. |
| Feng, X., & Hunter, A. (2026). Making implicit premises explicit in logical understanding of enthymemes. arXiv:2603.06114v3 | `[read]` abstract, §1, §2.2, §3.1–3.3, §4, opening of §5, §6. | A language model generates one to three intermediate premises for a premise and a claim; an AMR parser and a translator turn each sentence into a propositional formula; atoms are identified with one another when their sentence embeddings are similar above a threshold, with an NLI model as contradiction check; PySAT decides entailment on the result. Evaluated on ARCT and ANLI as a choice between a helpful and an unhelpful candidate. Best F1 for the entailment class on ARCT: 0.58 with three generated steps, 0.21 with the dataset's own premise; thresholds are chosen per dataset and class. The authors state that the experiments "do not evaluate unrestricted generation". | One premise–claim pair. A SAT solver over formulas *relaxed* by embedding similarity: the entailment shown depends on a tuned threshold. |
| Feng, X., & Hunter, A. (2026). Identifying implicit premises for logical reconstruction of argument graphs. arXiv:2608.18821v1 | `[read]` abstract, §1, discussion. | The same pipeline, used to generate implicit premises that establish a *given* relation (entailment, contradiction, neutral) between a premise and a claim. Evaluated on the Microtext corpus. End-to-end processing of plain text is named as future work. | One edge of an argument graph, with the relation label supplied. |
| David, V., & Hunter, A. (2025). A logic-based framework for decoding enthymemes in argument maps involving implicitness in premises and claims. *Proc. IJCAI-25*, 4445–4453. doi:10.24963/ijcai.2025/495 | `[read]` abstract, §1, opening of §2, the passage introducing the MaxSAT encoding. | An argument map (nodes with premise and claim text, arcs labelled support, attack or none) is given, together with a knowledge base of default rules. Decoding an enthymeme means choosing, for each node, which default rules are implicit in it. The choice over the whole map is an optimization problem: maximize the number of arcs whose label agrees with the logical relation between the decoded arguments; hard constraints encode the candidates, soft constraints the arcs, and a MaxSAT solver returns a solution. The authors say of earlier proposals that "none consider optimization of decoding". | A whole argument map. Default logic and MaxSAT. The knowledge base of candidate rules is assumed, not obtained from text. |
| Ben-Naim, J., David, V., & Hunter, A. (2026). Elucidating arguments maps in propositional logic: Addressing enthymemes and their relationships. *Proc. KR 2026*, Main Track, 156–166. doi:10.24963/kr.2026/15 | `[abstract]` | A framework in classical propositional logic with meta-level rules that add or delete premises, edit claims, split and merge arguments, and "gain measures" to direct the choice of rules, so that arguments attack or support one another as argument mining predicts or the user requires. | A whole argument map; an incremental, rule-directed elucidation. |
| Ku, H. B., Shin, J., Lee, H. J., Na, S., & Jeon, I. (2025). Multi-agent LLM debate unveils the premise left unsaid. *Proc. 12th Argument Mining Workshop*, 58–73. doi:10.18653/v1/2025.argmining-1.6 | `[abstract]` | Implicit-premise recovery as a debate between two language-model agents, evaluated on a binary premise-selection benchmark. | One argument. No formal check. |
| Stieger, B., Terberger, M., Huber, T., & Niklaus, C. (2026). TruthSplit: Operationalizing conditional validity in arguments through multi-perspective reasoning. arXiv:2606.09251 | `[abstract]` | An interactive system that extracts claims and premises from a text, applies a three-layer NLI approach for "logical and worldview-specific normative consistency", conditions a language model on "structured worldview profiles", and shows value conflicts and assumption gaps between perspectives. | One text read under several worldview profiles. Language-model inference; no solver or prover is mentioned in the abstract. |
| Komendarczyk, R., Block, W. E., Levendis, J., & Tipler, F. J. (2026). A formalization of Austrian economics. Praxeological foundations. arXiv:2606.18292 | `[abstract]` (13 November) | A hand-made axiomatization of one school's doctrine in many-sorted first-order logic, with a Lean 4 companion whose model serves as a consistency proof. | A body of doctrine, axiomatized by hand and kernel-checked. |

Earlier systems confirmed to exist on arXiv by title only, abstracts not read: DeepA2
(2110.01509), two papers by Quan and colleagues on refining explanations with a theorem
prover (2405.01379, 2505.24264) and one on ethical explanations (2402.00745), Ben-Naim
and colleagues on enthymemes in argument maps (2408.08648), VeriCoT (2511.04662),
BeliefBank (2109.14723). A system expected under the name NL2FOL returned no title
match and stays `[unverified]`. Also `[bib]` from S2: Black, E., & Hunter, A. (2012), A
relevance-theoretic framework for constructing and deconstructing enthymemes, *Journal
of Logic and Computation* 22(1), 55–78, doi:10.1093/logcom/exp064, cited by the two
groups above as the abductive account of enthymeme decoding.

## 8. RQ2. Is reconstructing a camp's axioms from text plausible, and what is the precedent?

**Short answer.** Reconstructing unstated premises is an old task in the theory of
argument and, since 2018, a measured one in language technology; in 2025–2026 it was
joined to formal checking by at least two groups. That makes our *task* plausible and
our *novelty claim* narrower than the pack states. What the precedent supports is the
reconstruction of premises that make a stated inference go through. It does not support
the recovery of what an author believes, and the one theorist read in full separates the
two explicitly. The measured accuracy of the generating step is modest, which is the
empirical case for keeping review and certification in the loop.

### 8.1 The precedent in the theory of argument

Hitchcock (1985) opens with "the tendency of most arguers to leave implicit an
assumption in virtue of which their conclusion follows from their premisses", and
credits the theme to Perelman, Toulmin, Hamblin, and van Eemeren and Grootendorst. Three
points in that paper bear on our design.

1. *What is reconstructed is disputed in kind.* Hitchcock reports that some authorities
   (he names Bolzano, Ryle, Toulmin and George) "deny that enthymemes have missing
   premisses", and announces that he will defend the denial (the defence is in a part
   of the paper not read). Habernal et al. (2018)
   use Toulmin's word in the same role: a warrant "explains why its claim follows from
   its premises" and is "usually presupposed and left implicit". Our pool members are
   first-order sentences used as premises, so we take the other side of this dispute by
   construction. That is a modelling choice and has to be stated as one.
2. *There is a precedent for trading generality against plausibility.* Hitchcock's
   thesis is that an enthymeme "implicitly assumes a universal generalization of its
   associated conditional over its repeated content expressions, in fact the maximal
   generalization consistent with plausibility". This is the informal-logic counterpart
   of RQ3: prefer the more general assumption, up to the point where it stops being
   plausible. It is stated for one argument and gives no measure of plausibility.
3. *The assumption of an argument is not the belief of its author.* On his closing page
   Hitchcock treats "evidence of the arguer's beliefs" as something that may help
   "resolve ambiguities about the argument's implicit assumption", and lists purposes
   for which an analyst supplies a premise "somewhat stronger than the assumption
   implicit in the argument itself". Reconstruction is guided by charity: the presumption
   that the argument "will become deductively valid if the arguer's assumptions are
   added as extra premisses". The reconstructed premise is thus an object distinct from
   both the text and the author's mind. Brief §5 ("verified sufficient", never "their
   beliefs") is this distinction turned into a language rule.

Toulmin (1958), Walton, Reed and Macagno (2008) and Ennis (1982) are verified as
records and were not read; nothing here is attributed to them directly.

### 8.2 The precedent in computation

Three lines of work, all in section 7.4.

*A measured task.* Habernal et al. (2018) built a dataset of about 2,000 arguments from
news comments with crowd-sourced warrants and posed the choice between two candidate
warrants as a task; their abstract reports that the neural models of the time "do not
suffice". Ku et al. (2025) report state-of-the-art accuracy on a binary premise-selection
benchmark with debating language models. So the generation and selection of unstated
premises is measurable and is not solved.

*Reconstruction joined to a formal check, per argument.* Feng and Hunter (2026) and Quan,
Gubelmann and Freitas (2026) both have a language model propose the missing premises
and a symbolic system test whether the claim then follows. They differ in what the test
is worth. Feng and Hunter identify atoms by embedding similarity before the solver
runs, so the entailment they report holds for a relaxed formula and moves with a
threshold. Quan et al. hand an explicit theory to a proof assistant and add tests that
the proof depends on the original premise and does not prove a contrast claim.

*Reconstruction over a whole argument map, by optimization.* David and Hunter (2025)
decode all the enthymemes of an argument map at once, choosing implicit default rules
so as to maximize agreement with the support and attack arcs that argument mining
produced, with MaxSAT. Ben-Naim, David and Hunter (2026) do the elucidation
incrementally in propositional logic. These are the nearest formal precedents for the
argument-graph architecture adopted for Phase 3 (owner decision, 13 November 2026). They
assume the candidate rules are given; the two 2026 pipelines above are, in Feng and
Hunter's words, the attempt to supply what "symbolic approaches currently assume".

### 8.3 What is and is not established

Established by sources read:

1. Leaving the licensing assumption unstated is the normal case in argument, and
   reconstructing it is a recognized analytical task (Hitchcock 1985).
2. Candidate unstated premises can be generated by a language model and tested
   symbolically, and when the generator is free, a valid proof is weak evidence: "a
   system free to add premises can make any claim provable, and a formally valid proof
   may assert the claim outright, prove it without the original premise, or establish
   more than the claim itself" (Quan et al. 2026, abstract).
3. Selecting among decodings of a whole map is an optimization problem with a declared
   objective (David & Hunter 2025).
4. The generating step is unreliable enough to need a gate. On ARCT, Feng and Hunter's
   best F1 for the entailment class is 0.58; Quan et al.'s system abstains rather than
   accept, and most abstentions are missing premises.

Not established by anything read:

1. *That the reconstructed premises are the author's.* No source read claims this, and
   Hitchcock distinguishes the two. Whether people's stated positions have the
   deductive structure a reconstruction presupposes is the Converse question, and
   belongs to Session 3.
2. *That a reconstruction is unique or stable.* The per-argument systems return one
   completion or abstain; none reports the set of alternatives or how the choice varies
   with a parameter. RQ3's hull report (amendment A5) has no counterpart in them.
3. *That per-argument accuracy carries over to a whole record.* All measured results are
   for one premise–claim pair with the candidates or the relation label supplied. Feng
   and Hunter name unrestricted generation and end-to-end processing as future work.
4. *That a strict logic can be kept at scale.* Feng and Hunter relax the logic to obtain
   their results. We keep symbols strict and move the alignment of vocabulary into human
   review; the price is visible in our own FOLIO runs, where a share of formalizations
   fail (README). Nothing read shows how that price changes on debate text.

### 8.4 Where Common Ground stands

The pack's claim under A3, that nobody combines the reconstruction of unstated premises
with formal verification and that "that intersection … is our contribution", is false
as worded: Feng and Hunter (2026) and Quan et al. (2026) do exactly that, and David and
Hunter (2025) optimize a reconstruction over a whole map. The differences that remain,
each stated against the nearest precedent:

| Our design | Nearest precedent | Difference |
|---|---|---|
| Unit: the whole reviewed record of a camp, E⁺ and R_soft; one set A must entail every claim | Quan et al. (pair); David & Hunter (map of separate arguments) | A single jointly sufficient and consistent set for all claims of a camp. Not found. |
| Rejections constrain the system: A ⊭ r, shown by an explicit countermodel | Quan et al., claim-contrast test: the contrast theory must be unprovable | Theirs is a failed proof search on a generated contrast; ours is a model, for claims the camp itself declined. Failure to prove is not a countermodel (RQ1 §2.5). |
| Selection among *several* certified systems by a declared cost, reported with its sensitivity | David & Hunter, MaxSAT objective: agreement with mined arcs | A different objective (plausibility and size, not arc agreement), and the alternatives are reported. Not found. |
| Entailments checked by the Lean kernel; no model text reaches Lean without human approval | Quan et al., Isabelle/HOL on model-written theories | Same kind of guarantee for the deduction. The difference is the human gate and the evidence quote required for every unstated axiom. |
| Minimal conflicts between two camps' systems (MUS) and provable common ground | TruthSplit (perspective divergence by language-model inference) | Formal conflict sets with certificates. Not found. |
| Strict symbols; vocabulary aligned in review | Feng & Hunter, embedding-similarity relaxation | A deliberate refusal of the relaxation, at the cost of more failed formalizations. |

**The claim this supports,** to be used in `THEORY.md` and the README: *within the
search described in section 7.4, we found no system that reconstructs one consistent
set of first-order axioms jointly sufficient for all reviewed claims of a camp,
constrained by the camp's rejections, selected by a declared cost among certified
alternatives, and compared across camps by minimal conflict sets. Every ingredient has a
precedent, cited above; the combination and the unit of analysis are what is new.* It
must be worded as "we found no", never as "none exists": three venues were not read
through and one was not located.

### 8.5 Design consequences

1. *Adopt the contrastive tests as named checks.* Quan et al.'s two tests have exact
   counterparts in RQ1. Premise dependence is (S4): no proper subset is sufficient, so
   every axiom is used. Claim selectivity is (S3) plus the excess report of RQ3 §3.4:
   the system must not entail what the camp declined, and what it entails beyond the
   record is listed. The Phase 3 design document should name both and cite this
   precedent. Their "asserts the claim outright" failure is our P4 (a conjunction of the
   claims as a single axiom); amendment A3 stands.
2. *Use the discourse graph as a check, not as the objective.* David and Hunter score a
   decoding by agreement with mined support and attack arcs. The relations extracted in
   Phase 2 allow the same comparison: a "supports" relation between two statements can
   be compared with membership in a minimal premise set, an "attacks" relation with
   joint inconsistency. Report the agreement for the selected system. Making it part of
   cost(A) would change brief §4 and would let an unreviewed extraction steer a
   certified result; that needs its own rationale and is not proposed here.
3. *Abstention is a result.* A record for which no reviewed pool yields a system better
   than the stated one A₀ should be reported as such. Quan et al. report most of their
   abstentions as missing premises; our equivalent is "the pool contains no unstated
   axiom that pays for itself".
4. *Coherence, read at last.* Ng and Mooney (1990) argue that the simplicity criterion
   "is not sufficient by itself": with a count of assumptions, "John was happy. The exam
   was easy." is best explained by assuming John is an optimist, which leaves the two
   sentences unconnected. Their coherence metric counts, over pairs of observations, the
   nodes of the proof graph from which both are reached. For us this is the load of
   brief §4 seen from the other side: an axiom with load above one connects claims. The
   cost already rewards it (RQ3, P2), and it does so only through the count of axioms.
   RQ3 §3.3's open item is therefore answered in part: economy and coherence pull the
   same way when every claim must be derived, which (S2) requires; they can differ in
   how they rank two systems of equal cost. Reporting, for each selected system, the
   number of claims each axiom is needed for (the load vector) makes the difference
   visible without a second criterion.

## 9. Terminology decision (for the owner's approval)

Brief §3 asks for a decision between "axiom", "warrant" and "implicit premise".

**Proposed.** Keep **axiom** for a member of a certified system. Qualify it by
provenance: a **stated axiom** is a reviewed claim quoted from the camp's texts; an
**unstated axiom** is a reviewed candidate that no text states, shown with its evidence
quotes. Do not use "warrant" or "implicit premise" in the interface. Use them in
documentation only to relate our objects to the literature.

**Rationale.**

1. *"Axiom" names a role in a deduction and nothing else.* A sentence is an axiom of a
   system because derivations start from it. The word makes no claim about a mind, which
   is what brief §5 requires. First use in the interface carries the gloss "a statement
   the derivations start from; verified sufficient, not a claim about what anyone
   believes".
2. *"Warrant" names something else in the sources read.* For Habernal et al. (2018) a
   warrant belongs to one argument and explains one step. Hitchcock (1985) places
   Toulmin among those who deny that enthymemes have missing premisses at all. Our
   objects are premises of a system that serves all of a camp's claims. Using "warrant"
   would import a per-argument, licence-not-premise meaning that our definition does not
   have.
3. *"Implicit" asserts more than we can show.* "Implicit premise" says the premise is in
   the argument, unspoken. What review and certification establish is weaker and
   checkable: the sentence is not stated in the texts, and it is sufficient together
   with the others. "Unstated" says the first and no more; "verified sufficient" says the
   second. Hitchcock's distinction between the assumption implicit in an argument and a
   stronger premise supplied by an analyst (section 8.1) is the reason to keep them
   apart: a cost-minimal system may well contain the second kind.
4. *One term across the product.* The engine, the brief and the golden corpus already
   say "axiom".

**Cost of the choice.** "Axiom" can read as self-evident truth. The gloss, the motto
and the two badges of brief §5 are the mitigation. If the owner prefers a plainer
word for lay readers, "starting point" is the candidate that loses least.

## 10. Critique of the source pack (Session 2 scope: Theme A, classic entries of B and C, H1, I.3)

| Entry | Finding |
|---|---|
| A3 | The entry's "design implication" states the novelty claim, which is false as worded (section 8.4). Date and publisher field wrong (section 7.2). Content unconfirmed: full text not obtained. |
| A4 | **Wrong first author.** It is Saadat-Yazdi & Wagemans. It describes a procedure for human analysts; the pack's inference that it "supports abduce.py's generate-then-rank design" goes beyond the abstract. The support for generate-then-select found in S2 is David & Hunter (2025) and Quan et al. (2026). |
| A1, A2 | Records verified, books not read. The pack's sentence that our axiom "is close to Toulmin's backing" is not confirmed by anything read and conflicts with section 9. |
| B3 | Author initial and title corrected (section 7.1). |
| B4 | **Wrong venue, volume and pages.** KR'91, 417–428 (section 7.1). |
| C1 | Record verified. "Coined by Schlobach & Cornet" not established. |
| C3 | **Wrong pages.** 57–95. |
| H1 | Restate: reconstructing unstated premises is an established and measured task for single arguments, and has been joined to formal checking; we extend the unit from an argument to a camp's whole record and add selection, rejections and cross-camp conflict sets. "Generalizes" is fair for the unit; it is not a claim that per-argument accuracy carries over. Cite Hitchcock (1985), Habernal et al. (2018), Quan et al. (2026), Feng & Hunter (2026), David & Hunter (2025). |
| I.3 | Answered in sections 7.4 and 8.4, with the stated limits of the search. |
| I.7 (d) | One system found (TruthSplit); by its abstract it works by language-model inference under worldview profiles. BeliefBank is confirmed by title only. Belief inference proper (D2, D3) is Session 4. |
| Pack, missing | The Hunter group's logic-based line (Black & Hunter 2012; David & Hunter 2025; Ben-Naim et al. 2026) is absent from the pack and is the closest formal precedent for the argument-graph architecture. |

## 11. Carried to Sessions 3 and 4

- Session 3: Converse and the question of section 8.3, item 1; the coverage metric;
  whether a model's plausibility estimate can be read as a probability; elicitation.
- Session 4: A6, D2, D3, G3 and RQ6; the finding the pack attributes to A6; write H1
  into `THEORY.md` in the wording of section 10; record the terminology decision there
  if the owner approves it.
- Open, any session: full text of A3 and A4 (copies from the owner); Charniak and
  Shimony (1994) itself; the three venues not read through (ACL, EMNLP, AAAI 2026) and
  COMMA 2026.
