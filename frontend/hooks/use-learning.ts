import { useQuery } from "@tanstack/react-query"
import { apiGet } from "@/lib/api"

export interface ResolutionPattern {
  exception_type: string
  total_count: number
  resolved_count: number
  auto_resolved_count: number
  tolerance_applied_count: number
  resolution_rate: number
  auto_resolve_rate: number
}

export interface ThresholdRecommendation {
  id: string
  type: string
  title: string
  description: string
  current_value: string
  recommended_value: string
  impact: string
  confidence: number
  category: string
}

export interface RuleSuggestion {
  id: string
  type: string
  title: string
  description: string
  rule_text: string
  impact: string
  confidence: number
  category: string
}

export interface BenchmarkMetric {
  current: number
  industry_avg: number
  best_in_class: number
  rating: string
}

export interface PerformanceBenchmarks {
  total_invoices: number
  total_exceptions: number
  touchless_rate: number
  exception_rate: number
  match_performance: {
    total_matched: number
    perfect_matches: number
    tolerance_matches: number
  }
  status_distribution: Record<string, number>
  benchmarks: Record<string, BenchmarkMetric>
}

export interface LearningSummary {
  maturity_score: number
  maturity_level: string
  resolution_patterns: {
    total_exceptions: number
    resolved_count: number
    auto_resolve_rate: number
    patterns: ResolutionPattern[]
  }
  threshold_recommendations: ThresholdRecommendation[]
  rule_suggestions: RuleSuggestion[]
  benchmarks: PerformanceBenchmarks
  total_recommendations: number
  generated_at: string
}

export function useLearningSummary() {
  return useQuery({
    queryKey: ["learning", "summary"],
    queryFn: () => apiGet<LearningSummary>("/learning/summary"),
  })
}

export function useThresholdRecommendations() {
  return useQuery({
    queryKey: ["learning", "threshold-recommendations"],
    queryFn: () => apiGet<ThresholdRecommendation[]>("/learning/threshold-recommendations"),
  })
}

export function useRuleSuggestions() {
  return useQuery({
    queryKey: ["learning", "rule-suggestions"],
    queryFn: () => apiGet<RuleSuggestion[]>("/learning/rule-suggestions"),
  })
}

export function useBenchmarks() {
  return useQuery({
    queryKey: ["learning", "benchmarks"],
    queryFn: () => apiGet<PerformanceBenchmarks>("/learning/benchmarks"),
  })
}
