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
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { useRunPipeline, type PipelineResult, type PipelineStep } from "@/hooks/use-invoices"

// ── Step config ──────────────────────────────────────────────────────────────

const STEP_CONFIG: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  ocr_extraction: { icon: <Eye className="size-4" />, color: "text-blue-500", label: "OCR" },
  classification: { icon: <Brain className="size-4" />, color: "text-violet-500", label: "Classify" },
  three_way_match: { icon: <GitMerge className="size-4" />, color: "text-amber-500", label: "Match" },
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

function HorizontalStepper({ steps, activeIndex }: { steps: PipelineStep[]; activeIndex: number }) {
  return (
    <div className="flex items-center gap-1 w-full">
      {steps.map((step, i) => {
        const cfg = STEP_CONFIG[step.step] || { icon: <Zap className="size-4" />, color: "text-primary", label: step.label }
        const isActive = i <= activeIndex
        const isComplete = step.status === "complete"
        const isError = step.status === "error"

        return (
          <React.Fragment key={step.step}>
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all ${
              isActive ? "bg-card border shadow-sm" : "opacity-40"
            }`}>
              <div className={`flex items-center justify-center size-7 rounded-full border-2 transition-colors ${
                isError ? "border-red-500 bg-red-50 dark:bg-red-950" :
                isComplete ? "border-green-500 bg-green-50 dark:bg-green-950" :
                isActive ? "border-primary bg-primary/10" : "border-muted-foreground/30"
              }`}>
                {isError ? <X className="size-3.5 text-red-500" /> :
                 isComplete ? <Check className="size-3.5 text-green-600" /> :
                 <span className="text-xs font-medium text-muted-foreground">{i + 1}</span>}
              </div>
              <div className="hidden sm:block">
                <p className="text-xs font-medium leading-none">{cfg.label}</p>
                {isActive && (
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    {step.duration_ms < 1000 ? `${step.duration_ms}ms` : `${(step.duration_ms / 1000).toFixed(1)}s`}
                  </p>
                )}
              </div>
            </div>
            {i < steps.length - 1 && (
              <div className={`flex-1 h-0.5 min-w-4 rounded transition-colors ${
                i < activeIndex ? (steps[i].status === "error" ? "bg-red-300" : "bg-green-400") : "bg-muted"
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
        {match ? (
          <CheckCircle2 className="size-4 text-green-500" />
        ) : (
          <XCircle className="size-4 text-red-500" />
        )}
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
          {/* Invoice column */}
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-muted-foreground mb-1">
              <FileText className="size-3" />
              <span className="font-medium">Invoice</span>
            </div>
            <div>Qty: <span className="font-mono font-medium">{inv.quantity}</span></div>
            <div>Price: <span className="font-mono font-medium">${inv.unit_price.toFixed(2)}</span></div>
            <div>Total: <span className="font-mono font-medium">${inv.line_total.toFixed(2)}</span></div>
          </div>

          {/* PO column */}
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-muted-foreground mb-1">
              <Package className="size-3" />
              <span className="font-medium">PO</span>
            </div>
            <div className="flex items-center gap-1">
              Qty: <span className="font-mono font-medium">{po.quantity}</span>
              {checks?.quantity && (
                checks.quantity.match
                  ? <CheckCircle2 className="size-3 text-green-500" />
                  : <span className="text-red-500 font-medium">({checks.quantity.variance_pct > 0 ? "+" : ""}{checks.quantity.variance_pct}%)</span>
              )}
            </div>
            <div>Price: <span className="font-mono font-medium">${po.unit_price.toFixed(2)}</span></div>
            <div className="flex items-center gap-1">
              Total: <span className="font-mono font-medium">${po.line_total.toFixed(2)}</span>
              {checks?.amount && (
                checks.amount.match
                  ? <CheckCircle2 className="size-3 text-green-500" />
                  : <span className="text-red-500 font-medium">({checks.amount.variance_pct > 0 ? "+" : ""}{checks.amount.variance_pct}%)</span>
              )}
            </div>
          </div>

          {/* GRN column */}
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-muted-foreground mb-1">
              <Truck className="size-3" />
              <span className="font-medium">GRN</span>
            </div>
            {grn ? (
              <>
                <div className="flex items-center gap-1">
                  Rcvd: <span className="font-mono font-medium">{grn.quantity_received}</span>
                  {checks?.grn_receipt && (
                    checks.grn_receipt.match
                      ? <CheckCircle2 className="size-3 text-green-500" />
                      : <span className="text-red-500 font-medium">({checks.grn_receipt.variance_pct > 0 ? "+" : ""}{checks.grn_receipt.variance_pct}%)</span>
                  )}
                </div>
                <div className="text-muted-foreground">{grn.grn_count} receipt(s)</div>
              </>
            ) : (
              <div className="text-muted-foreground italic">N/A (2-way)</div>
            )}
          </div>
        </div>
      )}

      {/* Exceptions for this line */}
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
      {/* Score + Status Header */}
      <div className="flex items-center gap-4">
        <ScoreGauge score={score} size={72} />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg font-bold">
              {matchStatus === "matched" ? "Full Match" :
               matchStatus === "tolerance_passed" ? "Matched (Tolerance)" :
               matchStatus === "partial" ? "Partial Match" : "Unmatched"}
            </span>
            <Badge variant="outline" className="text-xs">
              {matchType.replace("_", "-")}
            </Badge>
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

      {/* Header Match Checks */}
      {headerMatch && Object.keys(headerMatch).length > 0 && (
        <Card>
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Header-Level Checks</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-3 space-y-1.5">
            {headerMatch.vendor && (
              <MatchIndicator match={(headerMatch.vendor as { match: boolean }).match} label="Vendor" />
            )}
            {headerMatch.po_number && (
              <MatchIndicator match={(headerMatch.po_number as { match: boolean }).match} label="PO Number"
                value={(headerMatch.po_number as { value?: string }).value} />
            )}
            {headerMatch.currency && (
              <MatchIndicator match={(headerMatch.currency as { match: boolean }).match} label="Currency" />
            )}
            {headerMatch.invoice_total !== undefined && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Total Amount</span>
                <span className="font-mono text-xs">
                  ${(headerMatch.invoice_total as number).toFixed(2)} vs ${(headerMatch.po_total as number).toFixed(2)}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tolerance Info */}
      {(output.tolerance_applied as boolean) && toleranceConfig && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground bg-blue-50 dark:bg-blue-950/30 rounded-lg px-3 py-2">
          <ShieldCheck className="size-3.5 text-blue-500" />
          <span>
            Tolerance applied &mdash; Amount: {(toleranceConfig.amount_pct as number)}% / ${(toleranceConfig.amount_abs as number).toFixed(0)},
            Quantity: {(toleranceConfig.quantity_pct as number)}%
            <span className="text-muted-foreground/60 ml-1">({(toleranceConfig.scope as string)})</span>
          </span>
        </div>
      )}

      {/* Line-Level Comparison */}
      {lines.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Line-Level Comparison</p>
          {lines.map((line, i) => (
            <LineComparisonRow key={i} line={line} />
          ))}
        </div>
      )}
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

function StepCard({ step, index, visible }: { step: PipelineStep; index: number; visible: boolean }) {
  const [expanded, setExpanded] = React.useState(step.step === "three_way_match")
  const cfg = STEP_CONFIG[step.step] || { icon: <Zap className="size-4" />, color: "text-primary", label: step.label }
  const isMatchStep = step.step === "three_way_match"

  if (!visible) return null

  return (
    <Card className="overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-300">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`flex items-center justify-center size-8 rounded-full border-2 ${
              step.status === "complete"
                ? "border-green-500 bg-green-50 dark:bg-green-950"
                : "border-red-500 bg-red-50 dark:bg-red-950"
            }`}>
              {step.status === "complete" ? (
                <CheckCircle2 className="size-4 text-green-600" />
              ) : (
                <XCircle className="size-4 text-red-500" />
              )}
            </div>
            <div>
              <p className="text-sm font-semibold">
                <span className="text-muted-foreground mr-1">Step {index + 1}:</span>
                {step.label}
              </p>
              <p className={`text-xs ${cfg.color} flex items-center gap-1`}>
                {cfg.icon}
                {step.agent}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Clock className="size-3" />
              {step.duration_ms < 1000 ? `${step.duration_ms}ms` : `${(step.duration_ms / 1000).toFixed(1)}s`}
            </span>
            <Badge variant={step.status === "complete" ? "default" : "destructive"} className="text-xs">
              {step.status}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {step.status === "error" ? (
          <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 rounded-lg p-3">
            <AlertTriangle className="size-4 shrink-0" />
            {step.error ?? "Unknown error"}
          </div>
        ) : isMatchStep && step.output?.details ? (
          <MatchVisualization output={step.output} />
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
    </Card>
  )
}

// ── Recommendation card ──────────────────────────────────────────────────────

function RecommendationCard({ result, visible }: { result: PipelineResult; visible: boolean }) {
  if (!visible) return null

  const rec = result.recommendation
  const lastStep = result.steps.find((s) => s.step === "approval_recommendation")
  const output = lastStep?.output as {
    recommendation?: string
    reasoning?: string
    risk_factors?: string[]
  } | undefined

  const colorMap = {
    approve: {
      bg: "bg-green-50 dark:bg-green-950",
      border: "border-green-400",
      text: "text-green-700 dark:text-green-300",
      badge: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
      icon: <ShieldCheck className="size-6 text-green-600" />,
      label: "APPROVED",
    },
    review: {
      bg: "bg-amber-50 dark:bg-amber-950",
      border: "border-amber-400",
      text: "text-amber-700 dark:text-amber-300",
      badge: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-100",
      icon: <ShieldQuestion className="size-6 text-amber-600" />,
      label: "NEEDS REVIEW",
    },
    reject: {
      bg: "bg-red-50 dark:bg-red-950",
      border: "border-red-400",
      text: "text-red-700 dark:text-red-300",
      badge: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
      icon: <ShieldAlert className="size-6 text-red-600" />,
      label: "REJECTED",
    },
  }
  const style = colorMap[rec ?? "review"]

  return (
    <Card className={`border-2 ${style.border} ${style.bg} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
      <CardContent className="pt-6 pb-6">
        <div className="flex items-start gap-4">
          {style.icon}
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className={`text-lg font-bold ${style.text}`}>{style.label}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${style.badge}`}>
                AI Recommendation
              </span>
            </div>

            {output?.reasoning && (
              <p className="text-sm text-foreground/80 mb-3 leading-relaxed">
                &ldquo;{output.reasoning}&rdquo;
              </p>
            )}

            {output?.risk_factors && output.risk_factors.length > 0 ? (
              <div className="mb-3">
                <p className="text-xs font-medium text-muted-foreground mb-1">Risk factors:</p>
                <ul className="text-sm space-y-0.5">
                  {output.risk_factors.map((f, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <AlertTriangle className="size-3 shrink-0 mt-0.5 text-amber-500" />
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground mb-3">No risk factors identified.</p>
            )}

            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-4">
              <Clock className="size-3" />
              Total pipeline: {(result.total_duration_ms / 1000).toFixed(2)}s
              <Separator orientation="vertical" className="h-3" />
              Final status: <span className="font-medium">{result.final_status.replace("_", " ")}</span>
            </div>

            <div className="flex gap-2">
              <Button size="sm" asChild>
                <Link href="/approvals">View in Approvals &rarr;</Link>
              </Button>
              <Button size="sm" variant="outline" asChild>
                <Link href={`/invoices/${result.invoice_id}`}>View Invoice</Link>
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ── Timing summary bar ───────────────────────────────────────────────────────

function TimingBar({ result }: { result: PipelineResult }) {
  const total = result.total_duration_ms
  return (
    <div className="space-y-2">
      <div className="flex rounded-lg overflow-hidden h-2 bg-muted/30">
        {result.steps.map((s) => {
          const pct = total > 0 ? (s.duration_ms / total) * 100 : 25
          const colors: Record<string, string> = {
            ocr_extraction: "bg-blue-400",
            classification: "bg-violet-400",
            three_way_match: "bg-amber-400",
            approval_recommendation: "bg-emerald-400",
          }
          return (
            <div key={s.step} className={`${colors[s.step] || "bg-primary"} transition-all`}
              style={{ width: `${pct}%` }} title={`${s.label}: ${s.duration_ms}ms`} />
          )
        })}
      </div>
      <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
        <span className="font-medium text-foreground">
          Total: {(total / 1000).toFixed(2)}s
        </span>
        {result.steps.map((s) => {
          const colors: Record<string, string> = {
            ocr_extraction: "bg-blue-400",
            classification: "bg-violet-400",
            three_way_match: "bg-amber-400",
            approval_recommendation: "bg-emerald-400",
          }
          return (
            <span key={s.step} className="flex items-center gap-1.5">
              <span className={`size-2 rounded-full ${colors[s.step] || "bg-primary"}`} />
              {s.label}: <span className="font-medium text-foreground">
                {s.duration_ms < 1000 ? `${s.duration_ms}ms` : `${(s.duration_ms / 1000).toFixed(1)}s`}
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

  const runPipeline = useRunPipeline()
  const [result, setResult] = React.useState<PipelineResult | null>(null)
  const [visibleSteps, setVisibleSteps] = React.useState(0)
  const [showRecommendation, setShowRecommendation] = React.useState(false)

  const executePipeline = React.useCallback((id: string) => {
    setResult(null)
    setVisibleSteps(0)
    setShowRecommendation(false)
    runPipeline.mutate(id, {
      onSuccess: (data) => {
        setResult(data)
        data.steps.forEach((_, i) => {
          setTimeout(() => setVisibleSteps(i + 1), i * 400)
        })
        setTimeout(() => setShowRecommendation(true), data.steps.length * 400 + 300)
      },
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Auto-run on mount
  React.useEffect(() => {
    if (!invoiceId) return
    executePipeline(invoiceId)
  }, [invoiceId, executePipeline])

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
            {result && (
              <span className="text-sm text-muted-foreground">&mdash; {result.invoice_number}</span>
            )}
          </div>
        </div>
        {result && (
          <Button variant="outline" size="sm" onClick={() => executePipeline(invoiceId)}
            disabled={runPipeline.isPending}>
            <RefreshCw className={`size-3.5 mr-1.5 ${runPipeline.isPending ? "animate-spin" : ""}`} />
            Re-run
          </Button>
        )}
      </div>

      {/* Horizontal Stepper */}
      {result && (
        <div className="animate-in fade-in duration-300">
          <HorizontalStepper steps={result.steps} activeIndex={visibleSteps - 1} />
        </div>
      )}

      {/* Running indicator */}
      {runPipeline.isPending && !result && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="py-6">
            <div className="flex items-center gap-4">
              <Loader2 className="size-6 text-primary animate-spin shrink-0" />
              <div>
                <p className="font-semibold">Running Agent Pipeline...</p>
                <p className="text-sm text-muted-foreground mt-0.5">
                  OCR Extraction &rarr; Document Classification &rarr; 3-Way Match &rarr; Approval Recommendation
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error state */}
      {runPipeline.isError && (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="py-6">
            <div className="flex items-center gap-3">
              <XCircle className="size-5 text-destructive shrink-0" />
              <div>
                <p className="font-medium text-destructive">Pipeline failed to start</p>
                <p className="text-sm text-muted-foreground">
                  {runPipeline.error instanceof Error ? runPipeline.error.message : "Unknown error"}
                </p>
              </div>
              <Button size="sm" variant="outline" className="ml-auto"
                onClick={() => executePipeline(invoiceId)}>
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step cards */}
      {result && (
        <div className="space-y-4">
          {result.steps.map((step, i) => (
            <StepCard key={step.step} step={step} index={i} visible={i < visibleSteps} />
          ))}

          <RecommendationCard result={result} visible={showRecommendation} />

          {showRecommendation && (
            <div className="animate-in fade-in duration-500">
              <TimingBar result={result} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
