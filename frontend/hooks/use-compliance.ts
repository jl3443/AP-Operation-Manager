import { useQuery } from "@tanstack/react-query"
import { apiGet } from "@/lib/api"
import type {
  ControlMapping,
  ComplianceGap,
  RootCauseItem,
  OptimizationProposal,
  TouchlessRate,
  ControlTestResult,
  ComplianceScoringResult,
  AuditPack,
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

// ── Phase 3: New Compliance Hooks ─────────────────────────────────

export function useControlTests() {
  return useQuery({
    queryKey: ["compliance", "control-tests"],
    queryFn: () => apiGet<ControlTestResult[]>("/compliance/control-tests"),
  })
}

export function useComplianceScoring() {
  return useQuery({
    queryKey: ["compliance", "scoring"],
    queryFn: () => apiGet<ComplianceScoringResult>("/compliance/scoring"),
  })
}

export function useAuditPack() {
  return useQuery({
    queryKey: ["compliance", "audit-pack"],
    queryFn: () => apiGet<AuditPack>("/compliance/audit-pack"),
  })
}
