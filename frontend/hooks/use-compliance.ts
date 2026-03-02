import { useQuery } from "@tanstack/react-query"
import { apiGet } from "@/lib/api"
import type {
  ControlMapping,
  ComplianceGap,
  RootCauseItem,
  OptimizationProposal,
  TouchlessRate,
} from "@/lib/types"

export function useTouchlessRate() {
  return useQuery({
    queryKey: ["analytics", "touchless-rate"],
    queryFn: () => apiGet<TouchlessRate>("/analytics/touchless-rate"),
  })
}

export function useControlMap() {
  return useQuery({
    queryKey: ["compliance", "control-map"],
    queryFn: () => apiGet<ControlMapping[]>("/compliance/control-map"),
  })
}

export function useComplianceGaps() {
  return useQuery({
    queryKey: ["compliance", "gaps"],
    queryFn: () => apiGet<ComplianceGap[]>("/compliance/gaps"),
  })
}

export function useRootCauses() {
  return useQuery({
    queryKey: ["analytics", "root-causes"],
    queryFn: () => apiGet<RootCauseItem[]>("/analytics/root-causes"),
  })
}

export function useOptimizationProposals() {
  return useQuery({
    queryKey: ["analytics", "optimization-proposals"],
    queryFn: () => apiGet<OptimizationProposal[]>("/analytics/optimization-proposals"),
  })
}
