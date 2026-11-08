export const LEAN_TOOLCHAIN = "Lean 4.35.0";

export const LEAN_PRELUDE = `namespace CommonGround

inductive Policy where
  | targetedBagPolicy
  | productionCaps
  | combinedPackage
  deriving DecidableEq, Repr

inductive Effect where
  | reducesBagUse
  | reducesShorelineBagLitter
  | addressesVirginProduction
  deriving DecidableEq, Repr

section
variable (Achieves : Policy → Effect → Prop)
variable (ResponsibleDesign RequiresReuseAccounting : Policy → Prop)
variable (SolvesPlasticPollutionAlone : Policy → Prop)
variable (ShouldAdopt ShouldPrioritize ShouldConsider : Policy → Prop)
variable (ShouldReducePlasticPollution : Prop)
`;

export interface LeanProofSeed {
  id: string;
  theoremName: string;
  title: string;
  conclusionId: string;
  owner: "advocate" | "critic" | "shared";
  description: string;
  premiseIds: string[];
  code: string;
}

export const leanProofs: LeanProofSeed[] = [
  {
    id: "proof-advocate",
    theoremName: "advocate_case",
    title: "The targeted-policy case",
    conclusionId: "X1",
    owner: "advocate",
    description:
      "A well-designed targeted policy follows from the two effectiveness premises, the responsible-design premise, and the advocate’s normative rule.",
    premiseIds: ["A1", "A2", "A3", "A4"],
    code: `theorem advocate_case
    (hUse : Achieves Policy.targetedBagPolicy Effect.reducesBagUse)
    (hLitter : Achieves Policy.targetedBagPolicy Effect.reducesShorelineBagLitter)
    (hDesign : ResponsibleDesign Policy.targetedBagPolicy)
    (hRule : ∀ p, Achieves p Effect.reducesBagUse →
      Achieves p Effect.reducesShorelineBagLitter →
      ResponsibleDesign p → ShouldAdopt p) :
    ShouldAdopt Policy.targetedBagPolicy :=
  hRule Policy.targetedBagPolicy hUse hLitter hDesign
`,
  },
  {
    id: "proof-critic",
    theoremName: "critic_case",
    title: "The upstream-first case",
    conclusionId: "X2",
    owner: "critic",
    description:
      "Prioritizing production caps follows from the upstream-production premise and the critic’s normative priority rule. It does not prove that bag policies are useless.",
    premiseIds: ["C2", "C4"],
    code: `theorem critic_case
    (hProduction : Achieves Policy.productionCaps Effect.addressesVirginProduction)
    (hRule : ∀ p, Achieves p Effect.addressesVirginProduction → ShouldPrioritize p) :
    ShouldPrioritize Policy.productionCaps :=
  hRule Policy.productionCaps hProduction
`,
  },
  {
    id: "proof-shared",
    theoremName: "shared_ground",
    title: "The shared, bounded conclusion",
    conclusionId: "X3",
    owner: "shared",
    description:
      "Both sides can accept that bag litter falls, that a bag policy is not a complete solution, and that plastic pollution should be reduced.",
    premiseIds: ["A2", "C1", "S1"],
    code: `theorem shared_ground
    (hLitter : Achieves Policy.targetedBagPolicy Effect.reducesShorelineBagLitter)
    (hLimit : ¬ SolvesPlasticPollutionAlone Policy.targetedBagPolicy)
    (hGoal : ShouldReducePlasticPollution) :
    Achieves Policy.targetedBagPolicy Effect.reducesShorelineBagLitter ∧
      ¬ SolvesPlasticPollutionAlone Policy.targetedBagPolicy ∧
      ShouldReducePlasticPollution :=
  ⟨hLitter, hLimit, hGoal⟩
`,
  },
  {
    id: "proof-combined",
    theoremName: "combined_package",
    title: "A conditional common-ground package",
    conclusionId: "X4",
    owner: "shared",
    description:
      "The facilitator’s explicitly marked bridge combines both position-specific proofs. Lean certifies the deduction, not whether the bridge is politically acceptable.",
    premiseIds: ["A1", "A2", "A3", "A4", "C2", "C4", "B1"],
    code: `theorem combined_package
    (hUse : Achieves Policy.targetedBagPolicy Effect.reducesBagUse)
    (hLitter : Achieves Policy.targetedBagPolicy Effect.reducesShorelineBagLitter)
    (hDesign : ResponsibleDesign Policy.targetedBagPolicy)
    (hAdvocateRule : ∀ p, Achieves p Effect.reducesBagUse →
      Achieves p Effect.reducesShorelineBagLitter →
      ResponsibleDesign p → ShouldAdopt p)
    (hProduction : Achieves Policy.productionCaps Effect.addressesVirginProduction)
    (hCriticRule : ∀ p, Achieves p Effect.addressesVirginProduction → ShouldPrioritize p)
    (hBridge : ShouldAdopt Policy.targetedBagPolicy →
      ShouldPrioritize Policy.productionCaps →
      ShouldConsider Policy.combinedPackage) :
    ShouldConsider Policy.combinedPackage :=
  hBridge
    (advocate_case Achieves ResponsibleDesign ShouldAdopt hUse hLitter hDesign hAdvocateRule)
    (critic_case Achieves ShouldPrioritize hProduction hCriticRule)
`,
  },
];

export const negativeControl = {
  id: "negative-overreach",
  theoremName: "overreach_from_litter",
  title: "Negative control: litter reduction proves too little",
  description:
    "This deliberately invalid proof tries to infer that a bag policy solves all plastic pollution from shoreline-litter evidence alone. Lean must reject it.",
  code: `theorem overreach_from_litter
    (hLitter : Achieves Policy.targetedBagPolicy Effect.reducesShorelineBagLitter) :
    SolvesPlasticPollutionAlone Policy.targetedBagPolicy := by
  exact hLitter
`,
};

export function buildLeanSource(theoremName?: string): string {
  const proofs = leanProofs.map((proof) => proof.code).join("\n");
  const audit = theoremName ? `\n#print axioms ${theoremName}\n` : "";
  return `${LEAN_PRELUDE}\n${proofs}${audit}\nend\nend CommonGround\n`;
}

export function buildNegativeControlSource(): string {
  return `${LEAN_PRELUDE}\n${negativeControl.code}\nend\nend CommonGround\n`;
}
