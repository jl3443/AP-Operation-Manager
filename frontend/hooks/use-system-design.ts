import { useQuery } from "@tanstack/react-query"
import { apiGet } from "@/lib/api"

export interface ArchitectureLayer {
  name: string
  tech: string
  components: string[]
}

export interface SixActItem {
  act: number
  name: string
  status: string
  description: string
  features: string[]
}

export interface Architecture {
  name: string
  version: string
  framework: string
  layers: ArchitectureLayer[]
  six_acts: SixActItem[]
}

export interface PipelineStep {
  step: number
  name: string
  description: string
  ai_role: string
  outputs: string[]
}

export interface DataFlow {
  pipeline: PipelineStep[]
}

export interface ApiEndpoint {
  method: string
  path: string
  description: string
}

export interface ApiModule {
  name: string
  prefix: string
  endpoints: ApiEndpoint[]
}

export interface ApiContracts {
  base_url: string
  auth: string
  modules: ApiModule[]
}

export interface SystemStats {
  database: Record<string, number>
  api: { total_endpoints: number; modules: number; auth_method: string }
  tech_stack: Record<string, string[]>
}

export function useArchitecture() {
  return useQuery({
    queryKey: ["system-design", "architecture"],
    queryFn: () => apiGet<Architecture>("/system-design/architecture"),
  })
}

export function useDataFlow() {
  return useQuery({
    queryKey: ["system-design", "data-flow"],
    queryFn: () => apiGet<DataFlow>("/system-design/data-flow"),
  })
}

export function useApiContracts() {
  return useQuery({
    queryKey: ["system-design", "api-contracts"],
    queryFn: () => apiGet<ApiContracts>("/system-design/api-contracts"),
  })
}

export function useSystemStats() {
  return useQuery({
    queryKey: ["system-design", "stats"],
    queryFn: () => apiGet<SystemStats>("/system-design/stats"),
  })
}
