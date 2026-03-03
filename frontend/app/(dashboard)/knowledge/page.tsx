"use client"

import * as React from "react"
import {
  BookOpen,
  FileText,
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Search,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Building2,
  Scale,
  FileCheck,
} from "lucide-react"

import {
  useKnowledgeSummary,
  useKnowledgeDocuments,
  useKnowledgeRules,
  useApproveRule,
  useRejectRule,
  type PolicyRuleInfo,
} from "@/hooks/use-knowledge"
import { KpiCardSkeleton, TableSkeleton } from "@/components/loading-skeleton"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const ruleTypeLabels: Record<string, string> = {
  approval_threshold: "Approval Threshold",
  matching_requirement: "Matching Requirement",
  exception_handling: "Exception Handling",
  payment_terms: "Payment Terms",
  vendor_management: "Vendor Management",
  audit_control: "Audit Control",
  kpi_target: "KPI Target",
  invoice_validation: "Invoice Validation",
  duplicate_prevention: "Duplicate Prevention",
  tax_treatment: "Tax Treatment",
  escalation: "Escalation",
  price_tolerance: "Price Tolerance",
  surcharge_allowance: "Surcharge Allowance",
  volume_discount: "Volume Discount",
  penalty_clause: "Penalty Clause",
  audit_finding: "Audit Finding",
  control_gap: "Control Gap",
  delivery_terms: "Delivery Terms",
}

const ruleTypeColors: Record<string, string> = {
  approval_threshold: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
  matching_requirement: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  exception_handling: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  payment_terms: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  price_tolerance: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400",
  surcharge_allowance: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
  volume_discount: "bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-400",
  penalty_clause: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  audit_finding: "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400",
  duplicate_prevention: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400",
  kpi_target: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
}

const docTypeIcons: Record<string, React.ElementType> = {
  policy: Shield,
  contract: Building2,
  audit_report: Scale,
  match_report: FileCheck,
}

const statusColors: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  approved: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
  rejected: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color =
    pct >= 90 ? "bg-emerald-500" : pct >= 70 ? "bg-amber-500" : "bg-red-500"
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden max-w-[60px]">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-muted-foreground">{pct}%</span>
    </div>
  )
}

function RuleRow({
  rule,
  onApprove,
  onReject,
}: {
  rule: PolicyRuleInfo
  onApprove: (id: string) => void
  onReject: (id: string) => void
}) {
  const [expanded, setExpanded] = React.useState(false)

  return (
    <>
      <TableRow
        className="cursor-pointer hover:bg-muted/50"
        onClick={() => setExpanded(!expanded)}
      >
        <TableCell className="w-8">
          {expanded ? (
            <ChevronDown className="size-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="size-4 text-muted-foreground" />
          )}
        </TableCell>
        <TableCell>
          <Badge
            variant="secondary"
            className={
              ruleTypeColors[rule.rule_type] ||
              "bg-slate-100 text-slate-800 dark:bg-slate-900/30 dark:text-slate-400"
            }
          >
            {ruleTypeLabels[rule.rule_type] || rule.rule_type}
          </Badge>
        </TableCell>
        <TableCell className="max-w-[400px]">
          <p className="text-sm truncate">{rule.source_text}</p>
        </TableCell>
        <TableCell>
          <ConfidenceBar value={rule.confidence} />
        </TableCell>
        <TableCell>
          <Badge variant="secondary" className={statusColors[rule.status] || ""}>
            {rule.status}
          </Badge>
        </TableCell>
        <TableCell>
          <span className="text-xs text-muted-foreground">{rule.document}</span>
        </TableCell>
        <TableCell onClick={(e) => e.stopPropagation()}>
          {rule.status === "pending" && (
            <div className="flex gap-1">
              <Button
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                onClick={() => onApprove(rule.id)}
              >
                <CheckCircle className="size-3.5 mr-1" />
                Approve
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                onClick={() => onReject(rule.id)}
              >
                <XCircle className="size-3.5 mr-1" />
                Reject
              </Button>
            </div>
          )}
        </TableCell>
      </TableRow>
      {expanded && (
        <TableRow className="bg-muted/30">
          <TableCell colSpan={7}>
            <div className="py-2 px-4 space-y-2">
              <div className="grid grid-cols-2 gap-4 text-sm">
                {rule.conditions && (
                  <div>
                    <span className="font-medium text-muted-foreground">Conditions:</span>
                    <pre className="mt-1 text-xs bg-background rounded p-2 overflow-x-auto">
                      {JSON.stringify(rule.conditions, null, 2)}
                    </pre>
                  </div>
                )}
                {rule.action && (
                  <div>
                    <span className="font-medium text-muted-foreground">Action:</span>
                    <pre className="mt-1 text-xs bg-background rounded p-2 overflow-x-auto">
                      {JSON.stringify(rule.action, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
              <div className="flex gap-4 text-xs text-muted-foreground">
                <span>Source: {rule.document_type}</span>
                <span>Document: {rule.document}</span>
              </div>
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  )
}

export default function KnowledgePage() {
  const { data: summary, isLoading: summaryLoading } = useKnowledgeSummary()
  const { data: documents, isLoading: docsLoading } = useKnowledgeDocuments()
  const [ruleFilter, setRuleFilter] = React.useState<string | undefined>(undefined)
  const [statusFilter, setStatusFilter] = React.useState<string | undefined>(undefined)
  const { data: rules, isLoading: rulesLoading } = useKnowledgeRules({
    rule_type: ruleFilter,
    status: statusFilter,
  })
  const approveMutation = useApproveRule()
  const rejectMutation = useRejectRule()

  const handleApprove = (id: string) => approveMutation.mutate(id)
  const handleReject = (id: string) => rejectMutation.mutate({ ruleId: id })

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      {summaryLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <KpiCardSkeleton key={i} />
          ))}
        </div>
      ) : summary ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Documents Parsed</p>
                  <p className="text-2xl font-bold">{summary.total_documents}</p>
                </div>
                <FileText className="size-8 text-blue-500 opacity-80" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Rules</p>
                  <p className="text-2xl font-bold">{summary.total_rules}</p>
                </div>
                <BookOpen className="size-8 text-purple-500 opacity-80" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Pending Review</p>
                  <p className="text-2xl font-bold">{summary.pending_review}</p>
                </div>
                <Clock className="size-8 text-amber-500 opacity-80" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Approved</p>
                  <p className="text-2xl font-bold">{summary.approved_rules}</p>
                </div>
                <CheckCircle className="size-8 text-emerald-500 opacity-80" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Avg Confidence</p>
                  <p className="text-2xl font-bold">{Math.round(summary.avg_confidence * 100)}%</p>
                </div>
                <Sparkles className="size-8 text-cyan-500 opacity-80" />
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}

      <Tabs defaultValue="rules" className="space-y-4">
        <TabsList>
          <TabsTrigger value="rules">Extracted Rules</TabsTrigger>
          <TabsTrigger value="documents">Source Documents</TabsTrigger>
          <TabsTrigger value="breakdown">Rule Breakdown</TabsTrigger>
        </TabsList>

        {/* Rules Tab */}
        <TabsContent value="rules" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Policy Rules & Contract Terms</CardTitle>
                  <CardDescription>
                    AI-extracted rules from policy documents, supplier contracts, and audit reports
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <select
                    className="text-sm border rounded-md px-2 py-1 bg-background"
                    value={ruleFilter || ""}
                    onChange={(e) => setRuleFilter(e.target.value || undefined)}
                  >
                    <option value="">All Types</option>
                    {summary?.rules_by_type &&
                      Object.keys(summary.rules_by_type).map((t) => (
                        <option key={t} value={t}>
                          {ruleTypeLabels[t] || t} ({summary.rules_by_type[t]})
                        </option>
                      ))}
                  </select>
                  <select
                    className="text-sm border rounded-md px-2 py-1 bg-background"
                    value={statusFilter || ""}
                    onChange={(e) => setStatusFilter(e.target.value || undefined)}
                  >
                    <option value="">All Statuses</option>
                    <option value="pending">Pending</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                  </select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {rulesLoading ? (
                <TableSkeleton />
              ) : rules && rules.length > 0 ? (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-8" />
                        <TableHead>Type</TableHead>
                        <TableHead>Rule</TableHead>
                        <TableHead className="w-[100px]">Confidence</TableHead>
                        <TableHead className="w-[100px]">Status</TableHead>
                        <TableHead>Source</TableHead>
                        <TableHead className="w-[160px]">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {rules.map((rule) => (
                        <RuleRow
                          key={rule.id}
                          rule={rule}
                          onApprove={handleApprove}
                          onReject={handleReject}
                        />
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <BookOpen className="size-12 mx-auto mb-4 opacity-30" />
                  <p>No rules found. Parse documents to populate the knowledge base.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="documents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Parsed Documents</CardTitle>
              <CardDescription>
                Source documents that have been parsed to extract business rules
              </CardDescription>
            </CardHeader>
            <CardContent>
              {docsLoading ? (
                <TableSkeleton />
              ) : documents && documents.length > 0 ? (
                <div className="grid gap-3">
                  {documents.map((doc) => {
                    const Icon = docTypeIcons[doc.document_type] || FileText
                    return (
                      <div
                        key={doc.id}
                        className="flex items-center justify-between rounded-lg border p-4 hover:bg-muted/50"
                      >
                        <div className="flex items-center gap-3">
                          <div className="flex items-center justify-center size-10 rounded-lg bg-muted">
                            <Icon className="size-5 text-muted-foreground" />
                          </div>
                          <div>
                            <p className="font-medium text-sm">{doc.filename}</p>
                            <p className="text-xs text-muted-foreground">
                              {doc.document_type} &middot; Uploaded{" "}
                              {doc.uploaded_at
                                ? new Date(doc.uploaded_at).toLocaleDateString()
                                : "unknown"}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <p className="text-lg font-semibold">{doc.rules_count}</p>
                            <p className="text-xs text-muted-foreground">rules</p>
                          </div>
                          <Badge
                            variant="secondary"
                            className={
                              doc.extraction_status === "completed"
                                ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400"
                                : doc.extraction_status === "failed"
                                  ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                                  : "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400"
                            }
                          >
                            {doc.extraction_status}
                          </Badge>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <FileText className="size-12 mx-auto mb-4 opacity-30" />
                  <p>No documents have been parsed yet.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Breakdown Tab */}
        <TabsContent value="breakdown" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Rules by Type</CardTitle>
              </CardHeader>
              <CardContent>
                {summary?.rules_by_type ? (
                  <div className="space-y-2">
                    {Object.entries(summary.rules_by_type)
                      .sort(([, a], [, b]) => (b as number) - (a as number))
                      .map(([type, count]) => (
                        <div key={type} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge
                              variant="secondary"
                              className={
                                ruleTypeColors[type] ||
                                "bg-slate-100 text-slate-800 dark:bg-slate-900/30 dark:text-slate-400"
                              }
                            >
                              {ruleTypeLabels[type] || type}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                              <div
                                className="h-full bg-primary rounded-full"
                                style={{
                                  width: `${
                                    ((count as number) / summary.total_rules) * 100
                                  }%`,
                                }}
                              />
                            </div>
                            <span className="text-sm font-medium w-6 text-right">
                              {count as number}
                            </span>
                          </div>
                        </div>
                      ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-sm">No data</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Documents by Type</CardTitle>
              </CardHeader>
              <CardContent>
                {summary?.documents_by_type ? (
                  <div className="space-y-3">
                    {Object.entries(summary.documents_by_type).map(([type, count]) => {
                      const Icon = docTypeIcons[type] || FileText
                      return (
                        <div key={type} className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                          <div className="flex items-center justify-center size-10 rounded-lg bg-background">
                            <Icon className="size-5 text-muted-foreground" />
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-sm capitalize">
                              {type.replace("_", " ")}
                            </p>
                          </div>
                          <p className="text-2xl font-bold">{count as number}</p>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-sm">No data</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
