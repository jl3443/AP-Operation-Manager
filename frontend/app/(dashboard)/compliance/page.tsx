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
  FileCheck,
  BarChart3,
  FileText,
  Download,
  Activity,
} from "lucide-react"

import {
  useControlMap,
  useComplianceGaps,
  useRootCauses,
  useOptimizationProposals,
  useControlTests,
  useComplianceScoring,
  useAuditPack,
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

const gradeColors: Record<string, string> = {
  A: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
  B: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  C: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  F: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
}

function ScoreBar({ score }: { score: number }) {
  const color =
    score >= 90
      ? "bg-emerald-500"
      : score >= 75
        ? "bg-blue-500"
        : score >= 60
          ? "bg-amber-500"
          : "bg-red-500"
  return (
    <div className="flex items-center gap-2 w-full">
      <div className="h-2 flex-1 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs font-mono w-12 text-right">{score}%</span>
    </div>
  )
}

export default function CompliancePage() {
  const { data: controls, isLoading: controlsLoading } = useControlMap()
  const { data: gaps, isLoading: gapsLoading } = useComplianceGaps()
  const { data: rootCauses, isLoading: rcLoading } = useRootCauses()
  const { data: proposals, isLoading: proposalsLoading } = useOptimizationProposals()
  const { data: controlTests, isLoading: testsLoading } = useControlTests()
  const { data: scoring, isLoading: scoringLoading } = useComplianceScoring()
  const { data: auditPack, isLoading: auditLoading } = useAuditPack()

  const activeControls = controls?.filter((c) => c.implementation_status === "active").length ?? 0
  const totalControls = controls?.length ?? 0
  const openGaps = gaps?.filter((g) => g.status === "open").length ?? 0
  const testsPassing = controlTests?.filter((t) => t.result === "pass").length ?? 0
  const totalTests = controlTests?.length ?? 0

  return (
    <div className="space-y-6">
      <p className="text-muted-foreground">
        Audit compliance, control testing, scoring, gap analysis, and audit pack generation.
      </p>

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
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
                <p className="text-sm text-muted-foreground">Tests Passing</p>
                <p className="text-2xl font-bold">{testsPassing}/{totalTests}</p>
              </div>
              <FileCheck className="size-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg Score</p>
                <p className="text-2xl font-bold">{scoring?.avg_score ?? 0}%</p>
              </div>
              <BarChart3 className="size-8 text-violet-500" />
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
                <p className="text-sm text-muted-foreground">Audit Trail</p>
                <p className="text-2xl font-bold">{auditPack?.audit_trail?.total_entries ?? 0}</p>
              </div>
              <FileText className="size-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="control-tests" className="space-y-4">
        <TabsList className="flex flex-wrap">
          <TabsTrigger value="control-tests">Control Tests</TabsTrigger>
          <TabsTrigger value="scoring">Compliance Scoring</TabsTrigger>
          <TabsTrigger value="controls">Control Mapping</TabsTrigger>
          <TabsTrigger value="gaps">Gap Analysis</TabsTrigger>
          <TabsTrigger value="audit-pack">Audit Pack</TabsTrigger>
          <TabsTrigger value="root-causes">Root Causes</TabsTrigger>
          <TabsTrigger value="optimization">Optimization</TabsTrigger>
        </TabsList>

        {/* Tab: Control Tests */}
        <TabsContent value="control-tests">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileCheck className="size-5" />
                Automated Control Test Results
              </CardTitle>
              <CardDescription>
                Live tests verifying AP controls are working as designed
              </CardDescription>
            </CardHeader>
            <CardContent>
              {testsLoading ? (
                <TableSkeleton rows={7} cols={5} />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Control</TableHead>
                      <TableHead>Test Description</TableHead>
                      <TableHead>Expected</TableHead>
                      <TableHead>Actual</TableHead>
                      <TableHead>Result</TableHead>
                      <TableHead>Severity</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {controlTests?.map((t) => (
                      <TableRow key={t.control_id}>
                        <TableCell>
                          <div>
                            <p className="font-mono text-xs">{t.control_id}</p>
                            <p className="text-sm font-medium">{t.control_name}</p>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm max-w-xs">{t.test_description}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">{t.expected}</TableCell>
                        <TableCell className="text-xs font-mono">{t.actual}</TableCell>
                        <TableCell>
                          {t.result === "pass" ? (
                            <Badge variant="secondary" className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">
                              <CheckCircle className="size-3 mr-1" /> Pass
                            </Badge>
                          ) : (
                            <Badge variant="secondary" className="bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
                              <XCircle className="size-3 mr-1" /> Fail
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className={severityColors[t.severity]}>
                            {t.severity}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Compliance Scoring */}
        <TabsContent value="scoring">
          <div className="space-y-4">
            {/* Score Distribution */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {["A", "B", "C", "F"].map((grade) => (
                <Card key={grade}>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Grade {grade}</p>
                        <p className="text-2xl font-bold">
                          {scoring?.grade_distribution?.[grade] ?? 0}
                        </p>
                      </div>
                      <div className={`size-10 rounded-full flex items-center justify-center text-lg font-bold ${gradeColors[grade]}`}>
                        {grade}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Individual Scores */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="size-5" />
                  Invoice Compliance Scores
                </CardTitle>
                <CardDescription>
                  Each invoice scored against 6 compliance checks ({scoring?.count ?? 0} invoices, avg {scoring?.avg_score ?? 0}%)
                </CardDescription>
              </CardHeader>
              <CardContent>
                {scoringLoading ? (
                  <TableSkeleton rows={8} cols={5} />
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Invoice</TableHead>
                        <TableHead>Score</TableHead>
                        <TableHead>Grade</TableHead>
                        <TableHead className="w-[200px]">Progress</TableHead>
                        <TableHead>Checks</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {scoring?.scores?.map((s) => (
                        <TableRow key={s.invoice_id}>
                          <TableCell className="font-mono text-sm">{s.invoice_number}</TableCell>
                          <TableCell className="font-mono">{s.total_points}/{s.max_points}</TableCell>
                          <TableCell>
                            <Badge variant="secondary" className={gradeColors[s.grade]}>
                              {s.grade}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <ScoreBar score={s.compliance_score} />
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              {s.checks.map((c, i) => (
                                <div
                                  key={i}
                                  title={`${c.check}: ${c.status} (${c.points}/${c.max})`}
                                  className={`size-5 rounded-sm flex items-center justify-center text-[10px] ${
                                    c.status === "pass"
                                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                                      : c.status === "partial"
                                        ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                                        : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                                  }`}
                                >
                                  {c.status === "pass" ? "\u2713" : c.status === "partial" ? "~" : "\u2717"}
                                </div>
                              ))}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab: Control Mapping */}
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

        {/* Tab: Gap Analysis */}
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

        {/* Tab: Audit Pack */}
        <TabsContent value="audit-pack">
          <div className="space-y-4">
            {auditLoading ? (
              <TableSkeleton rows={6} cols={4} />
            ) : auditPack ? (
              <>
                {/* Executive Summary */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="size-5" />
                      Audit Pack — Executive Summary
                    </CardTitle>
                    <CardDescription>
                      Generated {new Date(auditPack.generated_at).toLocaleString()} | Period: {auditPack.period}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                      <div className="border rounded-lg p-4 space-y-1">
                        <p className="text-xs text-muted-foreground">Total Invoices</p>
                        <p className="text-2xl font-bold">{auditPack.executive_summary.total_invoices}</p>
                      </div>
                      <div className="border rounded-lg p-4 space-y-1">
                        <p className="text-xs text-muted-foreground">Touchless Rate</p>
                        <p className="text-2xl font-bold">{auditPack.executive_summary.touchless_rate}%</p>
                      </div>
                      <div className="border rounded-lg p-4 space-y-1">
                        <p className="text-xs text-muted-foreground">Avg Compliance</p>
                        <p className="text-2xl font-bold">{auditPack.executive_summary.avg_compliance_score}%</p>
                      </div>
                      <div className="border rounded-lg p-4 space-y-1">
                        <p className="text-xs text-muted-foreground">Controls Passed</p>
                        <p className="text-2xl font-bold">
                          {auditPack.executive_summary.controls_passed}/{auditPack.executive_summary.controls_tested}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Control Test Summary */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Control Test Summary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {auditPack.control_test_results.map((t) => (
                        <div key={t.control_id} className="flex items-center gap-3 py-2 border-b last:border-0">
                          {t.result === "pass" ? (
                            <CheckCircle className="size-4 text-emerald-500 shrink-0" />
                          ) : (
                            <XCircle className="size-4 text-red-500 shrink-0" />
                          )}
                          <span className="font-mono text-xs text-muted-foreground w-16">{t.control_id}</span>
                          <span className="text-sm flex-1">{t.control_name}</span>
                          <span className="text-xs text-muted-foreground">{t.actual}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Open Exceptions */}
                {auditPack.open_exceptions.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center gap-2">
                        <AlertTriangle className="size-4 text-amber-500" />
                        Open Exceptions ({auditPack.open_exceptions.length})
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Invoice</TableHead>
                            <TableHead>Exception Type</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Amount</TableHead>
                            <TableHead>Created</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {auditPack.open_exceptions.slice(0, 20).map((exc, i) => (
                            <TableRow key={i}>
                              <TableCell className="font-mono text-sm">{exc.invoice_number}</TableCell>
                              <TableCell className="text-sm">{exc.exception_type}</TableCell>
                              <TableCell>
                                <Badge variant="secondary" className={gapStatusColors[exc.status] ?? ""}>
                                  {exc.status}
                                </Badge>
                              </TableCell>
                              <TableCell className="font-mono">${Number(exc.amount).toLocaleString()}</TableCell>
                              <TableCell className="text-xs text-muted-foreground">
                                {exc.created_at ? new Date(exc.created_at).toLocaleDateString() : "—"}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                )}

                {/* Audit Trail & Knowledge Base */}
                <div className="grid gap-4 sm:grid-cols-2">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Audit Trail Summary</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold mb-3">{auditPack.audit_trail.total_entries} entries</p>
                      <div className="space-y-2">
                        {Object.entries(auditPack.audit_trail.by_action).map(([action, count]) => (
                          <div key={action} className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">{action}</span>
                            <span className="font-mono">{count as number}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Knowledge Base Coverage</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Documents Parsed</span>
                          <span className="font-bold">{(auditPack.knowledge_base as Record<string, number>)?.documents_parsed ?? 0}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Total Rules</span>
                          <span className="font-bold">{(auditPack.knowledge_base as Record<string, number>)?.total_rules ?? 0}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Approved Rules</span>
                          <span className="font-bold">{(auditPack.knowledge_base as Record<string, number>)?.approved ?? 0}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Avg Confidence</span>
                          <span className="font-bold">
                            {((auditPack.knowledge_base as Record<string, number>)?.avg_confidence * 100)?.toFixed(0) ?? 0}%
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </>
            ) : (
              <p className="text-center text-muted-foreground py-8">Failed to load audit pack data</p>
            )}
          </div>
        </TabsContent>

        {/* Tab: Root Cause Analysis */}
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

        {/* Tab: Optimization Proposals */}
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
