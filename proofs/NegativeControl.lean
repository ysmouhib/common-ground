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

theorem overreach_from_litter
    (hLitter : Achieves Policy.targetedBagPolicy Effect.reducesShorelineBagLitter) :
    SolvesPlasticPollutionAlone Policy.targetedBagPolicy := by
  exact hLitter

end
end CommonGround
