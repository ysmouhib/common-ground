import { useState } from "react";
import { KeyRound, Lock, LockOpen } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { trpc } from "@/providers/trpc";
import { setReviewerToken } from "@/lib/reviewer";

interface Props {
  access: { reviewEnabled: boolean; isReviewer: boolean; lockedOut: boolean } | undefined;
}

type Problem = "wrong" | "locked" | "unreachable" | null;

const MESSAGES: Record<Exclude<Problem, null>, string> = {
  wrong: "That token was not accepted.",
  locked: "Too many wrong tokens were sent from this network. No token is accepted for up to 15 minutes.",
  unreachable: "The server could not be reached. The token was not checked.",
};

/**
 * Review decisions, Lean runs and AI drafts need the deployment's reviewer token.
 * Everything else is public. This control shows which of the two the visitor has.
 */
export function ReviewerAccess({ access }: Props) {
  const [open, setOpen] = useState(false);
  const [token, setToken] = useState("");
  const [problem, setProblem] = useState<Problem>(null);
  const [checking, setChecking] = useState(false);
  const utils = trpc.useUtils();

  if (!access) return null;
  if (!access.reviewEnabled) {
    return (
      <span className="inline-flex min-h-11 items-center gap-2 border border-[#c8cfdb] px-4 text-sm text-[#4c5260]" title="No reviewer token is configured on this deployment.">
        <Lock className="size-4" aria-hidden="true" /> Read-only deployment
      </span>
    );
  }

  // One request per attempt: the server counts every wrong token, so the answer to
  // this request is the check. It also replaces the cached workspace, which is what
  // the rest of the page reads its access from.
  async function apply(next: string) {
    setChecking(true);
    setReviewerToken(next);
    try {
      const fresh = await utils.workspace.get.fetch(undefined, { staleTime: 0 });
      if (next && !fresh.access.isReviewer) {
        setReviewerToken("");
        setProblem(fresh.access.lockedOut ? "locked" : "wrong");
        return;
      }
      setProblem(null);
      setToken("");
      setOpen(false);
    } catch {
      setReviewerToken("");
      setProblem("unreachable");
    } finally {
      setChecking(false);
    }
  }

  const shown: Problem = problem ?? (access.lockedOut ? "locked" : null);

  return (
    <>
      <button
        type="button"
        onClick={() => (access.isReviewer ? void apply("") : setOpen(true))}
        className="transition-ui inline-flex min-h-11 items-center justify-center gap-2 border border-[#8b93a2] px-4 text-sm font-semibold hover:bg-secondary"
      >
        {access.isReviewer ? <LockOpen className="size-4 text-primary" aria-hidden="true" /> : <KeyRound className="size-4" aria-hidden="true" />}
        {access.isReviewer ? "Reviewer: sign out" : "Reviewer access"}
      </button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reviewer access</DialogTitle>
            <DialogDescription>
              Reading is open to everyone. Recording a review decision, re-running Lean or requesting an AI draft needs this site&apos;s reviewer token. It is kept for this browser tab only.
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void apply(token.trim());
            }}
          >
            <label htmlFor="reviewer-token" className="text-sm font-semibold">Reviewer token</label>
            <input
              id="reviewer-token"
              type="password"
              autoComplete="off"
              value={token}
              onChange={(event) => {
                setToken(event.target.value);
                setProblem(null);
              }}
              className="mt-2 w-full border border-[#aeb8c9] bg-[#f8f8f8] p-3 text-base text-foreground"
            />
            {shown && <p role="alert" className="mt-2 text-sm text-[#8a2d21]">{MESSAGES[shown]}</p>}
            <button
              type="submit"
              disabled={checking || token.trim().length === 0}
              className="transition-ui mt-4 inline-flex min-h-11 items-center justify-center bg-primary px-4 font-semibold text-primary-foreground hover:bg-[#173f92] disabled:opacity-45"
            >
              {checking ? "Checking…" : "Unlock review"}
            </button>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
