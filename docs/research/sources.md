# Research Source Pack for Common Ground v2


---

## 0. How to use this pack (senior researcher protocol)

1. **Verify every entry.** Entries tagged `[✓ web-verified]` were confirmed to exist via web search on 2026-11-13 (title, authors, venue). Re-verify anyway and correct any detail (year, page numbers, venue). Entries tagged `[classic, verify]` are canonical works cited from memory: confirm the exact bibliographic data before citing them in `THEORY.md`.
2. **Never invent citations.** If you add a source, you must have read it or verified its existence in this session. If you are unsure, write `[unverified]` next to it and resolve it before Phase R ends.
3. **Read the annotation before the paper.** Each entry says what it is for. Phase R is about answering the six research questions, not about reading everything.
4. **Push further.** Each theme ends with what is missing. Your job is to fill those gaps with better or newer sources, and to contradict this pack where the literature disagrees with our design (§4 of the build brief).
5. **Priority tags:** `[M]` must read in full, `[S]` skim (abstract, intro, conclusions), `[R]` reference only (consult when a specific question arises).

The six research questions from the build brief (Phase R):
- **RQ1.** What is the formal definition of "axiom system" we commit to, and what does sufficiency mean (weakest sufficient conditions)?
- **RQ2.** Is reconstructing someone's axioms from text scientifically plausible, and what is the precedent (enthymemes, warrants, belief inference)?
- **RQ3.** Why is parsimony the right selection principle, and how should the cost function be justified (weighted abduction, MDL)?
- **RQ4.** What psychology says disagreements trace back to divergent values (moral foundations, sacred values, belief systems)?
- **RQ5.** What are the failure modes we must design against (motivated reasoning, belief bias, LLM value priors)?
- **RQ6.** How do we evaluate: what corpora and benchmarks exist, and what can we claim honestly?

---

## Theme A. Enthymemes, warrants, and implicit premises: the precedent for axiom reconstruction `[answers RQ2]`

**A1. Toulmin, S. (1958). *The Uses of Argument*. Cambridge University Press.** `[classic, verify]` `[M]`
The original claim that every argument rests on a **warrant**: an unstated link that licenses the step from data to claim, backed by deeper **backing**. This is the intellectual ancestor of the entire project: what we call an "axiom" is close to Toulmin's backing, made explicit and formalized.
→ *Design implication:* our reconstructed axioms are warrants/backings generalized to a whole corpus of one speaker. The UI should show the warrant chain: quote, warrant (proposed axiom), formalization, verification status.

**A2. Walton, D., Reed, C., & Macagno, F. (2008). *Argumentation Schemes*. Cambridge University Press.** `[classic, verify]` `[S]`
A taxonomy of stereotypical patterns of inference, each with its characteristic implicit premises. The de facto standard vocabulary for classifying implicit premises in argument mining.
→ *Design implication:* use scheme names as candidate-axiom generators (e.g., "argument from consequences" generates axioms of the form "if action a has consequence c and c is bad, then a is bad").

**A3. Sviridova, E., Cabrio, E., & Villata, S. (2026). Mining implicit arguments for reasoning: A survey.** SAGE, DOI `10.1177/19462174251344764`; preprint at https://hal.science/hal-05435118 `[✓ web-verified]` `[M]`
The state of the art on enthymemes: detection, reconstruction, and restoration of implicit premises, warrants, and conclusions. Confirms the field's roadmap: argumentation models (Toulmin, Walton) are the tools used for implicit premise reconstruction; Walton's model is used for detection and reconstruction of implicit premises (Rajendran et al.; Chakrabarty et al.), Toulmin's for implicit warrants. This is the single most important paper for our related-work section: it defines what exists so we can position what is new.
→ *Design implication:* novelty claim. Enthymeme reconstruction restores one missing premise for one argument. Nobody reconstructs the *minimal consistent system* behind a whole corpus and verifies it with a theorem prover. That intersection (abductive system reconstruction + formal verification) is our contribution.

**A4. Wagemans, J. et al. Finding the missing link: An algorithmic approach to reconstructing enthymemes. *Argumentation* (2025).** https://link.springer.com/article/10.1007/s10503-025-09682-z `[✓ web-verified]` `[S]`
A systematic, procedural approach to enthymeme reconstruction built on the Periodic Table of Arguments and the Argument Type Identification Procedure. Important because it is *algorithmic*, not just theoretical: a manual procedure that narrows down candidate missing premises by argument form.
→ *Design implication:* candidate axiom generation should follow a typed procedure per argument form, then rank candidates. This supports abduce.py's generate-then-rank design over free-form LLM generation.

**A5. Lawrence, J., & Reed, C. (2020). Argument mining: A survey. *Computational Linguistics*, 45(4), 765-818.** DOI `10.1162/coli_a_00364`, https://direct.mit.edu/coli/article/45/4/765/93362 `[✓ web-verified]` `[S]`
The canonical survey of the argument mining field: component tasks (claim/premise identification, relation classification), corpora, and the gap that matters to us: implicit structure is the hard, unsolved part.
→ *Design implication:* our pipeline inherits the standard decomposition (segment, classify, link) but adds the layers the field lacks: axiom proposal and formal verification.

**A6. Large Language Models in Argument Mining: A Survey (2025).** https://arxiv.org/abs/2506.16383 `[✓ web-verified]` `[S]`
Covers literature to 2025-09-27. Documents the shift from supervised pipelines to LLM-driven approaches and states the open problem we attack: systems are effective on explicit clause-level claims but fail when claims are implied through presupposition, metaphor, or narrative framing; implicit claim phenomena are systematically underrepresented in evaluation.
→ *Design implication:* honest limitations section. Quote this survey when we state that claim extraction from implicit text is unreliable, hence the human review queue.

---

## Theme B. Abduction, weakest sufficient conditions, parsimony: the formal core `[answers RQ1, RQ3]`

**B1. Lin, F. (2001). On strongest necessary and weakest sufficient conditions. *Artificial Intelligence*, 128(1-2), 143-159.** DOI `10.1016/S0004-3702(01)00070-4` `[✓ verified S1 2026-11-13: Crossref + full text read]` `[M]`
> **S1 correction.** Pages were given as 128(2), 249-261. The annotation below overstates the paper (propositional only; no claim that abduction "computes approximations") and its design implication points the wrong way. See `RESEARCH.md` §2.3 and §4.
The formal backbone. Lin defines, for a formula φ: the **strongest necessary condition** (the most information carried by φ that follows from it) and the **weakest sufficient condition** (WSC: the most general property that suffices for φ). Abduction is characterized as computing approximations of these.
→ *Design implication:* this gives our central object a rigorous name. Our axiom system A for a speaker s should *approximate the weakest sufficient condition of s's endorsed claims*: A is sufficient for φ (A ⊨ φ), and as weak/general as the cost function allows. Write this definition in THEORY.md verbatim and cite Lin.

**B2. Hobbs, J., Stickel, M., Appelt, D., & Martin, P. (1993). Interpretation as abduction. *Artificial Intelligence*, 63(1-2), 69-142.** DOI `10.1016/0004-3702(93)90015-4` `[✓ verified S1 2026-11-13: Crossref + §1, §4, §7, §8.3, §9 read]` `[M]`
> **S1 correction.** Pages were given as 319-350. The form of the cost function has this paper as precedent; the value of λ does not, and the authors call their own numbers ad hoc. See `RESEARCH.md` §3.
Weighted abduction: interpreting text means finding the lowest-cost explanation, where each assumed fact carries a cost and each used rule carries a weight. The direct ancestor of our cost function.
→ *Design implication:* our `cost(A) = Σ_a (1 − plausibility(a)) + λ·|A|` is weighted abduction with plausibility as the complement of assumption cost, plus a size penalty. Justify λ (≈0.3) as the standard abduction/MDL trade-off between explanation quality and system size; consider calibrating it on the golden corpus rather than fixing it a priori.

**B3. Alchourrón, C., Gärdenfors, D., & Makinson, D. (1985). On the logic of theory change. *Journal of Symbolic Logic*, 50(2), 510-530.** `[classic, verify]` `[R]`
AGM belief revision: how a rational agent's belief set changes when new information arrives (expansion, contraction, revision). Foundational if we ever model how a speaker's axiom system *should* update when confronted with common ground.
→ *Design implication:* Phase 1+ only. If we later add "what would it take for this speaker to accept that claim" (revision operators), AGM is the framework.

**B4. Nebel, B. (1991). Belief revision and default reasoning. *Artificial Intelligence*, 35(2), 203-220.** `[classic, verify]` `[R]`
Revision when beliefs are represented as finite bases rather than logically closed sets. Closer to our setting: we work with a finite axiom base A, not a deductive closure.
→ *Design implication:* base revision justifies representing speakers by a finite axiom list instead of a closure; cite when defining our data model.

**B5. Rissanen, J. (1978). Modeling by shortest data description. *Automatica*, 14(5), 465-471.** DOI `10.1016/0005-1098(78)90005-5` `[✓ bibliographic data verified S1 2026-11-13: Crossref; content not read, MDL read in Grünwald 2004]` `[R]`
Minimum Description Length: the best theory is the one that compresses the data with the shortest total description (theory + residuals). The information-theoretic twin of parsimony.
→ *Design implication:* alternative justification for the λ·|A| term; THEORY.md should mention both weighted-abduction and MDL as converging justifications of the same cost function.

---

## Theme C. Engineering precedents: pinpointing, minimal unsatisfiability, diagnosis `[answers RQ1, RQ4 partially]`

**C1. Baader, F., & Suntisrivaraporn, B. (2008). Debugging SNOMED CT using axiom pinpointing in the description logic EL+.** Proc. KRMED 2008, CEUR-WS. `[✓ existence web-verified]` `[S]`
Axiom pinpointing in a real, deployed medical ontology: given an entailment, compute the minimal subset of axioms responsible. The term "pinpointing" was coined by Schlobach & Cornet (2003) `[classic, verify]`; survey in Peñaloza, R., *Explaining axiom pinpointing in description logics* `[classic, verify]` `[R]`.
→ *Design implication:* when a speaker's claims are inconsistent, pinpointing is how we find the *root axioms responsible*, rather than blaming a random surface claim. This is the precedent for our "root-axiom divergence" output.

**C2. Liffiton, M., & Sakallah, K. (2008). Algorithms for computing minimal unsatisfiable subsets of constraints. *Journal of Automated Reasoning*, 40(1), 1-33.** DOI `10.1007/s10817-007-9084-z` (online 2007) `[✓ verified S1 2026-11-13: Crossref + §1-6, §7.2, §9, §10 read]` `[M]`
> **S1 correction.** This paper is CAMUS, not MARCO. MARCO, which `argmap.py` implements, is Liffiton, Previti, Malik & Marques-Silva (2016), *Constraints* 21(2), 223-250, DOI `10.1007/s10601-015-9183-0`. Cite the 2008 paper for the MUS/MCS definitions and the hitting-set duality only. See `RESEARCH.md` §1 and §4.
The MARCO family of algorithms for computing MUSes (minimal unsatisfiable subsets) and MCSes. Our `argmap.py` already implements MARCO.
→ *Design implication:* our reduced-disagreement feature (find the minimal set of mutually incompatible endorsed claims) is an MUS computation over the union of the camps' axiom systems. Cite this as the algorithmic basis; also note the "MUS relaxation" explanation style for users.

**C3. Reiter, R. (1987). A theory of diagnosis from first principles. *Artificial Intelligence*, 32(1), 1-32.** `[classic, verify]` `[R]`
Model-based diagnosis: given a system and an observation that contradicts it, compute the minimal sets of components whose faultiness explains the inconsistency. Structurally identical to our problem: given axioms and a rejected claim, compute the minimal axiom sets whose *absence or difference* explains the rejection.
→ *Design implication:* cite when defining "explanation of disagreement": a disagreement is explained by a minimal differing axiom set (a hitting-set problem over the two camps' axiom systems).

---

## Theme D. Belief systems: what people actually have `[answers RQ2, RQ4]`

**D1. Converse, P. (1964). The nature of belief systems in mass publics.** In D. Apter (ed.), *Ideology and Discontent*. Free Press. Republished in *Critical Review* 18(1-3): https://www.tandfonline.com/doi/pdf/10.1080/08913810608443650 `[✓ web-verified]` `[M]`
The founding result of political psychology. A belief system is "a configuration of ideas and attitudes in which the elements are bound together by some form of constraint or functional interdependence." Crucially, Converse found that *mass publics* show little constraint: most people's political beliefs do not form a tight logical system; only elites approximate ideological structure.
→ *Design implication (double-edged):* (a) Converse legitimates the concept of constraint between beliefs, which is what our entailment checks exploit; (b) but he also warns that for most people, a *perfectly consistent* axiom system will not exist. This is why the design already separates firm rejections (verified non-entailment) from soft ones, and why we report the *best systematization* of a corpus, never claim to have found "the person's actual beliefs". THEORY.md must confront Converse explicitly; the two-layer language ("sufficient to explain", not "what they believe") is the correct response and must be justified here.

**D2. A benchmark for zero-shot belief inference in large language models (2025).** https://arxiv.org/abs/2511.18616 `[✓ web-verified]` `[S]`
Evaluates how well LLMs predict individuals' beliefs across topics from text and context. Finds real capacity and real limits; provides a reproducible benchmark for LLM emulation of human belief reasoning.
→ *Design implication:* empirical precedent that inferring beliefs from text with an LLM is a measurable, bounded task. Justifies our abduce.py step while its documented limits justify our verification layer and uncertainty reporting.

**D3. Ma, A., & Powell, D. et al. Evaluating large language models for belief inference. *Findings of EMNLP 2025*, pp. 20787-20795.** https://aclanthology.org/2025.findings-emnlp.1132/ `[✓ web-verified]` `[S]`
Systematic evaluation of LLM belief inference capabilities.
→ *Design implication:* cite alongside D2 when reporting how much trust the LLM proposal layer has earned; use their evaluation methodology ideas for our own abduce.py validation (Phase 8).

**D4. SemEval-2026 Task 11: Disentangling reasoning from belief.** Task overview and system descriptions: https://aclanthology.org/2026.semeval-1.65/ (RvH-40 system paper: symbolic abstraction to remove belief bias) `[✓ web-verified]` `[S]`
Shared task on the finding that LLMs (like humans) suffer **belief bias**: semantic world knowledge overrides formal logical structure in syllogistic reasoning. The winning approaches use symbolic abstraction: strip content, keep logical form, reason on the form.
→ *Design implication (critical):* this is the strongest empirical argument for our two-layer architecture. The LLM proposes; a symbolic layer (Z3, then Lean for the certified tier) decides entailment. Never let the LLM be the judge of its own proposed axiom systems. It also suggests a concrete technique: when verifying, abstract away predicate names to prevent content bias from leaking into verdicts.

---

## Theme E. Values as axioms: the psychology of foundational disagreement `[answers RQ4]`

**E1. Graham, J., Haidt, J., & Nosek, B. (2009). Liberals and conservatives rely on different sets of moral foundations. *Journal of Personality and Social Psychology*, 96(5), 1029-1046.** DOI `10.1037/a0015141` `[✓ web-verified]` `[M]`
Moral Foundations Theory made empirical: across four studies, political left and right differ *predictably* in which moral foundations they use (harm/care and fairness/reciprocity vs. the full five including loyalty, authority, purity). Moral texts (sermons) literally use different foundation vocabulary.
→ *Design implication:* the psychological warrant for our central claim that surface disagreements trace to *foundational* differences: disagreements are often two different prioritarian axiom sets, not different facts. Our golden CO2 corpus should be annotatable by foundation: the Yes camp's axioms (responsibility, harm to nature) vs. the No camp's (fairness of cost, efficacy/efficiency).

**E2. Schwartz, S. (1992). Universals in the content and structure of values. *Advances in Experimental Social Psychology*, 25, 1-65.** `[classic, verify]` `[S]`
Ten basic human values with a circumplex structure (opposing motivations, e.g., self-direction vs. conformity). Cross-culturally validated across dozens of countries.
→ *Design implication:* an off-the-shelf, validated value vocabulary for the axiom candidate generator. Rather than free-form axioms only, abduce.py can propose "value-prior axioms" (e.g., "preserving nature takes priority over short-term economic cost" as a self-transcendence value axiom) and tag them with Schwartz categories, which makes outputs comparable across speakers.

**E3. Tetlock, P., Kristel, O., Elson, S., Green, M., & Lerner, J. (2000). The psychology of the unthinkable: Taboo trade-offs, forbidden base rates, and heretical counterfactuals. *Journal of Personality and Social Psychology*, 78(5), 853-870.** DOI `10.1037/0022-3514.78.5.853` `[✓ web-verified]` `[M]`
Sacred values: people protect certain values from mere cost-benefit trade-offs, and respond to trade-off framing with moral outrage and moral cleansing. Monetizing a sacred value is "unthinkable".
→ *Design implication (important):* sacred-value structure explains a class of *apparent* irrationality in debates (a camp refusing an "obviously favorable" utilitarian deal). In the cost function, axioms flagged as sacred should arguably be non-discountable (plausibility not up for trade-off). At minimum, the UI must never present sacred values as "biased assumptions"; that is a product-level ethical requirement, and THEORY.md should cite Tetlock for why.

**E4. Yuan, C., Ma, B., Zhang, Z., Prenkaj, B., Kreuter, F., & Kasneci, G. (2026). Moral lenses, political coordinates: Towards ideological positioning of morally conditioned LLMs. *Proceedings of EMNLP 2026*, pp. 5950-5984.** https://aclanthology.org/2026.emnlp-main.262/ `[✓ web-verified]` `[S]`
Recent work placing LLM moral/political behavior within Moral Foundations Theory, building on Abdulhai et al. (2024), *Moral foundations of large language models*, EMNLP `[✓ existence verified via citation, fetch]`.
→ *Design implication:* methodology reference for probing which value priors an LLM brings, which we need for calibrating our own proposal layer.

**E5. Tracing moral foundations in large language models (2026).** https://arxiv.org/abs/2601.05437 `[✓ web-verified]` `[S]`
Documents LLM moral judgment pathologies: "moral hypocrisy" (gap between abstract principles and concrete judgments), "moral mimicry" (justifications adapt to the prompter's perceived identity), and WEIRD (Western, Educated, Industrialized, Rich, Democratic) value skew persisting even in multilingual settings.
→ *Design implication (critical):* the plausibility(a) prior in cost(A) comes from an LLM, and this literature says LLM value judgments are biased and unstable. Design responses: (1) plausibility scores must be presented as *proposed priors* with textual evidence, never as measurements of the person; (2) run the proposal layer with a calibrated, documented model and record model identity in outputs; (3) the human review queue is mandatory for any axiom tagged as value-laden; (4) consider reporting plausibility intervals or multi-sample agreement rather than point scores.

---

## Theme F. Failure modes and honest limits `[answers RQ5]`

**F1. Festinger, L. (1957). *A Theory of Cognitive Dissonance*. Stanford University Press.** `[classic, verify]` `[R]`
People experience inconsistency between beliefs/behavior as aversive and reduce it by changing beliefs or rationalizing.
→ *Design implication:* explains why real corpora sometimes *will* show inconsistency the speaker does not acknowledge; our system must surface it gently (dispute suspension, not "you are contradictory" verdicts).

**F2. Kunda, Z. (1990). The case for motivated reasoning. *Journal of Personality and Social Psychology*, 53(5), 636-647.** `[classic, verify]` `[S]`
Reasoning is goal-driven: people "can" reason to desired conclusions while feeling objective. Mechanism: biased memory access, credulous evaluation of congenial evidence.
→ *Design implication:* expected artifact: axiom systems reconstructed from motivated text may be *post-hoc rationalizations*, not true generative axioms. THEORY.md must carry this caveat verbatim: we reconstruct the system that best explains the text; the speaker's operative psychology may differ.

**F3. Lord, C., Ross, L., & Lepper, M. (1979). Biased assimilation and attitude polarization. *Journal of Personality and Social Psychology*, 37(11), 2098-2109.** `[classic, verify]` `[R]`
When shown mixed evidence, opposing camps polarize: same evidence, different assimilation.
→ *Design implication:* a warning for our evaluation: do not expect common-ground presentation to reduce disagreement mechanically; measure effects modestly (if at all) and never market the tool as a depolarization machine.

**F4. The LLM belief-bias evidence in D4 (SemEval-2026 Task 11) and the LLM value-prior evidence in E5 belong to this theme too.** The design's defenses: symbolic verification (D4), evidence-grounded proposals with review queue (E5), two-layer language rules (the brief §5).

---

## Theme G. Evaluation precedents and corpora `[answers RQ6]`

**G1. Wachsmuth, H., et al. (2017). Building an argument search engine for the web (args.me).** `[classic, verify, find venue: COMMA 2017]` `[S]`
Large-scale argument corpus (384,527 arguments from debate portals) and search engine; the standard resource of the field.
→ *Design implication:* candidate external corpus if the Swiss votation golden set proves too small; but note it lacks axiom-level annotations (nothing does; that is why we must build our own golden corpus in Phase 7).

**G2. FOLIO benchmark** (already referenced in `formalize.py` with empty rows and Wilson intervals). `[in-repo, verify the canonical citation: Han et al., 2024?)` `[R]`
First-order logic reasoning over text. Our existing benchmark harness already reports Wilson intervals and McNemar tests; keep that statistical discipline.
→ *Design implication:* the Phase 7 golden corpus evaluation should reuse the same statistical apparatus (Wilson intervals on per-axiom accuracy, McNemar when comparing two formalizers), so numbers stay comparable across versions.

**G3. Proceedings of the 12th Argument Mining Workshop (ArgMining @ ACL 2025).** https://aclanthology.org/volumes/2025.argmining-1/ `[✓ web-verified]` `[S]`
Where this community publishes evaluation methods now; scan for implicit-premise and LLM-evaluation protocols we can borrow for Phase 8.

**G4. Swiss votation materials (swissvotes.ch, vote 644, CO2 law, June 2021).** Primary sources: official voting booklets, campaign texts. `[to collect in Phase 7]`
Our golden corpus: camps with authentic public argumentation, known outcome, bilingual (FR/DE), and a policy domain where value divergence is documented. Human-annotate a subset (Younes + at least one other annotator; report inter-annotator agreement, e.g., Cohen's kappa) to measure abduce.py's per-axiom precision/recall against the annotation.

---

## H. Hypotheses this pack licenses (write these into THEORY.md, each with citations)

1. **H1 (reconstruction precedent).** Reconstructing unstated premises from argumentative text is an established, measurable task (enthymeme reconstruction), and our system generalizes it: from single missing premises to the minimal sufficient axiom system of a corpus. (A1, A3, A4)
2. **H2 (formal core).** A speaker's axiom system A is an approximation of the weakest sufficient condition of their endorsed claims: A ⊨ φ for each endorsed φ, minimized by a cost function. (B1, B2, B5)
3. **H3 (parsimony).** Selecting among candidate systems by cost (plausibility-weighted, size-penalized) is weighted abduction, with MDL as converging justification; λ trades generality against economy. (B2, B5)
4. **H4 (disagreement localization).** When two camps disagree, the disagreement can be *localized* to minimal differing axiom subsets, using the same algorithms as ontology debugging (pinpointing, MUS, hitting-set diagnosis). (C1, C2, C3)
5. **H5 (values as axioms).** A substantial share of foundational disagreement is value divergence: predictable, structured, and partly language-visible (moral foundations, basic values, sacred values). This licenses value-tagged axiom proposals. (E1, E2, E3)
6. **H6 (humans are not logicians).** Expect imperfect consistency in real corpora; report best systematization with firm/soft distinctions; never assert discovered "true beliefs". (D1, F1, F2)
7. **H7 (LLMs need symbolic checks).** Both LLMs and humans exhibit belief bias: world knowledge overrides logical form. Entailment must be decided by symbolic verification, not by the proposing model. (D4)
8. **H8 (LLM value priors are biased).** LLM moral/value judgments show hypocrisy, mimicry, and WEIRD skew; plausibility priors must be evidence-grounded, model-attributed, human-reviewable, and ideally interval-valued. (E4, E5)
9. **H9 (evaluation honesty).** No benchmark exists for axiom-system reconstruction; we must build one (golden corpus with human annotations, Wilson intervals, McNemar comparisons), borrow statistical discipline from our FOLIO harness, and publish limitations. (A6, G1, G2, G4)

## I. Open questions pushed to you, the senior researcher

1. **Converse tension.** How far can we lean on "constraint" given Converse's finding that mass-public belief systems are loose? Should our output include a *systematization score* (how much of the corpus the best A actually entails)? Consider a coverage metric with the same statistical treatment as the FOLIO harness.
2. **Sacred values in the cost function.** Should axioms tagged sacred be non-discountable in cost(A), and how would we detect sacredness from text without mind-reading claims? (E3 suggests detection signals: absolutist language, outrage at trade-off framing.)
3. **Novelty positioning.** Verify that no published system combines enthymeme reconstruction with formal verification over whole corpora; search 2025-2026 venues (ArgMining, COMMA, ACL, AAAI) for close work. This determines the claim we can make in THEORY.md and the README.
4. **λ calibration.** Is there an accepted way to set the size penalty in weighted abduction or MDL for this task, or should λ be fit on the golden corpus and reported with sensitivity analysis? Propose the protocol.
5. **Plausibility elicitation.** Design the protocol for scoring plausibility(a): which model, which prompt, single-score vs. Likert, multi-sample agreement, and how evidence quotes are attached. Address E5's WEIRD-bias critique directly.
6. **Firm vs. soft rejections.** Ground the threshold and language for "firm" (prover says no) vs. "soft" (unproven) in the verification literature. What exactly can a NO verdict from Z3/Lean license us to say in the UI? Draft the precise UI phrasing.
7. **Missing themes you should add:** (a) argument quality / fallacy literature if relevant to filtering noise; (b) computational models of ideology scaling (e.g., scaling with legislator data) if useful for cross-camp geometry; (c) any Swiss deliberation / votation research literature for the golden corpus domain; (d) recent work on LLM-generated structured beliefs (worldview extraction) not captured here.

## J. Suggested reading order for Phase R (budgeted, Fable Pro plan)

Session 1 (formal core, must): B1 (Lin 2001), B2 (Hobbs 1993), C2 (Liffiton & Sakallah), then draft RQ1/RQ3 answers.
Session 2 (reconstruction precedent): A3 (Sviridova survey) first, then A4, A1 skim; answer RQ2; verify all `[classic, verify]` tags in Themes A, B, C.
Session 3 (psychology): D1 (Converse), E1 (Graham), E3 (Tetlock), E5; answer RQ4, RQ5; draft H6, H8.
Session 4 (evaluation): A6, D2, D3, G3 skim; answer RQ6; define the Phase 7 golden-corpus annotation protocol; write THEORY.md; flag every remaining `[unverified]`.

## K. Verification log

- **Session 1, 2026-11-13.** B1, B2, B5 and C2 checked and corrected in place above. Two entries tagged "web-verified" (B1, C2) carried errors, so that tag is not to be relied on in later sessions. Findings, the RQ1 and RQ3 drafts, and the sources added for Themes B and C are in [`RESEARCH.md`](RESEARCH.md); the draft definitions are in [`THEORY.md`](THEORY.md). The note under D1 and question I.6 conflate firm/soft rejection with proved/unproved; see `RESEARCH.md` §2.5.