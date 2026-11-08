import { trpc } from "@/providers/trpc";

export function useWorkspace() {
  return trpc.workspace.get.useQuery(undefined, {
    refetchOnWindowFocus: false,
    retry: 1,
  });
}

export type WorkspaceData = NonNullable<ReturnType<typeof useWorkspace>["data"]>;
export type Statement = WorkspaceData["statements"][number];
export type Evidence = WorkspaceData["evidence"][number];
export type Proof = WorkspaceData["proofs"][number];
export type Analysis = WorkspaceData["analysis"];
