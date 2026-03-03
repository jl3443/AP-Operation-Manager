"use client"

import * as React from "react"
import {
  Sparkles,
  TrendingUp,
  TrendingDown,
  Target,
  Lightbulb,
  Settings2,
  Zap,
  BarChart3,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Activity,
  ArrowRight,
} from "lucide-react"

import { useLearningSummary } from "@/hooks/use-learning"
import type { BenchmarkMetric } from "@/hooks/use-learning"
import { KpiCardSkeleton, TableSkeleton } from "@/components/loading-skeleton"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const maturityColors: Record<string, string> = {
  Initial: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  Developing: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  Managed: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  Optimized: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
}

const ratingColors: Record<string, string> = {
  best_in_class: "text-emerald-600 dark:text-emerald-400",
  above_average: "text-blue-600 dark:text-blue-400",
  below_average: "text-amber-600 dark:text-amber-400",
  needs_improvement: "text-red-600 dark:text-red-400",
}

const categoryColors: Record<string, string> = {
  tolerance: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  auto_resolution: "bg-violet-100 text-violet-800 dark:bg-violet-900/30 dark:text-violet-400",
  vendor_config: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  validation: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
  duplicate_prevention: "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400",
  approval: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400",
  escalation: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100)
  const color =
    pct >= 80
      ? "bg-emerald-500"
      : pct >= 60
        ? "bg-blue-500"
        : pct >= 40
          ? "bg-amber-500"
          : "bg-red-500"
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-20 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono">{pct}%</span>
    </div>
  )
}

function BenchmarkCard({ name, metric }: { name: string; metric: BenchmarkMetric }) {
  const displayName = name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
  const isGood = metric.rating === "best_in_class" || metric.rating === "above_average"
  const aboveIndustry = metric.current >= metric.industry_avg

  return (
    <div className="border rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">{displayName}</p>
        {isGood ? (
          <TrendingUp className="size-4 text-emerald-500" />
        ) : (
          <TrendingDown className="size-4 text-red-500" />
        )}
      </div>
      <div className="flex items-end gap-2">
        <span className="text-3xl font-bold">{metric.current}%</span>
        <span className={`text-sm mb-1 ${ratingColors[metric.rating] ?? ""}`}>
          {metric.rating.replace(/_/g, " ")}
        </span>
      </div>
      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Industry Avg</span>
          <span className="font-mono">{metric.industry_avg}%</span>
        </div>
        <div className="h-2 rounded-full bg-muted overflow-hidden relative">
          {/* Industry avg marker */}
          <div
            className="absolute top-0 h-full w-px bg-muted-foreground/40 z-10"
            style={{ left: `${metric.industry_avg}%` }}
          />
          <div
            className={`h-full rounded-full ${aboveIndustry ? "bg-emerald-500" : "bg-amber-500"}`}
            style={{ width: `${Math.min(metric.current, 100)}%` }}
          />
        </div>
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Best in Class</span>
          <span className="font-mono">{metric.best_in_class}%</span>
        </div>
      </div>
    </div>
  )
}

export default function ImprovementsPage() {
  const { data, isLoading } = useLearningSummary()

  if (isLoading) {
    return (
      <div className="space-y-6">
        <p className="text-muted-foreground">Loading AI improvement analysis...</p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => <KpiCardSkeleton key={i} />)}
        </div>
        <TableSkeleton rows={6} cols={4} />
      </div>
    )
  }

  if (!data) {
    return <p className="text-center text-muted-foreground py-8">Failed to load learning data</p>
  }

  const { benchmarks } = data

  return (
    <div className="space-y-6">
      <p className="text-muted-foreground">
        AI-driven self-improvement: learning from operations to optimize thresholds, suggest rules, and benchmark performance.
      </p>

      {/* Maturity & Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Maturity Level</p>
                <Badge variant="secondary" className={`mt-1 text-base px-3 py-1 ${maturityColors[data.maturity_level]}`}>
                  {data.maturity_level}
                </Badge>
              </div>
              <div className="size-12 rounded-full flex items-center justify-center bg-violet-100 dark:bg-violet-900/30">
                <Sparkles className="size-6 text-violet-600 dark:text-violet-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Recommendations</p>
                <p className="text-2xl font-bold">{data.total_recommendations}</p>
              </div>
              <Lightbulb className="size-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Auto-Resolve Rate</p>
                <p className="text-2xl font-bold">{data.resolution_patterns.auto_resolve_rate}%</p>
              </div>
              <Zap className="size-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Touchless Rate</p>
                <p className="text-2xl font-bold">{benchmarks.touchless_rate}%</p>
              </div>
              <Target className="size-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="benchmarks" className="space-y-4">
        <TabsList>
          <TabsTrigger value="benchmarks">Performance Benchmarks</TabsTrigger>
          <TabsTrigger value="thresholds">Threshold Tuning</TabsTrigger>
          <TabsTrigger value="rules">Rule Suggestions</TabsTrigger>
          <TabsTrigger value="patterns">Resolution Patterns</TabsTrigger>
        </TabsList>

        {/* Tab: Performance Benchmarks */}
        <TabsContent value="benchmarks">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="size-5" />
                Performance vs Industry Benchmarks
              </CardTitle>
              <CardDescription>
                Your AP operations compared against industry averages and best-in-class organizations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2">
                {Object.entries(benchmarks.benchmarks).map(([name, metric]) => (
                  <BenchmarkCard key={name} name={name} metric={metric} />
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Threshold Tuning */}
        <TabsContent value="thresholds">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings2 className="size-5" />
                AI Threshold Tuning Recommendations
              </CardTitle>
              <CardDescription>
                Learned from exception resolution patterns to recommend tolerance adjustments
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.threshold_recommendations.map((rec) => (
                  <div key={rec.id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-muted-foreground">{rec.id}</span>
                        <h4 className="font-medium">{rec.title}</h4>
                      </div>
                      <Badge variant="secondary" className={categoryColors[rec.category] ?? "bg-slate-100 text-slate-800"}>
                        {rec.category.replace(/_/g, " ")}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{rec.description}</p>
                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">Current:</span>
                        <Badge variant="outline">{rec.current_value}</Badge>
                      </div>
                      <ArrowRight className="size-4 text-muted-foreground" />
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">Recommended:</span>
                        <Badge variant="secondary" className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">
                          {rec.recommended_value}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm">
                        <TrendingUp className="size-4 text-emerald-500" />
                        <span className="text-emerald-600 dark:text-emerald-400">{rec.impact}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">Confidence:</span>
                        <ConfidenceBar confidence={rec.confidence} />
                      </div>
                    </div>
                  </div>
                ))}
                {data.threshold_recommendations.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">
                    No threshold adjustments needed — current settings are optimal
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Rule Suggestions */}
        <TabsContent value="rules">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="size-5" />
                AI-Suggested Business Rules
              </CardTitle>
              <CardDescription>
                New rules or process improvements suggested by analyzing operational data
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.rule_suggestions.map((rule) => (
                  <div key={rule.id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-muted-foreground">{rule.id}</span>
                        <h4 className="font-medium">{rule.title}</h4>
                      </div>
                      <Badge variant="secondary" className={categoryColors[rule.category] ?? "bg-slate-100 text-slate-800"}>
                        {rule.category.replace(/_/g, " ")}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{rule.description}</p>
                    <div className="rounded-md bg-muted p-3 font-mono text-xs">
                      {rule.rule_text}
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm">
                        <TrendingUp className="size-4 text-emerald-500" />
                        <span className="text-emerald-600 dark:text-emerald-400">{rule.impact}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">Confidence:</span>
                        <ConfidenceBar confidence={rule.confidence} />
                      </div>
                    </div>
                  </div>
                ))}
                {data.rule_suggestions.length === 0 && (
                  <p className="text-center text-muted-foreground py-8">
                    No new rules suggested — current rules are comprehensive
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Resolution Patterns */}
        <TabsContent value="patterns">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="size-5" />
                Exception Resolution Patterns
              </CardTitle>
              <CardDescription>
                How exceptions are being resolved — identifies opportunities for automation
              </CardDescription>
            </CardHeader>
            <CardContent>
              {data.resolution_patterns.patterns.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Exception Type</TableHead>
                      <TableHead className="text-center">Total</TableHead>
                      <TableHead className="text-center">Resolved</TableHead>
                      <TableHead className="text-center">Auto-Resolved</TableHead>
                      <TableHead>Resolution Rate</TableHead>
                      <TableHead>Auto Rate</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.resolution_patterns.patterns.map((p) => (
                      <TableRow key={p.exception_type}>
                        <TableCell>
                          <span className="text-sm font-medium">
                            {p.exception_type.replace(/_/g, " ")}
                          </span>
                        </TableCell>
                        <TableCell className="text-center font-mono">{p.total_count}</TableCell>
                        <TableCell className="text-center font-mono">{p.resolved_count}</TableCell>
                        <TableCell className="text-center font-mono">{p.auto_resolved_count}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="h-2 w-16 rounded-full bg-muted overflow-hidden">
                              <div
                                className={`h-full rounded-full ${p.resolution_rate >= 70 ? "bg-emerald-500" : p.resolution_rate >= 40 ? "bg-amber-500" : "bg-red-500"}`}
                                style={{ width: `${p.resolution_rate}%` }}
                              />
                            </div>
                            <span className="text-xs font-mono">{p.resolution_rate}%</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="h-2 w-16 rounded-full bg-muted overflow-hidden">
                              <div
                                className={`h-full rounded-full ${p.auto_resolve_rate >= 50 ? "bg-blue-500" : p.auto_resolve_rate > 0 ? "bg-violet-500" : "bg-slate-300"}`}
                                style={{ width: `${p.auto_resolve_rate}%` }}
                              />
                            </div>
                            <span className="text-xs font-mono">{p.auto_resolve_rate}%</span>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  No exception data available for pattern analysis
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
