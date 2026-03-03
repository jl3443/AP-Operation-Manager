import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost } from "@/lib/api"

export interface KnowledgeSummary {
  total_documents: number
  total_rules: number
  pending_review: number
  approved_rules: number
  rejected_rules: number
  avg_confidence: number
  rules_by_type: Record<string, number>
  documents_by_type: Record<string, number>
}

export interface PolicyDocumentInfo {
  id: string
  filename: string
  document_type: string
  extraction_status: string
  rules_count: number
  uploaded_at: string | null
}

export interface PolicyRuleInfo {
  id: string
  rule_type: string
  source_text: string
  conditions: Record<string, unknown> | null
  action: Record<string, unknown> | null
  confidence: number
  status: string
  document: string | null
  document_type: string | null
  created_at: string | null
}

export function useKnowledgeSummary() {
  return useQuery({
    queryKey: ["knowledge", "summary"],
    queryFn: () => apiGet<KnowledgeSummary>("/knowledge/summary"),
  })
}

export function useKnowledgeDocuments() {
  return useQuery({
    queryKey: ["knowledge", "documents"],
    queryFn: () => apiGet<PolicyDocumentInfo[]>("/knowledge/documents"),
  })
}

export function useKnowledgeRules(filters?: {
  rule_type?: string
  status?: string
  min_confidence?: number
}) {
  return useQuery({
    queryKey: ["knowledge", "rules", filters],
    queryFn: () =>
      apiGet<PolicyRuleInfo[]>("/knowledge/rules", {
        rule_type: filters?.rule_type,
        status: filters?.status,
        min_confidence: filters?.min_confidence,
      }),
  })
}

export function useSearchRules(query: string) {
  return useQuery({
    queryKey: ["knowledge", "search", query],
    queryFn: () => apiGet<PolicyRuleInfo[]>("/knowledge/search", { q: query }),
    enabled: query.length > 0,
  })
}

export function useParseDocuments() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { ap_inputs_dir?: string; use_ai?: boolean }) =>
      apiPost("/knowledge/parse", payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge"] })
    },
  })
}

export function useApproveRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (ruleId: string) =>
      apiPost(`/knowledge/rules/${ruleId}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge"] })
    },
  })
}

export function useRejectRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ ruleId, notes }: { ruleId: string; notes?: string }) =>
      apiPost(`/knowledge/rules/${ruleId}/reject`, { notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge"] })
    },
  })
}
