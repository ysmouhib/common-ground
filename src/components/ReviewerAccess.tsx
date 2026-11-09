import { useState } from "react";
import { KeyRound, Lock, LockOpen } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { trpc } from "@/providers/trpc";
import { setReviewerToken } from "@/lib/reviewer";

interface Props {
  access: { reviewEnabled: boolean; isReviewer: boolean } | undefined;
}

/**
 * Review decisions, Lean runs and AI drafts need the deployment's reviewer token.
 * Everything else is public. This control shows which of the two the visitor has.
 */
export function ReviewerAccess({ access }: Props) {
  const [open, setOpen] = useState(false);
  const [token, setToken] = useState("");
  const [rejected, setRejected] = useState(false);
  const utils = trpc.useUtils();

  if (!access) return null;
  if (!access.reviewEnabled) {
    return (
      <span className="inline-flex min-h-11 items-center gap-2 border border-[#c8cfdb] px-4 text-sm text-[#4c5260]" title="No reviewer token is configured on this deployment.">
        <Lock className="size-4" aria-hidden="true" /> Read-only deployment
      </span>
    );
  }

  async function apply(next: string) {
    setReviewerToken(next);
    const fresh = await utils.workspace.get.fetch(undefined, { staleTime: 0 });
    await utils.workspace.get.invalidate();
    if (next && !fresh.access.isReviewer) {
      setReviewerToken("");
      setRejected(true);
      return;
    }
    setRejected(false);
    setToken("");
    setOpen(false);
  }

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
              onChange={(event) => setToken(event.target.value)}
              className="mt-2 w-full border border-[#aeb8c9] bg-[#f8f8f8] p-3 text-base text-foreground"
            />
            {rejected && <p role="alert" className="mt-2 text-sm text-[#8a2d21]">That token was not accepted.</p>}
            <button
              type="submit"
              disabled={token.trim().length === 0}
              className="transition-ui mt-4 inline-flex min-h-11 items-center justify-center bg-primary px-4 font-semibold text-primary-foreground hover:bg-[#173f92] disabled:opacity-45"
            >
              Unlock review
            </button>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
