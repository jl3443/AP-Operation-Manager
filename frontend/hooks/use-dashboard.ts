import { useQuery } from "@tanstack/react-query"
import { apiGet } from "@/lib/api"
import type { DashboardKPI, FunnelData, TrendData, VendorSummary } from "@/lib/types"

export function useDashboardKPIs() {
  return useQuery({
    queryKey: ["dashboard", "kpis"],
    queryFn: () => apiGet<DashboardKPI>("/analytics/dashboard"),
  })
}

export function useFunnelData() {
  return useQuery({
    queryKey: ["dashboard", "funnel"],
    queryFn: () => apiGet<FunnelData>("/analytics/funnel"),
  })
}

export function useTrends(days = 30) {
  return useQuery({
    queryKey: ["dashboard", "trends", days],
    queryFn: () => apiGet<TrendData[]>("/analytics/trends", { days }),
  })
}

export function useTopVendors(limit = 10) {
  return useQuery({
    queryKey: ["dashboard", "vendors-top", limit],
    queryFn: () => apiGet<VendorSummary[]>("/analytics/vendors/top", { limit }),
  })
}
