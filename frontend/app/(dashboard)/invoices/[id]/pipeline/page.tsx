"use client"

import * as React from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronDown,
  ChevronRight,
  Zap,
  Eye,
  Brain,
  GitMerge,
  ShieldCheck,
  ShieldAlert,
  ShieldQuestion,
  Clock,
  AlertTriangle,
  FileText,
  Package,
  Truck,
  Check,
  X,
  RefreshCw,
  Users,
  Sparkles,
  RotateCcw,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { CompactStep } from "@/components/resolution/compact-step"
import { ApprovalCheckpoint } from "@/components/resolution/approval-checkpoint"
import { cn } from "@/lib/utils"
import {
  useRunPipelineStream,
  type StreamingPipelineStep,
} from "@/hooks/use-invoices"
import { useRerunMatch } from "@/hooks/use-exceptions"
import { toast } from "sonner"
import type { AutomationAction, ActionStatus } from "@/lib/types"

// ── Step config ──────────────────────────────────────────────────────────────

const STEP_CONFIG: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  ocr_extraction: { icon: <Eye className="size-4" />, color: "text-blue-500", label: "OCR" },
  vendor_match: { icon: <Users className="size-4" />, color: "text-cyan-500", label: "Vendor" },
  classification: { icon: <Brain className="size-4" />, color: "text-violet-500", label: "Classify" },
  three_way_match: { icon: <GitMerge className="size-4" />, color: "text-amber-500", label: "Match" },
  exception_resolution: { icon: <Sparkles className="size-4" />, color: "text-rose-500", label: "Resolve" },
  approval_recommendation: { icon: <ShieldCheck className="size-4" />, color: "text-emerald-500", label: "Approve" },
}

// ── Score Gauge ──────────────────────────────────────────────────────────────

function ScoreGauge({ score, size = 80 }: { score: number; size?: number }) {
  const radius = (size - 8) / 2
  const circumference = 2 * Math.PI * radius
  const progress = (score / 100) * circumference
  const color = score >= 90 ? "text-green-500" : score >= 70 ? "text-amber-500" : "text-red-500"
  const strokeColor = score >= 90 ? "stroke-green-500" : score >= 70 ? "stroke-amber-500" : "stroke-red-500"

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="currentColor"
          className="text-muted/30" strokeWidth={4} />
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" strokeWidth={4}
          className={strokeColor} strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={circumference - progress}
          style={{ transition: "stroke-dashoffset 1s ease-in-out" }} />
      </svg>
      <span className={`absolute text-sm font-bold ${color}`}>{Math.round(score)}%</span>
    </div>
  )
}

// ── Horizontal Stepper ──────────────────────────────────────────────────────

function HorizontalStepper({ steps }: { steps: StreamingPipelineStep[] }) {
  return (
    <div className="flex items-center gap-1 w-full">
      {steps.map((step, i) => {
        const cfg = STEP_CONFIG[step.step] || { icon: <Zap className="size-4" />, color: "text-primary", label: step.label }
        const isComplete = step.status === "complete"
        const isError = step.status === "error"
        const isRunning = step.status === "running"

        return (
          <React.Fragment key={step.step}>
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all bg-card border shadow-sm ${
              isRunning ? "ring-2 ring-primary/30" : ""
            }`}>
              <div className={`flex items-center justify-center size-7 rounded-full border-2 transition-colors ${
                isError ? "border-red-500 bg-red-50 dark:bg-red-950" :
                isComplete ? "border-green-500 bg-green-50 dark:bg-green-950" :
                isRunning ? "border-primary bg-primary/10" : "border-muted-foreground/30"
              }`}>
                {isError ? <X className="size-3.5 text-red-500" /> :
                 isComplete ? <Check className="size-3.5 text-green-600" /> :
                 isRunning ? <Loader2 className="size-3.5 text-primary animate-spin" /> :
                 <span className="text-xs font-medium text-muted-foreground">{i + 1}</span>}
              </div>
              <div className="hidden sm:block">
                <p className="text-xs font-medium leading-none">{cfg.label}</p>
                {step.duration_ms != null && (
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    {step.duration_ms < 1000 ? `${step.duration_ms}ms` : `${(step.duration_ms / 1000).toFixed(1)}s`}
                  </p>
                )}
                {isRunning && !step.duration_ms && (
                  <p className="text-[10px] text-primary mt-0.5">Running...</p>
                )}
              </div>
            </div>
            {i < steps.length - 1 && (
              <div className={`flex-1 h-0.5 min-w-4 rounded transition-colors ${
                isError ? "bg-red-300" : isComplete ? "bg-green-400" : "bg-muted"
              }`} />
            )}
          </React.Fragment>
        )
      })}
    </div>
  )
}

// ── Match Status Indicator ──────────────────────────────────────────────────

function MatchIndicator({ match, label, value }: { match: boolean; label: string; value?: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted-foreground">{label}</span>
      <div className="flex items-center gap-1.5">
        {value && <span className="font-mono text-xs">{value}</span>}
        {match ? <CheckCircle2 className="size-4 text-green-500" /> : <XCircle className="size-4 text-red-500" />}
      </div>
    </div>
  )
}

// ── Line Comparison Row ─────────────────────────────────────────────────────

function LineComparisonRow({ line }: { line: Record<string, unknown> }) {
  const inv = line.invoice as { quantity: number; unit_price: number; line_total: number } | undefined
  const po = line.po as { quantity: number; unit_price: number; line_total: number } | undefined
  const grn = line.grn as { quantity_received: number; grn_count: number } | undefined
  const checks = line.checks as Record<string, { match: boolean; variance_pct: number }> | undefined
  const status = line.status as string
  const isMatched = status === "matched"

  return (
    <div className={`rounded-lg border p-3 transition-colors ${
      isMatched ? "border-green-200 bg-green-50/50 dark:border-green-900 dark:bg-green-950/30" :
      "border-red-200 bg-red-50/50 dark:border-red-900 dark:bg-red-950/30"
    }`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-muted-foreground">#{line.line as number}</span>
          <span className="text-sm font-medium truncate max-w-48">{(line.description as string) || "Line Item"}</span>
        </div>
        <Badge variant={isMatched ? "default" : "destructive"} className="text-[10px] px-1.5 py-0">
          {isMatched ? "Match" : status}
        </Badge>
      </div>

      {inv && po && (
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-muted-foreground mb-1">
              <FileText className="size-3" /><span className="font-medium">Invoice</span>
            </div>
            <div>Qty: <span className="font-mono font-medium">{inv.quantity}</span></div>
            <div>Price: <span className="font-mono font-medium">${inv.unit_price.toFixed(2)}</span></div>
            <div>Total: <span className="font-mono font-medium">${inv.line_total.toFixed(2)}</span></div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-muted-foreground mb-1">
              <Package className="size-3" /><span className="font-medium">PO</span>
            </div>
            <div className="flex items-center gap-1">
              Qty: <span className="font-mono font-medium">{po.quantity}</span>
              {checks?.quantity && (checks.quantity.match
                ? <CheckCircle2 className="size-3 text-green-500" />
                : <span className="text-red-500 font-medium">({checks.quantity.variance_pct > 0 ? "+" : ""}{checks.quantity.variance_pct}%)</span>)}
            </div>
            <div>Price: <span className="font-mono font-medium">${po.unit_price.toFixed(2)}</span></div>
            <div className="flex items-center gap-1">
              Total: <span className="font-mono font-medium">${po.line_total.toFixed(2)}</span>
              {checks?.amount && (checks.amount.match
                ? <CheckCircle2 className="size-3 text-green-500" />
                : <span className="text-red-500 font-medium">({checks.amount.variance_pct > 0 ? "+" : ""}{checks.amount.variance_pct}%)</span>)}
            </div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-muted-foreground mb-1">
              <Truck className="size-3" /><span className="font-medium">GRN</span>
            </div>
            {grn ? (
              <>
                <div className="flex items-center gap-1">
                  Rcvd: <span className="font-mono font-medium">{grn.quantity_received}</span>
                  {checks?.grn_receipt && (checks.grn_receipt.match
                    ? <CheckCircle2 className="size-3 text-green-500" />
                    : <span className="text-red-500 font-medium">({checks.grn_receipt.variance_pct > 0 ? "+" : ""}{checks.grn_receipt.variance_pct}%)</span>)}
                </div>
                <div className="text-muted-foreground">{grn.grn_count} receipt(s)</div>
              </>
            ) : (
              <div className="text-muted-foreground italic">N/A (2-way)</div>
            )}
          </div>
        </div>
      )}

      {(line.exceptions as Array<{type: string; variance: string}> | undefined)?.length ? (
        <div className="mt-2 pt-2 border-t border-dashed">
          {(line.exceptions as Array<{type: string; variance: string}>).map((exc, i) => (
            <div key={i} className="flex items-center gap-1.5 text-xs text-amber-600 dark:text-amber-400">
              <AlertTriangle className="size-3" />
              <span>{exc.type.replace(/_/g, " ")}: {exc.variance}</span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}

// ── 3-Way Match Visualization ───────────────────────────────────────────────

function MatchVisualization({ output }: { output: Record<string, unknown> }) {
  const score = (output.overall_score as number) || 0
  const matchStatus = (output.match_status as string) || "unknown"
  const matchType = (output.match_type as string) || "unknown"
  const headerMatch = output.header_match as Record<string, unknown> | undefined
  const toleranceConfig = output.tolerance_config as Record<string, unknown> | undefined
  const details = output.details as { lines?: Array<Record<string, unknown>> } | undefined
  const lines = details?.lines || []
  const excCount = (output.exceptions_created as number) || 0

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <ScoreGauge score={score} size={72} />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg font-bold">
              {matchStatus === "matched" ? "Full Match" :
               matchStatus === "tolerance_passed" ? "Matched (Tolerance)" :
               matchStatus === "partial" ? "Partial Match" : "Unmatched"}
            </span>
            <Badge variant="outline" className="text-xs">{matchType.replace("_", "-")}</Badge>
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span>{lines.length} line(s) checked</span>
            <span className="text-muted-foreground/40">|</span>
            <span>{lines.filter(l => l.status === "matched").length} matched</span>
            {excCount > 0 && (
              <>
                <span className="text-muted-foreground/40">|</span>
                <span className="text-amber-500">{excCount} exception(s)</span>
              </>
            )}
          </div>
        </div>
      </div>

      {headerMatch && Object.keys(headerMatch).length > 0 && (
        <Card>
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Header-Level Checks</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-3 space-y-1.5">
            {headerMatch.vendor ? <MatchIndicator match={(headerMatch.vendor as { match: boolean }).match} label="Vendor" /> : null}
            {headerMatch.po_number ? <MatchIndicator match={(headerMatch.po_number as { match: boolean }).match} label="PO Number" value={String((headerMatch.po_number as { value?: string }).value ?? "")} /> : null}
            {headerMatch.currency ? <MatchIndicator match={(headerMatch.currency as { match: boolean }).match} label="Currency" /> : null}
            {headerMatch.invoice_total !== undefined && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Total Amount</span>
                <span className="font-mono text-xs">${(headerMatch.invoice_total as number).toFixed(2)} vs ${(headerMatch.po_total as number).toFixed(2)}</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {(output.tolerance_applied as boolean) && toleranceConfig && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground bg-blue-50 dark:bg-blue-950/30 rounded-lg px-3 py-2">
          <ShieldCheck className="size-3.5 text-blue-500" />
          <span>Tolerance applied &mdash; Amount: {(toleranceConfig.amount_pct as number)}% / ${(toleranceConfig.amount_abs as number).toFixed(0)}, Quantity: {(toleranceConfig.quantity_pct as number)}% <span className="text-muted-foreground/60 ml-1">({(toleranceConfig.scope as string)})</span></span>
        </div>
      )}

      {lines.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Line-Level Comparison</p>
          {lines.map((line, i) => <LineComparisonRow key={i} line={line} />)}
        </div>
      )}
    </div>
  )
}

// ── Exception Resolution Card ───────────────────────────────────────────────

function ExceptionResolutionCard({
  output,
  onRefresh,
}: {
  output: Record<string, unknown>
  onRefresh: () => void
}) {
  const plans = (output.plans as Array<Record<string, unknown>>) || []
  const rerunMatch = useRerunMatch()

  if (plans.length === 0) {
    return <p className="text-sm text-muted-foreground">No resolution plans generated.</p>
  }

  return (
    <div className="space-y-4">
      {plans.map((planData) => {
        if (planData.error) {
          return (
            <div key={planData.exception_id as string} className="text-sm text-red-500">
              Failed to generate plan for {planData.exception_type as string}: {planData.error as string}
            </div>
          )
        }

        const actions = (planData.actions as Array<Record<string, unknown>>) || []
        const sortedActions = [...actions].sort((a, b) => {
          const numA = parseInt(String(a.step_id).replace(/\D/g, "") || "0")
          const numB = parseInt(String(b.step_id).replace(/\D/g, "") || "0")
          return numA - numB
        })

        // Convert to AutomationAction-like objects for CompactStep
        const typedActions: AutomationAction[] = sortedActions.map((a) => ({
          id: a.id as string,
          step_id: a.step_id as string,
          action_type: a.action_type as string,
          status: a.status as ActionStatus,
          requires_human_approval: a.requires_human_approval as boolean,
          params_json: (a.params_json as Record<string, unknown>) || {},
          result_json: (a.result_json as Record<string, unknown>) || null,
          expected_result: a.expected_result as string | undefined,
          error_message: a.error_message as string | undefined,
        } as AutomationAction))

        const blockingAction = typedActions.find((a) => a.status === "awaiting_approval")
        const completedActions = typedActions.filter((a) => a.status === "done" || a.status === "skipped")
        const pendingActions = typedActions.filter((a) => a.status === "pending")
        const failedActions = typedActions.filter((a) => a.status === "failed")
        const allDone = completedActions.length === typedActions.length && typedActions.length > 0

        return (
          <Card key={planData.plan_id as string} className="border-l-4 border-l-rose-400">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    {(planData.exception_type as string).replace(/_/g, " ")}
                  </Badge>
                  <Badge className={cn("text-[10px]",
                    planData.plan_status === "completed" ? "bg-green-100 text-green-700" :
                    planData.plan_status === "executing" ? "bg-amber-100 text-amber-700" :
                    "bg-slate-100 text-slate-700"
                  )}>
                    {(planData.plan_status as string).replace(/_/g, " ")}
                  </Badge>
                </div>
                {planData.confidence != null && (
                  <span className={cn("text-sm font-bold",
                    (planData.confidence as number) >= 0.8 ? "text-green-600" : "text-amber-600"
                  )}>
                    {Math.round((planData.confidence as number) * 100)}%
                  </span>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {planData.diagnosis ? (
                <div className="flex items-start gap-2">
                  <Sparkles className="size-3.5 text-violet-500 mt-0.5 shrink-0" />
                  <p className="text-sm leading-relaxed">{String(planData.diagnosis)}</p>
                </div>
              ) : null}

              {/* Progress bar */}
              {typedActions.length > 0 && (
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className={cn("h-full rounded-full transition-all duration-500",
                      allDone ? "bg-green-500" : "bg-violet-500"
                    )}
                    style={{ width: `${Math.round((completedActions.length / typedActions.length) * 100)}%` }}
                  />
                </div>
              )}

              {/* Completed steps */}
              {completedActions.length > 0 && (
                <div className="pt-1">
                  {completedActions.map((action, idx) => (
                    <CompactStep
                      key={action.id}
                      action={action}
                      isLast={idx === completedActions.length - 1 && !blockingAction}
                    />
                  ))}
                </div>
              )}

              {/* Blocking step — approval checkpoint */}
              {blockingAction && (
                <ApprovalCheckpoint
                  action={blockingAction}
                  exceptionId={planData.exception_id as string}
                  onComplete={onRefresh}
                />
              )}

              {/* Pending steps (shown dimmed after blocking action) */}
              {pendingActions.length > 0 && (
                <div className="pt-1 opacity-50">
                  {pendingActions.map((action, idx) => (
                    <CompactStep
                      key={action.id}
                      action={action}
                      isLast={idx === pendingActions.length - 1}
                    />
                  ))}
                </div>
              )}

              {/* Failed steps */}
              {failedActions.length > 0 && (
                <div className="pt-1">
                  {failedActions.map((action, idx) => (
                    <CompactStep
                      key={action.id}
                      action={action}
                      isLast={idx === failedActions.length - 1}
                    />
                  ))}
                </div>
              )}

              {/* View Details link */}
              <div className="pt-1">
                <Link
                  href={`/exceptions/${planData.exception_id as string}`}
                  className="text-xs text-violet-600 hover:text-violet-800 hover:underline"
                >
                  View Full Details &rarr;
                </Link>
              </div>

              {/* All done → Re-run match */}
              {allDone && (
                <div className="text-center space-y-2 py-2">
                  <p className="text-xs text-green-600 font-medium">All resolution steps completed</p>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      rerunMatch.mutate(planData.exception_id as string, {
                        onSuccess: (result: Record<string, unknown>) => {
                          if (result.exception_resolved) {
                            toast.success("Match passed! Exception resolved.")
                          } else {
                            toast.info(`Match: ${result.match_status} (score: ${result.overall_score}%)`)
                          }
                          onRefresh()
                        },
                        onError: (err) => toast.error(String(err)),
                      })
                    }}
                    disabled={rerunMatch.isPending}
                  >
                    {rerunMatch.isPending ? <Loader2 className="size-3 mr-1.5 animate-spin" /> : <RotateCcw className="size-3 mr-1.5" />}
                    Re-Run 3-Way Match
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        )
      })}

      {/* Truncation note */}
      {output.truncated ? (
        <p className="text-xs text-muted-foreground text-center py-2">
          Showing {plans.length} of {Number(output.total_exceptions)} exceptions.{" "}
          <Link href="/exceptions" className="text-violet-600 hover:underline">View all exceptions</Link>
        </p>
      ) : null}
    </div>
  )
}

// ── JSON Fallback ───────────────────────────────────────────────────────────

function JsonBlock({ data, expanded }: { data: Record<string, unknown>; expanded: boolean }) {
  const json = JSON.stringify(data, null, 2)
  return (
    <pre className={`text-xs font-mono bg-muted/60 rounded-lg p-4 overflow-auto transition-all ${
      expanded ? "max-h-[600px]" : "max-h-56"
    } whitespace-pre text-foreground/80 leading-relaxed`}>
      {json}
    </pre>
  )
}

// ── Individual step card ─────────────────────────────────────────────────────

function StepCard({
  step,
  index,
  onRefresh,
}: {
  step: StreamingPipelineStep
  index: number
  onRefresh: () => void
}) {
  const [expanded, setExpanded] = React.useState(step.step === "three_way_match")
  const cfg = STEP_CONFIG[step.step] || { icon: <Zap className="size-4" />, color: "text-primary", label: step.label }
  const isMatchStep = step.step === "three_way_match"
  const isExceptionStep = step.step === "exception_resolution"
  const isRunning = step.status === "running"

  return (
    <Card className={cn(
      "overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-300",
      isRunning && "border-primary/30 bg-primary/5"
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`flex items-center justify-center size-8 rounded-full border-2 ${
              step.status === "complete"
                ? "border-green-500 bg-green-50 dark:bg-green-950"
                : step.status === "error"
                ? "border-red-500 bg-red-50 dark:bg-red-950"
                : "border-primary bg-primary/10"
            }`}>
              {step.status === "complete" ? (
                <CheckCircle2 className="size-4 text-green-600" />
              ) : step.status === "error" ? (
                <XCircle className="size-4 text-red-500" />
              ) : (
                <Loader2 className="size-4 text-primary animate-spin" />
              )}
            </div>
            <div>
              <p className="text-sm font-semibold">
                <span className="text-muted-foreground mr-1">Step {index + 1}:</span>
                {step.label}
              </p>
              <p className={`text-xs ${cfg.color} flex items-center gap-1`}>
                {cfg.icon}
                {step.agent || "Processing..."}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {step.duration_ms != null && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="size-3" />
                {step.duration_ms < 1000 ? `${step.duration_ms}ms` : `${(step.duration_ms / 1000).toFixed(1)}s`}
              </span>
            )}
            <Badge variant={
              step.status === "complete" ? "default" :
              step.status === "error" ? "destructive" : "secondary"
            } className="text-xs">
              {isRunning ? "running" : step.status}
            </Badge>
          </div>
        </div>
      </CardHeader>

      {/* Only show content when step is complete or error */}
      {step.status === "running" && (
        <CardContent className="pt-0">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Processing...
          </div>
        </CardContent>
      )}

      {step.status === "error" && (
        <CardContent className="pt-0">
          <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 rounded-lg p-3">
            <AlertTriangle className="size-4 shrink-0" />
            {step.error ?? "Unknown error"}
          </div>
        </CardContent>
      )}

      {step.status === "complete" && step.output && (
        <CardContent className="pt-0">
          {isMatchStep ? (
            <MatchVisualization output={step.output} />
          ) : isExceptionStep ? (
            <ExceptionResolutionCard output={step.output} onRefresh={onRefresh} />
          ) : (
            <>
              <JsonBlock data={step.output} expanded={expanded} />
              <Button variant="ghost" size="sm" className="mt-2 text-xs text-muted-foreground"
                onClick={() => setExpanded((e) => !e)}>
                {expanded ? (
                  <><ChevronDown className="size-3 mr-1" /> Collapse</>
                ) : (
                  <><ChevronRight className="size-3 mr-1" /> Show full output</>
                )}
              </Button>
            </>
          )}
        </CardContent>
      )}
    </Card>
  )
}

// ── Recommendation card ──────────────────────────────────────────────────────

function RecommendationCard({
  recommendation,
  reasoning,
  riskFactors,
  totalDuration,
  finalStatus,
  invoiceId,
}: {
  recommendation: string | null
  reasoning?: string
  riskFactors?: string[]
  totalDuration: number
  finalStatus: string
  invoiceId: string
}) {
  const rec = recommendation
  const colorMap = {
    approve: {
      bg: "bg-green-50 dark:bg-green-950", border: "border-green-400",
      text: "text-green-700 dark:text-green-300", badge: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
      icon: <ShieldCheck className="size-6 text-green-600" />, label: "APPROVED",
    },
    review: {
      bg: "bg-amber-50 dark:bg-amber-950", border: "border-amber-400",
      text: "text-amber-700 dark:text-amber-300", badge: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-100",
      icon: <ShieldQuestion className="size-6 text-amber-600" />, label: "NEEDS REVIEW",
    },
    reject: {
      bg: "bg-red-50 dark:bg-red-950", border: "border-red-400",
      text: "text-red-700 dark:text-red-300", badge: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
      icon: <ShieldAlert className="size-6 text-red-600" />, label: "REJECTED",
    },
  }
  const style = colorMap[rec as keyof typeof colorMap] || colorMap.review

  return (
    <Card className={`border-2 ${style.border} ${style.bg} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
      <CardContent className="pt-6 pb-6">
        <div className="flex items-start gap-4">
          {style.icon}
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className={`text-lg font-bold ${style.text}`}>{style.label}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${style.badge}`}>AI Recommendation</span>
            </div>
            {reasoning && <p className="text-sm text-foreground/80 mb-3 leading-relaxed">&ldquo;{reasoning}&rdquo;</p>}
            {riskFactors && riskFactors.length > 0 ? (
              <div className="mb-3">
                <p className="text-xs font-medium text-muted-foreground mb-1">Risk factors:</p>
                <ul className="text-sm space-y-0.5">
                  {riskFactors.map((f, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <AlertTriangle className="size-3 shrink-0 mt-0.5 text-amber-500" />{f}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground mb-3">No risk factors identified.</p>
            )}
            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-4">
              <Clock className="size-3" />
              Total pipeline: {(totalDuration / 1000).toFixed(2)}s
              <Separator orientation="vertical" className="h-3" />
              Final status: <span className="font-medium">{finalStatus.replace("_", " ")}</span>
            </div>
            <div className="flex gap-2">
              <Button size="sm" asChild><Link href="/approvals">View in Approvals &rarr;</Link></Button>
              <Button size="sm" variant="outline" asChild><Link href={`/invoices/${invoiceId}`}>View Invoice</Link></Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ── Timing summary bar ───────────────────────────────────────────────────────

function TimingBar({ steps, totalMs }: { steps: StreamingPipelineStep[]; totalMs: number }) {
  const completedSteps = steps.filter((s) => s.duration_ms != null)
  return (
    <div className="space-y-2">
      <div className="flex rounded-lg overflow-hidden h-2 bg-muted/30">
        {completedSteps.map((s) => {
          const pct = totalMs > 0 ? ((s.duration_ms || 0) / totalMs) * 100 : 100 / completedSteps.length
          const colors: Record<string, string> = {
            ocr_extraction: "bg-blue-400",
            vendor_match: "bg-cyan-400",
            classification: "bg-violet-400",
            three_way_match: "bg-amber-400",
            exception_resolution: "bg-rose-400",
            approval_recommendation: "bg-emerald-400",
          }
          return (
            <div key={s.step} className={`${colors[s.step] || "bg-primary"} transition-all`}
              style={{ width: `${pct}%` }} title={`${s.label}: ${s.duration_ms}ms`} />
          )
        })}
      </div>
      <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
        <span className="font-medium text-foreground">Total: {(totalMs / 1000).toFixed(2)}s</span>
        {completedSteps.map((s) => {
          const colors: Record<string, string> = {
            ocr_extraction: "bg-blue-400", vendor_match: "bg-cyan-400",
            classification: "bg-violet-400", three_way_match: "bg-amber-400",
            exception_resolution: "bg-rose-400", approval_recommendation: "bg-emerald-400",
          }
          return (
            <span key={s.step} className="flex items-center gap-1.5">
              <span className={`size-2 rounded-full ${colors[s.step] || "bg-primary"}`} />
              {s.label}: <span className="font-medium text-foreground">
                {(s.duration_ms || 0) < 1000 ? `${s.duration_ms}ms` : `${((s.duration_ms || 0) / 1000).toFixed(1)}s`}
              </span>
            </span>
          )
        })}
      </div>
    </div>
  )
}

// ── Main page ────────────────────────────────────────────────────────────────

export default function InvoicePipelinePage() {
  const params = useParams()
  const invoiceId = typeof params.id === "string" ? params.id : Array.isArray(params.id) ? params.id[0] : ""

  const { steps, isStreaming, error, done, start, reset } = useRunPipelineStream()

  const executePipeline = React.useCallback((id: string) => {
    reset()
    start(id)
  }, [start, reset])

  // Auto-run on mount
  React.useEffect(() => {
    if (!invoiceId) return
    executePipeline(invoiceId)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [invoiceId])

  // Extract recommendation from the approval step
  const approvalStep = steps.find((s) => s.step === "approval_recommendation" && s.status === "complete")
  const recOutput = approvalStep?.output as { recommendation?: string; reasoning?: string; risk_factors?: string[] } | undefined

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" asChild>
            <Link href={invoiceId ? `/invoices/${invoiceId}` : "/invoices"}>
              <ArrowLeft className="size-4 mr-1" />
              Back to Invoice
            </Link>
          </Button>
          <Separator orientation="vertical" className="h-5" />
          <div className="flex items-center gap-2">
            <Zap className="size-5 text-primary" />
            <h1 className="text-lg font-semibold">Agent Pipeline</h1>
            {done && (
              <span className="text-sm text-muted-foreground">&mdash; {done.invoice_number}</span>
            )}
          </div>
        </div>
        {(done || !isStreaming) && steps.length > 0 && (
          <Button variant="outline" size="sm" onClick={() => executePipeline(invoiceId)}
            disabled={isStreaming}>
            <RefreshCw className={`size-3.5 mr-1.5 ${isStreaming ? "animate-spin" : ""}`} />
            Re-run
          </Button>
        )}
      </div>

      {/* Horizontal Stepper */}
      {steps.length > 0 && (
        <div className="animate-in fade-in duration-300">
          <HorizontalStepper steps={steps} />
        </div>
      )}

      {/* Running indicator (before any steps arrive) */}
      {isStreaming && steps.length === 0 && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="py-6">
            <div className="flex items-center gap-4">
              <Loader2 className="size-6 text-primary animate-spin shrink-0" />
              <div>
                <p className="font-semibold">Starting Agent Pipeline...</p>
                <p className="text-sm text-muted-foreground mt-0.5">
                  OCR &rarr; Vendor Match &rarr; Classification &rarr; 3-Way Match &rarr; Exception Resolution &rarr; Recommendation
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error state */}
      {error && (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="py-6">
            <div className="flex items-center gap-3">
              <XCircle className="size-5 text-destructive shrink-0" />
              <div>
                <p className="font-medium text-destructive">Pipeline error</p>
                <p className="text-sm text-muted-foreground">{error}</p>
              </div>
              <Button size="sm" variant="outline" className="ml-auto"
                onClick={() => executePipeline(invoiceId)}>
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step cards — rendered progressively as they stream in */}
      {steps.length > 0 && (
        <div className="space-y-4">
          {steps.map((step, i) => (
            <StepCard
              key={step.step}
              step={step}
              index={i}
              onRefresh={() => {
                // After approval actions, we could re-fetch, but for now just log
              }}
            />
          ))}

          {/* Recommendation card */}
          {done && recOutput && (
            <RecommendationCard
              recommendation={done.recommendation}
              reasoning={recOutput.reasoning}
              riskFactors={recOutput.risk_factors}
              totalDuration={done.total_duration_ms}
              finalStatus={done.final_status}
              invoiceId={done.invoice_id}
            />
          )}

          {/* Timing bar */}
          {done && (
            <div className="animate-in fade-in duration-500">
              <TimingBar steps={steps} totalMs={done.total_duration_ms} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
