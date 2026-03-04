import * as React from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost, apiPatch, apiUpload, apiPostStream } from "@/lib/api"
import type { Invoice, PaginatedResponse, AuditLog } from "@/lib/types"

interface InvoiceListParams {
  page?: number
  page_size?: number
  status?: string
  vendor_id?: string
  search?: string
  sort_by?: string
  sort_order?: string
}

export function useInvoices(params: InvoiceListParams = {}) {
  return useQuery({
    queryKey: ["invoices", "list", params],
    queryFn: () =>
      apiGet<PaginatedResponse<Invoice>>("/invoices", {
        page: params.page ?? 1,
        page_size: params.page_size ?? 20,
        status: params.status,
        vendor_id: params.vendor_id,
        search: params.search,
        sort_by: params.sort_by ?? "created_at",
        sort_order: params.sort_order ?? "desc",
      }),
  })
}

export function useInvoice(id: string) {
  return useQuery({
    queryKey: ["invoices", "detail", id],
    queryFn: () => apiGet<Invoice>(`/invoices/${id}`),
    enabled: !!id,
  })
}

export function useInvoiceAuditTrail(id: string) {
  return useQuery({
    queryKey: ["invoices", "audit-trail", id],
    queryFn: () => apiGet<AuditLog[]>(`/invoices/${id}/audit-trail`),
    enabled: !!id,
  })
}

interface InvoiceCreatePayload {
  invoice_number: string
  vendor_id: string
  invoice_date: string
  due_date: string
  currency?: string
  total_amount: number
  tax_amount?: number
  freight_amount?: number
  discount_amount?: number
  document_type?: string
  source_channel?: string
  line_items?: Array<{
    line_number: number
    description?: string
    quantity?: number
    unit_price: number
    line_total: number
  }>
}

export function useUploadInvoiceFile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ file }: { file: File }) => {
      const formData = new FormData()
      formData.append("file", file)
      return apiUpload<Invoice>("/invoices/upload-file", formData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
    },
  })
}

export function useUploadInvoice() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: InvoiceCreatePayload) =>
      apiPost<Invoice>("/invoices/upload", payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
    },
  })
}

export interface ExtractResult {
  message: string
  data: {
    confidence: number
    extracted_data: Record<string, unknown>
    raw_text: string
    pages_processed: number
  }
  classification: {
    document_type: string
    classification_confidence: number
    classification_reasoning: string
    validation_passed: boolean
    validation_issues: Array<{ field: string; issue: string; severity: string }>
    field_confidence: Record<string, string>
    needs_human_review: boolean
    review_reasons: string[]
    quality_score: number
    recommendations: string[]
  }
}

export function useExtractInvoice() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (invoiceId: string) =>
      apiPost<ExtractResult>(`/invoices/${invoiceId}/extract`),
    onSuccess: (_data, invoiceId) => {
      queryClient.invalidateQueries({ queryKey: ["invoices", "detail", invoiceId] })
    },
  })
}

export function useMatchInvoice() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (invoiceId: string) =>
      apiPost<{
        match_id: string
        match_status: string
        overall_score: number
        details: Record<string, unknown>
      }>(`/invoices/${invoiceId}/match`),
    onSuccess: (_data, invoiceId) => {
      queryClient.invalidateQueries({ queryKey: ["invoices", "detail", invoiceId] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["exceptions"] })
    },
  })
}

export interface PipelineStep {
  step: string
  label: string
  agent: string
  status: "complete" | "error" | "skipped"
  duration_ms: number
  output: Record<string, unknown>
  error?: string
}

export interface PipelineResult {
  invoice_id: string
  invoice_number: string
  total_duration_ms: number
  steps: PipelineStep[]
  final_status: string
  recommendation: "approve" | "review" | "reject" | null
}

export function useApproveInvoice() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (invoiceId: string) =>
      apiPost<{ message: string; status: string; invoice_id: string }>(
        `/invoices/${invoiceId}/approve`
      ),
    onSuccess: (_data, invoiceId) => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] })
      queryClient.invalidateQueries({ queryKey: ["invoices", "detail", invoiceId] })
      queryClient.invalidateQueries({ queryKey: ["approvals"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
    },
  })
}

export function useRejectInvoice() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (invoiceId: string) =>
      apiPost<{ message: string; status: string; invoice_id: string }>(
        `/invoices/${invoiceId}/reject`
      ),
    onSuccess: (_data, invoiceId) => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] })
      queryClient.invalidateQueries({ queryKey: ["invoices", "detail", invoiceId] })
      queryClient.invalidateQueries({ queryKey: ["approvals"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
    },
  })
}

export function useRunPipeline() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (invoiceId: string) =>
      apiPost<PipelineResult>(`/invoices/${invoiceId}/run-pipeline`),
    onSuccess: (_data, invoiceId) => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] })
      queryClient.invalidateQueries({ queryKey: ["invoices", "detail", invoiceId] })
      queryClient.invalidateQueries({ queryKey: ["exceptions"] })
      queryClient.invalidateQueries({ queryKey: ["approvals"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
    },
  })
}

// ── Streaming Pipeline ──────────────────────────────────────────────────────

export interface StreamingPipelineStep {
  step: string
  label: string
  agent?: string
  status: "running" | "complete" | "error"
  duration_ms?: number
  output?: Record<string, unknown>
  error?: string
}

export interface PipelineDone {
  invoice_id: string
  invoice_number: string
  total_duration_ms: number
  final_status: string
  recommendation: "approve" | "review" | "reject" | null
}

export function useRunPipelineStream() {
  const queryClient = useQueryClient()
  const [steps, setSteps] = React.useState<StreamingPipelineStep[]>([])
  const [isStreaming, setIsStreaming] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [done, setDone] = React.useState<PipelineDone | null>(null)

  const start = React.useCallback((invoiceId: string) => {
    setSteps([])
    setIsStreaming(true)
    setError(null)
    setDone(null)

    apiPostStream(`/invoices/${invoiceId}/run-pipeline`, undefined, (event) => {
      const ev = event as Record<string, unknown>

      if (ev.event === "step_start") {
        setSteps((prev) => [
          ...prev,
          {
            step: ev.step as string,
            label: ev.label as string,
            status: "running",
          },
        ])
      } else if (ev.event === "step_complete") {
        setSteps((prev) => {
          const idx = prev.findIndex((s) => s.step === ev.step)
          if (idx >= 0) {
            const updated = [...prev]
            updated[idx] = {
              step: ev.step as string,
              label: ev.label as string,
              agent: ev.agent as string | undefined,
              status: ev.status as "complete" | "error",
              duration_ms: ev.duration_ms as number | undefined,
              output: ev.output as Record<string, unknown> | undefined,
              error: ev.error as string | undefined,
            }
            return updated
          }
          // Step wasn't in the list yet (e.g. exception_resolution that only appears conditionally)
          return [
            ...prev,
            {
              step: ev.step as string,
              label: ev.label as string,
              agent: ev.agent as string | undefined,
              status: ev.status as "complete" | "error",
              duration_ms: ev.duration_ms as number | undefined,
              output: ev.output as Record<string, unknown> | undefined,
              error: ev.error as string | undefined,
            },
          ]
        })
      } else if (ev.event === "pipeline_done") {
        setDone({
          invoice_id: ev.invoice_id as string,
          invoice_number: ev.invoice_number as string,
          total_duration_ms: ev.total_duration_ms as number,
          final_status: ev.final_status as string,
          recommendation: ev.recommendation as "approve" | "review" | "reject" | null,
        })
      } else if (ev.event === "error") {
        setError(ev.message as string)
      }
    })
      .then(() => {
        setIsStreaming(false)
        queryClient.invalidateQueries({ queryKey: ["invoices"] })
        queryClient.invalidateQueries({ queryKey: ["exceptions"] })
        queryClient.invalidateQueries({ queryKey: ["approvals"] })
        queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      })
      .catch((err) => {
        setIsStreaming(false)
        setError(err instanceof Error ? err.message : "Stream failed")
      })
  }, [queryClient])

  const reset = React.useCallback(() => {
    setSteps([])
    setIsStreaming(false)
    setError(null)
    setDone(null)
  }, [])

  return { steps, isStreaming, error, done, start, reset }
}
