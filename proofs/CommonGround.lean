namespace CommonGround

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

theorem advocate_case
    (hUse : Achieves Policy.targetedBagPolicy Effect.reducesBagUse)
    (hLitter : Achieves Policy.targetedBagPolicy Effect.reducesShorelineBagLitter)
    (hDesign : ResponsibleDesign Policy.targetedBagPolicy)
    (hRule : ∀ p, Achieves p Effect.reducesBagUse →
      Achieves p Effect.reducesShorelineBagLitter →
      ResponsibleDesign p → ShouldAdopt p) :
    ShouldAdopt Policy.targetedBagPolicy :=
  hRule Policy.targetedBagPolicy hUse hLitter hDesign

theorem critic_case
    (hProduction : Achieves Policy.productionCaps Effect.addressesVirginProduction)
    (hRule : ∀ p, Achieves p Effect.addressesVirginProduction → ShouldPrioritize p) :
    ShouldPrioritize Policy.productionCaps :=
  hRule Policy.productionCaps hProduction

theorem shared_ground
    (hLitter : Achieves Policy.targetedBagPolicy Effect.reducesShorelineBagLitter)
    (hLimit : ¬ SolvesPlasticPollutionAlone Policy.targetedBagPolicy)
    (hGoal : ShouldReducePlasticPollution) :
    Achieves Policy.targetedBagPolicy Effect.reducesShorelineBagLitter ∧
      ¬ SolvesPlasticPollutionAlone Policy.targetedBagPolicy ∧
      ShouldReducePlasticPollution :=
  ⟨hLitter, hLimit, hGoal⟩

theorem combined_package
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

end
end CommonGround
