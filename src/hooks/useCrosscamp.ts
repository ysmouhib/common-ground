import { useCallback, useState } from "react";

import type { inferProcedureInput } from "@trpc/server";

import type { AppRouter } from "../../api/router";

import { trpc } from "@/providers/trpc";

/**
 * Input state and the cross-camp run for the comparison view (CG6-4): two or
 * more (record JSON, candidates JSON) pairs, one per camp, in the same order.
 */

export type CrosscampRunInput = inferProcedureInput<AppRouter["crosscamp"]["run"]>;

export interface InputPair {
  id: string;
  recordText: string;
  candidatesText: string;
}

let counter = 0;
function nextId(): string {
  counter += 1;
  return `pair-${counter.toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

function emptyPair(): InputPair {
  return { id: nextId(), recordText: "", candidatesText: '{"candidates": []}' };
}

export function useCrosscamp() {
  const [pairs, setPairs] = useState<InputPair[]>([emptyPair(), emptyPair()]);
  const [lam, setLam] = useState(0.3);
  const [maxChecks, setMaxChecks] = useState(4000);
  const [lean, setLean] = useState(false);
  const [parseError, setParseError] = useState("");

  const addPair = useCallback(() => setPairs((current) => [...current, emptyPair()]), []);
  const removePair = useCallback((id: string) => {
    setPairs((current) => (current.length > 2 ? current.filter((pair) => pair.id !== id) : current));
  }, []);
  const updatePair = useCallback((id: string, patch: Partial<Omit<InputPair, "id">>) => {
    setPairs((current) => current.map((pair) => (pair.id === id ? { ...pair, ...patch } : pair)));
  }, []);

  const run = trpc.crosscamp.run.useMutation({
    onError: (error) => setParseError(error.message),
  });

  const runAll = useCallback(() => {
    setParseError("");
    try {
      const records = pairs.map((pair) => JSON.parse(pair.recordText) as CrosscampRunInput["records"][number]);
      const candidates = pairs.map((pair) => JSON.parse(pair.candidatesText) as CrosscampRunInput["candidates"][number]);
      run.mutate({ records, candidates, lam, maxChecks, timeoutMs: 5000, lean });
    } catch {
      setParseError("Every pair must hold valid JSON (copy records from the Camps view's \"Copy record JSON\").");
    }
  }, [pairs, lam, maxChecks, lean, run]);

  return { pairs, lam, setLam, maxChecks, setMaxChecks, lean, setLean, addPair, removePair, updatePair, run, runAll, parseError };
}
