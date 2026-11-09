import { leanProofs, negativeControl } from "../contracts/lean";
import { verificationSnapshots } from "./verification-snapshots";

function withVerification<T extends { id: string; status: "unverified" }>(proof: T) {
  const { verifiedAt, ...certificate } = verificationSnapshots[proof.id];
  return { ...proof, ...certificate, verifiedAt: new Date(verifiedAt) };
}

export const DEBATE_ID = "plastic-bag-policy";

export const debateSeed = {
  id: DEBATE_ID,
  title: "The plastic bag policy debate",
  question: "Should a city adopt a well-designed single-use plastic bag policy?",
  summary:
    "A source-grounded reconstruction of a public pro/con debate. The targeted-policy advocate emphasizes measured reductions in bag use and shoreline litter; the upstream-first critic emphasizes production limits and the life-cycle costs of substitutes.",
  sourceName: "Britannica ProCon — Single-Use Plastics Debate",
  sourceUrl: "https://www.britannica.com/procon/single-use-plastics-debate",
  methodNote:
    "This is an editorial formal reconstruction, not a verbatim transcript or a claim that the named sources endorse every formal premise. ‘Advocate’ and ‘Upstream-first critic’ are roles distilled from the public pro/con collection. Lean checks conditional deductions only; evidence and values remain open to challenge.",
};

export const evidenceSeed = [
  {
    id: "E0",
    debateId: DEBATE_ID,
    title: "Single-Use Plastics: Pros, Cons, Debate",
    authors: "Britannica ProCon editors and quoted contributors",
    publisher: "Encyclopaedia Britannica",
    publishedAt: "Accessed 7 Nov 2026",
    url: "https://www.britannica.com/procon/single-use-plastics-debate",
    sourceType: "debate_collection" as const,
    excerpt:
      "So, are single-use plastic bans the most effective policy to reduce plastic consumption and pollution?",
    finding:
      "Provides the public pro/con structure from which the two positions in this demonstration are reconstructed.",
    limitation:
      "An editorial collection, not a two-person transcript. The application’s formal statements are interpretive reconstructions and should not be attributed verbatim to contributors.",
    reviewStatus: "reviewed" as const,
  },
  {
    id: "E1",
    debateId: DEBATE_ID,
    title: "Plastic bag bans and fees reduce harmful bag litter on shorelines",
    authors: "Anna Papp and Kimberly L. Oremus",
    publisher: "Science",
    publishedAt: "19 Jun 2025",
    url: "https://www.science.org/doi/10.1126/science.adp9274",
    sourceType: "peer_reviewed" as const,
    excerpt:
      "We find that plastic bag policies lead to a 25 to 47% decrease in plastic bags as a share of total items collected at cleanups relative to areas without policies.",
    finding:
      "Using data from 45,067 US shoreline cleanups, the study estimates a relative reduction in bags as a share of collected litter after bag bans or fees.",
    limitation:
      "The outcome is bags’ relative share of cleanup items, not proof that all plastic pollution declines. Policies limit rather than eliminate shoreline bag debris; US results do not automatically generalize everywhere.",
    reviewStatus: "reviewed" as const,
  },
  {
    id: "E2",
    debateId: DEBATE_ID,
    title: "Plastic Bag Bans Work",
    authors: "Celeste Meiffren-Swango, Jenn Engstrom, and Louis Sokolow",
    publisher: "Environment America Research & Policy Center",
    publishedAt: "17 Jan 2024",
    url: "https://environmentamerica.org/center/resources/plastic-bag-bans-work/",
    sourceType: "advocacy_report" as const,
    excerpt:
      "Bans in five states and cities that cover more than 12 million people combined have cut single-use plastic bag consumption by about 6 billion bags per year.",
    finding:
      "The report aggregates results from five jurisdictions and estimates that a similar well-designed ban could avoid roughly 300 bags per person per year.",
    limitation:
      "An advocacy-authored report covering selected jurisdictions. The per-person figure is an estimate for similar policies, not a guaranteed local outcome.",
    reviewStatus: "reviewed" as const,
  },
  {
    id: "E3",
    debateId: DEBATE_ID,
    title: "Life Cycle Assessment of grocery carrier bags",
    authors: "Valentina Bisinella, Paola Federica Albizzati, Thomas Fruergaard Astrup, and Anders Damgaard",
    publisher: "Danish Environmental Protection Agency / DTU Environment",
    publishedAt: "Feb 2018",
    url: "https://www2.mst.dk/udgiv/publications/2018/02/978-87-93614-73-4.pdf",
    sourceType: "government_report" as const,
    excerpt:
      "For all carrier bags, reuse as many times as possible before disposal is strongly encouraged.",
    finding:
      "Required reuse varies sharply by material, design, disposal scenario, and environmental indicator; substitutes cannot be assumed impact-free.",
    limitation:
      "The study examines bags available in Danish supermarkets in 2017. It excludes littering effects, behavioral change, and retailer economic impacts; its large reuse thresholds depend strongly on indicators and assumptions.",
    reviewStatus: "reviewed" as const,
  },
  {
    id: "E4",
    debateId: DEBATE_ID,
    title: "To stop plastic pollution, we must stop plastic production, scientists say",
    authors: "Mongabay; quotes Melanie Bergmann and other researchers",
    publisher: "Mongabay",
    publishedAt: "28 Apr 2022",
    url: "https://news.mongabay.com/2022/04/to-stop-plastic-pollution-we-must-stop-plastic-production-scientists-say/",
    sourceType: "news_analysis" as const,
    excerpt:
      "Only upstream measures such as a cap on plastic production will prevent further degradation of our life-supporting ecosystems.",
    finding:
      "Presents the upstream-first argument that consumer-side measures are insufficient while virgin plastic production continues to grow.",
    limitation:
      "The quoted statement is an expert’s policy argument reported by a news outlet, not a direct estimate of the effect of a particular production-cap design.",
    reviewStatus: "reviewed" as const,
  },
];

export const statementSeed = [
  {
    id: "D1",
    debateId: DEBATE_ID,
    owner: "shared" as const,
    kind: "definition" as const,
    title: "Shared vocabulary",
    body:
      "A targeted bag policy means a well-designed ban or fee on single-use checkout bags. A responsible design avoids a simple switch to another disposable material and considers access and substitute-bag impacts.",
    formalText: "(vocabulary only: introduces ResponsibleDesign and asserts nothing)",
    formalizationNote:
      "An editorial definition synthesized from the sourced debate and life-cycle caveats. It deliberately narrows the question away from an unqualified ban on every plastic item. It carries no formal premise: whether the proposed policy is responsibly designed is claim A3.",
    evidenceId: "E0",
    sortOrder: 1,
    isWorkshop: false,
  },
  {
    id: "A1",
    debateId: DEBATE_ID,
    owner: "advocate" as const,
    kind: "empirical" as const,
    title: "Bag use falls",
    body: "Well-designed targeted bag policies reduce single-use plastic bag consumption.",
    formalText: "Achieves Policy.targetedBagPolicy Effect.reducesBagUse",
    formalizationNote:
      "The general claim is treated as a premise conditional on accepting the report’s selected-jurisdiction evidence and similar-policy assumption.",
    evidenceId: "E2",
    sortOrder: 2,
    isWorkshop: false,
  },
  {
    id: "A2",
    debateId: DEBATE_ID,
    owner: "advocate" as const,
    kind: "empirical" as const,
    title: "Shoreline bag litter falls",
    body:
      "Bag bans and fees reduce bags’ share of shoreline cleanup litter relative to comparable areas without policies.",
    formalText:
      "Achieves Policy.targetedBagPolicy Effect.reducesShorelineBagLitter",
    formalizationNote:
      "The formal atom abbreviates the study’s relative, population-level result; it does not encode the 25–47% estimate or every causal assumption.",
    evidenceId: "E1",
    sortOrder: 3,
    isWorkshop: false,
  },
  {
    id: "A3",
    debateId: DEBATE_ID,
    owner: "advocate" as const,
    kind: "design" as const,
    title: "Responsible design is required",
    body:
      "The proposed policy protects essential access and accounts for the life-cycle impacts of alternative bags.",
    formalText: "ResponsibleDesign Policy.targetedBagPolicy",
    formalizationNote:
      "This is a design requirement accepted for the demonstration, not an empirical claim that every existing ban satisfies it.",
    evidenceId: "E3",
    sortOrder: 4,
    isWorkshop: false,
  },
  {
    id: "A4",
    debateId: DEBATE_ID,
    owner: "advocate" as const,
    kind: "normative" as const,
    title: "The advocate’s adoption rule",
    body:
      "If a policy reduces bag use and shoreline bag litter, and its design is responsible, then the city should adopt it.",
    formalText:
      "∀ p, Achieves p Effect.reducesBagUse → Achieves p Effect.reducesShorelineBagLitter → ResponsibleDesign p → ShouldAdopt p",
    formalizationNote:
      "A normative rule, not a scientific finding. It encodes the advocate’s willingness to trade off other concerns once these three conditions hold.",
    evidenceId: "E0",
    sortOrder: 5,
    isWorkshop: false,
  },
  {
    id: "C1",
    debateId: DEBATE_ID,
    owner: "critic" as const,
    kind: "empirical" as const,
    title: "A bag policy is not a complete solution",
    body: "A targeted bag policy alone does not solve plastic pollution as a whole.",
    formalText: "¬ SolvesPlasticPollutionAlone Policy.targetedBagPolicy",
    formalizationNote:
      "This is a scope limitation, not a negation of A2. A policy can reduce shoreline bag litter while leaving the wider pollution problem unresolved.",
    evidenceId: "E1",
    sortOrder: 6,
    isWorkshop: false,
  },
  {
    id: "C2",
    debateId: DEBATE_ID,
    owner: "critic" as const,
    kind: "empirical" as const,
    title: "Production caps address the upstream source",
    body: "Production-cap policies directly address virgin plastic production.",
    formalText: "Achieves Policy.productionCaps Effect.addressesVirginProduction",
    formalizationNote:
      "Encodes the upstream-first argument at a high level. It does not assert a specific cap’s magnitude, feasibility, or distributional effect.",
    evidenceId: "E4",
    sortOrder: 7,
    isWorkshop: false,
  },
  {
    id: "C3",
    debateId: DEBATE_ID,
    owner: "critic" as const,
    kind: "design" as const,
    title: "Substitute bags need reuse accounting",
    body:
      "Reusable alternatives must be evaluated by material, actual reuse, and full life-cycle impacts rather than assumed to be automatically superior.",
    formalText: "RequiresReuseAccounting Policy.targetedBagPolicy",
    formalizationNote:
      "A design constraint drawn from the Danish assessment. It is intentionally not used as a hidden premise in the adoption proof.",
    evidenceId: "E3",
    sortOrder: 8,
    isWorkshop: false,
  },
  {
    id: "C4",
    debateId: DEBATE_ID,
    owner: "critic" as const,
    kind: "normative" as const,
    title: "The critic’s priority rule",
    body: "If a policy directly addresses virgin plastic production, give it priority.",
    formalText:
      "∀ p, Achieves p Effect.addressesVirginProduction → ShouldPrioritize p",
    formalizationNote:
      "A normative priority rule. It does not logically imply that targeted bag policies should be rejected.",
    evidenceId: "E0",
    sortOrder: 9,
    isWorkshop: false,
  },
  {
    id: "S1",
    debateId: DEBATE_ID,
    owner: "shared" as const,
    kind: "normative" as const,
    title: "Shared environmental goal",
    body: "The city should reduce plastic pollution.",
    formalText: "ShouldReducePlasticPollution",
    formalizationNote:
      "A deliberately modest common-ground premise shared by both reconstructed positions.",
    evidenceId: "E0",
    sortOrder: 10,
    isWorkshop: false,
  },
  {
    id: "B1",
    debateId: DEBATE_ID,
    owner: "shared" as const,
    kind: "bridge" as const,
    title: "Facilitator’s combination bridge",
    body:
      "If the city should adopt the targeted policy and should prioritize production caps, then it should consider a combined policy package.",
    formalText:
      "ShouldAdopt Policy.targetedBagPolicy → ShouldPrioritize Policy.productionCaps → ShouldConsider Policy.combinedPackage",
    formalizationNote:
      "Workshop-created and accepted for this demo. It is not imported from a source. Revoke it to see the combined conclusion lose active certification.",
    evidenceId: null,
    sortOrder: 11,
    isWorkshop: true,
  },
  {
    id: "X1",
    debateId: DEBATE_ID,
    owner: "advocate" as const,
    kind: "conclusion" as const,
    title: "Advocate’s conclusion",
    body: "The city should adopt the well-designed targeted bag policy.",
    formalText: "ShouldAdopt Policy.targetedBagPolicy",
    formalizationNote: "Derived by proof-advocate; never treated as an imported fact.",
    evidenceId: null,
    sortOrder: 12,
    isWorkshop: false,
  },
  {
    id: "X2",
    debateId: DEBATE_ID,
    owner: "critic" as const,
    kind: "conclusion" as const,
    title: "Critic’s conclusion",
    body: "The city should prioritize plastic production caps.",
    formalText: "ShouldPrioritize Policy.productionCaps",
    formalizationNote: "Derived by proof-critic; compatible with X1 unless an additional conflict premise is added.",
    evidenceId: null,
    sortOrder: 13,
    isWorkshop: false,
  },
  {
    id: "X3",
    debateId: DEBATE_ID,
    owner: "shared" as const,
    kind: "conclusion" as const,
    title: "Bounded common ground",
    body:
      "Targeted policies reduce shoreline bag litter, do not solve all plastic pollution alone, and serve a shared pollution-reduction goal.",
    formalText:
      "Achieves Policy.targetedBagPolicy Effect.reducesShorelineBagLitter ∧ ¬ SolvesPlasticPollutionAlone Policy.targetedBagPolicy ∧ ShouldReducePlasticPollution",
    formalizationNote: "Derived by proof-shared.",
    evidenceId: null,
    sortOrder: 14,
    isWorkshop: false,
  },
  {
    id: "X4",
    debateId: DEBATE_ID,
    owner: "shared" as const,
    kind: "conclusion" as const,
    title: "Conditional combined package",
    body: "The city should consider a package combining the targeted bag policy and production caps.",
    formalText: "ShouldConsider Policy.combinedPackage",
    formalizationNote: "Derived by proof-combined and explicitly dependent on facilitator bridge B1.",
    evidenceId: null,
    sortOrder: 15,
    isWorkshop: false,
  },
];

export const proofSeed = [
  ...leanProofs.map((proof) => withVerification({
    id: proof.id,
    debateId: DEBATE_ID,
    theoremName: proof.theoremName,
    title: proof.title,
    conclusionId: proof.conclusionId,
    owner: proof.owner,
    description: proof.description,
    premiseIds: proof.premiseIds,
    leanCode: proof.code,
    status: "unverified" as const,
    isNegativeControl: false,
  })),
  withVerification({
    id: negativeControl.id,
    debateId: DEBATE_ID,
    theoremName: negativeControl.theoremName,
    title: negativeControl.title,
    conclusionId: "C1",
    owner: "shared" as const,
    description: negativeControl.description,
    premiseIds: ["A2"],
    leanCode: negativeControl.code,
    status: "unverified" as const,
    isNegativeControl: true,
  }),
];


/**
 * Corrections to rows that an existing database may already hold. Seeding never
 * overwrites a row, so a fix to the seed needs an explicit, guarded update: each
 * entry applies only while the stored value is still exactly the old one.
 */
export const seedCorrections = {
  evidenceExcerpt: [
    {
      id: "E0",
      // The stored text was not the page's wording.
      from: "So, are single-use plastic bans the most effective way to reduce plastic consumption and pollution? Explore the debate below.",
      to: "So, are single-use plastic bans the most effective policy to reduce plastic consumption and pollution?",
    },
  ],
  evidencePublishedAt: [{ id: "E4", from: "29 Apr 2022", to: "28 Apr 2022" }],
  statementFormalText: [
    {
      id: "D1",
      // A definition had been given the same formula as premise A3, so A3 had a silent duplicate.
      from: "ResponsibleDesign Policy.targetedBagPolicy",
      to: "(vocabulary only: introduces ResponsibleDesign and asserts nothing)",
    },
  ],
};
