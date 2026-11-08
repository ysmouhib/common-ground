import { createHash } from "node:crypto";
import { describe, expect, it } from "vitest";
import { buildLeanSource, buildNegativeControlSource, leanProofs } from "./lean";
import { verificationSnapshots } from "../db/verification-snapshots";

describe("Lean source generation", () => {
  it("keeps four explicit proof certificates and no placeholder constructs", () => {
    expect(leanProofs).toHaveLength(4);
    for (const proof of leanProofs) {
      const source = buildLeanSource(proof.theoremName);
      expect(source).toContain(`theorem ${proof.theoremName}`);
      expect(source).toContain(`#print axioms ${proof.theoremName}`);
      expect(source).not.toMatch(/\b(sorry|admit|axiom|unsafe|native_decide|extern|implemented_by)\b/);
      expect(createHash("sha256").update(source).digest("hex")).toHaveLength(64);
    }
  });

  it("uses a genuinely different type in the negative control", () => {
    const source = buildNegativeControlSource();
    expect(source).toContain("theorem overreach_from_litter");
    expect(source).toContain("SolvesPlasticPollutionAlone Policy.targetedBagPolicy := by");
    expect(source).toContain("exact hLitter");
  });

  it("pins every stored certificate to the exact current source", () => {
    for (const proof of leanProofs) {
      const snapshot = verificationSnapshots[proof.id];
      const hash = createHash("sha256").update(buildLeanSource(proof.theoremName)).digest("hex");
      expect(snapshot.status).toBe("verified");
      expect(snapshot.proofHash).toBe(hash);
      expect(snapshot.verifierOutput).toContain("does not depend on any axioms");
    }
    const negative = verificationSnapshots["negative-overreach"];
    const negativeHash = createHash("sha256").update(buildNegativeControlSource()).digest("hex");
    expect(negative.status).toBe("failed");
    expect(negative.proofHash).toBe(negativeHash);
    expect(negative.verifierOutput).toContain("Type mismatch");
  });
});
