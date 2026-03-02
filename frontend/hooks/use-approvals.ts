import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost } from "@/lib/api"
import type { ApprovalTask } from "@/lib/types"

export function usePendingApprovals() {
  return useQuery({
    queryKey: ["approvals", "pending"],
    queryFn: () => apiGet<ApprovalTask[]>("/approvals/pending"),
  })
}

export function useApprovalHistory(params: { page?: number; page_size?: number } = {}) {
  return useQuery({
    queryKey: ["approvals", "history", params],
    queryFn: () =>
      apiGet<ApprovalTask[]>("/approvals/history", {
        page: params.page ?? 1,
        page_size: params.page_size ?? 20,
      }),
  })
}

export function useApproveTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, comments }: { taskId: string; comments?: string }) =>
      apiPost<ApprovalTask>(`/approvals/${taskId}/approve`, { comments }),
    onMutate: async ({ taskId }) => {
      await queryClient.cancelQueries({ queryKey: ["approvals", "pending"] })
      const previous = queryClient.getQueryData<ApprovalTask[]>(["approvals", "pending"])
      queryClient.setQueryData<ApprovalTask[]>(
        ["approvals", "pending"],
        (old) => old?.filter((t) => t.id !== taskId) ?? []
      )
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["approvals", "pending"], context.previous)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["invoices"] })
    },
  })
}

export function useRejectTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, comments }: { taskId: string; comments?: string }) =>
      apiPost<ApprovalTask>(`/approvals/${taskId}/reject`, { comments }),
    onMutate: async ({ taskId }) => {
      await queryClient.cancelQueries({ queryKey: ["approvals", "pending"] })
      const previous = queryClient.getQueryData<ApprovalTask[]>(["approvals", "pending"])
      queryClient.setQueryData<ApprovalTask[]>(
        ["approvals", "pending"],
        (old) => old?.filter((t) => t.id !== taskId) ?? []
      )
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["approvals", "pending"], context.previous)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["invoices"] })
    },
  })
}

export function useBatchApprove() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { task_ids: string[]; comments?: string }) =>
      apiPost<{ approved: number; errors: string[] }>(
        "/approvals/batch-approve",
        payload
      ),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["invoices"] })
    },
  })
}
