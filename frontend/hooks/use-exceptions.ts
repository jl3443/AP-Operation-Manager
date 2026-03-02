import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPatch, apiPost } from "@/lib/api"
import type { Exception_, ExceptionComment, PaginatedResponse } from "@/lib/types"

interface ExceptionListParams {
  page?: number
  page_size?: number
  status?: string
  severity?: string
  exception_type?: string
  assigned_to?: string
}

export function useExceptions(params: ExceptionListParams = {}) {
  return useQuery({
    queryKey: ["exceptions", "list", params],
    queryFn: () =>
      apiGet<PaginatedResponse<Exception_>>("/exceptions", {
        page: params.page ?? 1,
        page_size: params.page_size ?? 20,
        status: params.status,
        severity: params.severity,
        exception_type: params.exception_type,
        assigned_to: params.assigned_to,
      }),
  })
}

export function useException(id: string) {
  return useQuery({
    queryKey: ["exceptions", "detail", id],
    queryFn: () => apiGet<Exception_>(`/exceptions/${id}`),
    enabled: !!id,
  })
}

export function useUpdateException() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      ...payload
    }: {
      id: string
      status?: string
      assigned_to?: string
      severity?: string
      resolution_type?: string
      resolution_notes?: string
    }) => apiPatch<Exception_>(`/exceptions/${id}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exceptions"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
    },
  })
}

export function useAddExceptionComment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      exceptionId,
      comment_text,
      mentions,
    }: {
      exceptionId: string
      comment_text: string
      mentions?: string[]
    }) =>
      apiPost<ExceptionComment>(`/exceptions/${exceptionId}/comments`, {
        comment_text,
        mentions,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exceptions"] })
    },
  })
}

export function useBatchAssignExceptions() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { exception_ids: string[]; assigned_to: string }) =>
      apiPost<{ message: string; updated: number }>(
        "/exceptions/batch-assign",
        payload
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exceptions"] })
    },
  })
}
