import { AlertTriangle, Check, CircleDashed, FlaskConical, ShieldCheck } from "lucide-react";

type Tone = "blue" | "green" | "amber" | "red" | "neutral";

const toneClasses: Record<Tone, string> = {
  blue: "border-[#9cadd7] bg-[#eaf0ff] text-[#173f92]",
  green: "border-[#8aa900] bg-[#efffc0] text-[#314300]",
  amber: "border-[#d7ae4a] bg-[#fff0c2] text-[#694b00]",
  red: "border-[#dca497] bg-[#ffebe6] text-[#8a2d21]",
  neutral: "border-[#c5cbd4] bg-[#f1f2f4] text-[#3f4550]",
};

export function StatusBadge({
  children,
  tone = "neutral",
  icon,
}: {
  children: React.ReactNode;
  tone?: Tone;
  icon?: "check" | "shield" | "warning" | "draft" | "test";
}) {
  const Icon =
    icon === "check"
      ? Check
      : icon === "shield"
        ? ShieldCheck
        : icon === "warning"
          ? AlertTriangle
          : icon === "test"
            ? FlaskConical
            : CircleDashed;
  return (
    <span
      className={`inline-flex min-h-7 items-center gap-1.5 border px-2 py-0.5 text-xs font-semibold leading-5 ${toneClasses[tone]}`}
    >
      {icon && <Icon className="size-3.5" aria-hidden="true" />}
      {children}
    </span>
  );
}

export function ApprovalBadge({ status }: { status: "approved" | "disputed" | "draft" }) {
  if (status === "approved") return <StatusBadge tone="green" icon="check">Approved</StatusBadge>;
  if (status === "disputed") return <StatusBadge tone="red" icon="warning">Disputed</StatusBadge>;
  return <StatusBadge tone="amber" icon="draft">Draft</StatusBadge>;
}

export function ProofBadge({ proof }: { proof: import("@/hooks/useWorkspace").Proof }) {
  if (proof.isNegativeControl) {
    if (proof.status === "failed" && proof.hashCurrent) {
      return <StatusBadge tone="green" icon="test">Rejected as expected</StatusBadge>;
    }
    if (proof.status === "verified" && proof.hashCurrent) {
      return <StatusBadge tone="red" icon="warning">Invalid proof accepted</StatusBadge>;
    }
    return <StatusBadge tone="amber" icon="test">Control not run</StatusBadge>;
  }
  if (proof.active) return <StatusBadge tone="green" icon="shield">Active certificate</StatusBadge>;
  if (proof.kernelVerified) return <StatusBadge tone="amber" icon="warning">Kernel verified · inactive</StatusBadge>;
  if (proof.status === "failed") return <StatusBadge tone="red" icon="warning">Lean rejected</StatusBadge>;
  return <StatusBadge tone="neutral" icon="draft">Unverified</StatusBadge>;
}
