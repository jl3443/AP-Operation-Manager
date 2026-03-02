"use client"

import * as React from "react"
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Lightbulb,
  TrendingDown,
  ArrowUpRight,
} from "lucide-react"

import {
  useControlMap,
  useComplianceGaps,
  useRootCauses,
  useOptimizationProposals,
} from "@/hooks/use-compliance"
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

const statusColors: Record<string, string> = {
  active: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
  partial: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  planned: "bg-slate-100 text-slate-800 dark:bg-slate-900/30 dark:text-slate-400",
}

const severityColors: Record<string, string> = {
  high: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  medium: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  low: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
}

const priorityColors: Record<string, string> = {
  high: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  medium: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  low: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
}

const gapStatusColors: Record<string, string> = {
  open: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  remediation: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  closed: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
}

export default function CompliancePage() {
  const { data: controls, isLoading: controlsLoading } = useControlMap()
  const { data: gaps, isLoading: gapsLoading } = useComplianceGaps()
  const { data: rootCauses, isLoading: rcLoading } = useRootCauses()
  const { data: proposals, isLoading: proposalsLoading } = useOptimizationProposals()

  const activeControls = controls?.filter((c) => c.implementation_status === "active").length ?? 0
  const totalControls = controls?.length ?? 0
  const openGaps = gaps?.filter((g) => g.status === "open").length ?? 0
  const highPriorityProposals = proposals?.filter((p) => p.priority === "high").length ?? 0

  return (
    <div className="space-y-6">
      <p className="text-muted-foreground">
        Audit compliance, control mapping, gap analysis, and continuous improvement insights.
      </p>

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Controls Active</p>
                <p className="text-2xl font-bold">{activeControls}/{totalControls}</p>
              </div>
              <ShieldCheck className="size-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Open Gaps</p>
                <p className="text-2xl font-bold">{openGaps}</p>
              </div>
              <ShieldAlert className="size-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Root Causes</p>
                <p className="text-2xl font-bold">{rootCauses?.length ?? 0}</p>
              </div>
              <TrendingDown className="size-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Optimization Ideas</p>
                <p className="text-2xl font-bold">{highPriorityProposals} high priority</p>
              </div>
              <Lightbulb className="size-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="controls" className="space-y-4">
        <TabsList>
          <TabsTrigger value="controls">Control Mapping</TabsTrigger>
          <TabsTrigger value="gaps">Gap Analysis</TabsTrigger>
          <TabsTrigger value="root-causes">Root Causes</TabsTrigger>
          <TabsTrigger value="optimization">Optimization</TabsTrigger>
        </TabsList>

        {/* Tab 1: Control Mapping */}
        <TabsContent value="controls">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="size-5" />
                AP Control-to-Policy Mapping
              </CardTitle>
              <CardDescription>
                System controls mapped to AP policy sections with implementation status
              </CardDescription>
            </CardHeader>
            <CardContent>
              {controlsLoading ? (
                <TableSkeleton rows={6} cols={5} />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>Control</TableHead>
                      <TableHead>Policy Section</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Auto</TableHead>
                      <TableHead>Test</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {controls?.map((c) => (
                      <TableRow key={c.control_id}>
                        <TableCell className="font-mono text-xs">{c.control_id}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium text-sm">{c.control_name}</p>
                            <p className="text-xs text-muted-foreground">{c.description}</p>
                          </div>
                        </TableCell>
                        <TableCell className="text-xs">{c.policy_section}</TableCell>
                        <TableCell>
                          <Badge variant="secondary" className={statusColors[c.implementation_status]}>
                            {c.implementation_status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {c.automated ? (
                            <CheckCircle className="size-4 text-emerald-500" />
                          ) : (
                            <Clock className="size-4 text-muted-foreground" />
                          )}
                        </TableCell>
                        <TableCell>
                          {c.test_result === "pass" ? (
                            <Badge variant="secondary" className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">Pass</Badge>
                          ) : c.test_result === "fail" ? (
                            <Badge variant="secondary" className="bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">Fail</Badge>
                          ) : (
                            <Badge variant="secondary">N/A</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: Gap Analysis */}
        <TabsContent value="gaps">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="size-5" />
                Compliance Gap Register
              </CardTitle>
              <CardDescription>
                Identified compliance gaps based on exception patterns and audit data
              </CardDescription>
            </CardHeader>
            <CardContent>
              {gapsLoading ? (
                <TableSkeleton rows={4} cols={5} />
              ) : (
                <div className="space-y-4">
                  {gaps?.map((g) => (
                    <div key={g.gap_id} className="border rounded-lg p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs text-muted-foreground">{g.gap_id}</span>
                          <Badge variant="secondary" className={severityColors[g.severity]}>
                            {g.severity}
                          </Badge>
                          <Badge variant="secondary" className={gapStatusColors[g.status]}>
                            {g.status}
                          </Badge>
                        </div>
                        <span className="text-xs text-muted-foreground">Control: {g.control_id}</span>
                      </div>
                      <p className="text-sm font-medium">{g.finding}</p>
                      <div className="flex items-start gap-2 text-sm text-muted-foreground">
                        <Lightbulb className="size-4 shrink-0 mt-0.5" />
                        <span>{g.recommendation}</span>
                      </div>
                      {g.evidence_count > 0 && (
                        <p className="text-xs text-muted-foreground">Evidence: {g.evidence_count} occurrences</p>
                      )}
                    </div>
                  ))}
                  {(!gaps || gaps.length === 0) && (
                    <p className="text-center text-muted-foreground py-8">No compliance gaps identified</p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: Root Cause Analysis */}
        <TabsContent value="root-causes">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingDown className="size-5" />
                Root Cause Analysis
              </CardTitle>
              <CardDescription>
                Exception patterns analyzed by type and vendor to identify systemic issues
              </CardDescription>
            </CardHeader>
            <CardContent>
              {rcLoading ? (
                <TableSkeleton rows={5} cols={5} />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Issue</TableHead>
                      <TableHead className="text-center">Occurrences</TableHead>
                      <TableHead className="text-right">Impact ($)</TableHead>
                      <TableHead>Suggested Fix</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {rootCauses?.map((rc, i) => (
                      <TableRow key={i}>
                        <TableCell>
                          <div>
                            <p className="font-medium text-sm">{rc.issue}</p>
                            <Badge variant="secondary" className="mt-1 text-xs">
                              {rc.category.replace(/_/g, " ")}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell className="text-center font-mono">{rc.occurrence_count}</TableCell>
                        <TableCell className="text-right font-mono">
                          ${rc.impact_amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground max-w-xs">
                          {rc.suggested_fix}
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!rootCauses || rootCauses.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                          No root cause patterns identified
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 4: Optimization Proposals */}
        <TabsContent value="optimization">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="size-5" />
                AI-Generated Optimization Proposals
              </CardTitle>
              <CardDescription>
                Data-driven suggestions to improve touchless rate and reduce exceptions
              </CardDescription>
            </CardHeader>
            <CardContent>
              {proposalsLoading ? (
                <TableSkeleton rows={4} cols={5} />
              ) : (
                <div className="space-y-4">
                  {proposals?.map((p) => (
                    <div key={p.id} className="border rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium">{p.title}</h4>
                          <Badge variant="secondary" className={priorityColors[p.priority]}>
                            {p.priority}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{p.category.replace(/_/g, " ")}</Badge>
                          <Badge variant="outline">Effort: {p.effort}</Badge>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground">{p.description}</p>
                      <div className="flex items-center gap-2 text-sm">
                        <ArrowUpRight className="size-4 text-emerald-500" />
                        <span className="font-medium text-emerald-600 dark:text-emerald-400">
                          Projected Impact: {p.projected_impact}
                        </span>
                      </div>
                    </div>
                  ))}
                  {(!proposals || proposals.length === 0) && (
                    <p className="text-center text-muted-foreground py-8">No optimization proposals generated yet</p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
