import { useQuery } from "@tanstack/react-query"
import { apiGet } from "@/lib/api"
import type { AuditLog, PaginatedResponse } from "@/lib/types"

interface AuditListParams {
  page?: number
  page_size?: number
  entity_type?: string
  action?: string
  actor_name?: string
  date_from?: string
  date_to?: string
}

export function useAuditLogs(params: AuditListParams = {}) {
  return useQuery({
    queryKey: ["audit", "list", params],
    queryFn: () =>
      apiGet<PaginatedResponse<AuditLog>>("/audit", {
        page: params.page ?? 1,
        page_size: params.page_size ?? 20,
        entity_type: params.entity_type,
        action: params.action,
        actor_name: params.actor_name,
        date_from: params.date_from,
        date_to: params.date_to,
      }),
  })
}
