import { useQuery, useMutation } from "@tanstack/react-query"
import { apiGet } from "@/lib/api"
import type {
  AgingData,
  ExceptionBreakdown,
  VendorRiskDistribution,
  MonthlyComparison,
  ApprovalTurnaround,
} from "@/lib/types"

export function useAgingAnalysis() {
  return useQuery({
    queryKey: ["analytics", "aging"],
    queryFn: () => apiGet<AgingData>("/analytics/aging"),
  })
}

export function useExceptionBreakdown() {
  return useQuery({
    queryKey: ["analytics", "exceptions-breakdown"],
    queryFn: () => apiGet<ExceptionBreakdown[]>("/analytics/exceptions/breakdown"),
  })
}

export function useVendorRiskDistribution() {
  return useQuery({
    queryKey: ["analytics", "vendor-risk"],
    queryFn: () => apiGet<VendorRiskDistribution[]>("/analytics/vendors/risk-distribution"),
  })
}

export function useMonthlyComparison() {
  return useQuery({
    queryKey: ["analytics", "monthly-comparison"],
    queryFn: () => apiGet<MonthlyComparison[]>("/analytics/monthly-comparison"),
  })
}

export function useApprovalTurnaround() {
  return useQuery({
    queryKey: ["analytics", "approval-turnaround"],
    queryFn: () => apiGet<ApprovalTurnaround[]>("/analytics/approvals/turnaround"),
  })
}

export function useExportPdfReport() {
  return useMutation({
    mutationFn: async (params?: { dateFrom?: string; dateTo?: string }) => {
      const token = localStorage.getItem("access_token")
      const url = new URL("/api/v1/analytics/report/pdf", window.location.origin)

      if (params?.dateFrom) {
        url.searchParams.append("date_from", params.dateFrom)
      }
      if (params?.dateTo) {
        url.searchParams.append("date_to", params.dateTo)
      }

      const response = await fetch(url.toString(), {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error("Failed to export PDF report")
      }

      const blob = await response.blob()
      const blobUrl = URL.createObjectURL(blob)

      const a = document.createElement("a")
      a.href = blobUrl
      a.download = `ap-analytics-report-${new Date().toISOString().slice(0, 10)}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)

      URL.revokeObjectURL(blobUrl)
    },
  })
}
