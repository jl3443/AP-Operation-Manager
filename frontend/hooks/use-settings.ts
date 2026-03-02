import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPatch } from "@/lib/api"

interface ToleranceConfig {
  id: string
  name: string
  scope: string
  scope_value?: string
  amount_tolerance_pct: number
  amount_tolerance_abs: number
  quantity_tolerance_pct: number
  is_active: boolean
  version: number
  created_at: string
  updated_at: string
}

export function useTolerances() {
  return useQuery({
    queryKey: ["config", "tolerances"],
    queryFn: () => apiGet<ToleranceConfig[]>("/config/tolerances"),
  })
}

export function useUpdateTolerance() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string } & Partial<ToleranceConfig>) =>
      apiPatch<ToleranceConfig>(`/config/tolerances/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["config"] })
    },
  })
}
