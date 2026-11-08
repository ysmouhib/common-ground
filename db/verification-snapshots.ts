import type { LEAN_TOOLCHAIN } from "../contracts/lean";

export interface VerificationSnapshot {
  status: "verified" | "failed";
  verifierOutput: string;
  axiomReport: string | null;
  proofHash: string;
  toolchain: typeof LEAN_TOOLCHAIN;
  verifiedAt: string;
}

// Captured from genuine Lean 4.35.0 executions; never hand-authored.
export const verificationSnapshots: Record<string, VerificationSnapshot> = {
  "proof-advocate": {
    "status": "verified",
    "verifierOutput": "'CommonGround.advocate_case' does not depend on any axioms",
    "axiomReport": "'CommonGround.advocate_case' does not depend on any axioms",
    "proofHash": "cc38c9e9186ca7c426a4bc8dfdbedff67a40451ffa463a2f133c329381a45357",
    "toolchain": "Lean 4.35.0",
    "verifiedAt": "2026-11-07T02:25:20.000Z"
  },
  "proof-critic": {
    "status": "verified",
    "verifierOutput": "'CommonGround.critic_case' does not depend on any axioms",
    "axiomReport": "'CommonGround.critic_case' does not depend on any axioms",
    "proofHash": "596e6a0ea5273c6cfc40b7f54a08e5c50a4972c9290ba6fe335461f3c0618582",
    "toolchain": "Lean 4.35.0",
    "verifiedAt": "2026-11-07T02:25:21.000Z"
  },
  "proof-shared": {
    "status": "verified",
    "verifierOutput": "'CommonGround.shared_ground' does not depend on any axioms",
    "axiomReport": "'CommonGround.shared_ground' does not depend on any axioms",
    "proofHash": "efcd61b78cee63f7f850302fa6b4ba04668d139fa0524eb2222913348c47577c",
    "toolchain": "Lean 4.35.0",
    "verifiedAt": "2026-11-07T02:25:21.000Z"
  },
  "proof-combined": {
    "status": "verified",
    "verifierOutput": "'CommonGround.combined_package' does not depend on any axioms",
    "axiomReport": "'CommonGround.combined_package' does not depend on any axioms",
    "proofHash": "c9974eb5d431bedc168f8b8ed6f4d1deb78d0d393b4ef7830686eeafbd4e2531",
    "toolchain": "Lean 4.35.0",
    "verifiedAt": "2026-11-07T02:25:22.000Z"
  },
  "negative-overreach": {
    "status": "failed",
    "verifierOutput": "./Proof.lean:25:2: error: Type mismatch\n  hLitter\nhas type\n  Achieves Policy.targetedBagPolicy Effect.reducesShorelineBagLitter\nbut is expected to have type\n  SolvesPlasticPollutionAlone Policy.targetedBagPolicy",
    "axiomReport": null,
    "proofHash": "8ed232be537138cf2513c01caf82be410e42a08f8baef52c8a74726b1c9c8dac",
    "toolchain": "Lean 4.35.0",
    "verifiedAt": "2026-11-07T02:27:01.000Z"
  }
};
