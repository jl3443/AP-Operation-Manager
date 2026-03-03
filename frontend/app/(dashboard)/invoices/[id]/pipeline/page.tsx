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
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { useRunPipeline, type PipelineResult, type PipelineStep } from "@/hooks/use-invoices"

// ── Step icon mapping ────────────────────────────────────────────────────────

const STEP_ICONS: Record<string, React.ReactNode> = {
  ocr_extraction: <Eye className="size-4" />,
  classification: <Brain className="size-4" />,
  three_way_match: <GitMerge className="size-4" />,
  approval_recommendation: <ShieldCheck className="size-4" />,
}

const STEP_COLORS: Record<string, string> = {
  ocr_extraction: "text-blue-500",
  classification: "text-violet-500",
  three_way_match: "text-amber-500",
  approval_recommendation: "text-green-500",
}

// ── JSON viewer ──────────────────────────────────────────────────────────────

function JsonBlock({ data, expanded }: { data: Record<string, unknown>; expanded: boolean }) {
  const json = JSON.stringify(data, null, 2)
  return (
    <pre
      className={`text-xs font-mono bg-muted/60 rounded-lg p-4 overflow-auto transition-all ${
        expanded ? "max-h-[600px]" : "max-h-56"
      } whitespace-pre text-foreground/80 leading-relaxed`}
    >
      {json}
    </pre>
  )
}

// ── Individual step card ─────────────────────────────────────────────────────

function StepCard({
  step,
  index,
  visible,
}: {
  step: PipelineStep
  index: number
  visible: boolean
}) {
  const [expanded, setExpanded] = React.useState(false)
  const color = STEP_COLORS[step.step] ?? "text-primary"
  const icon = STEP_ICONS[step.step]

  if (!visible) return null

  return (
    <Card className="overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-300">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Step number + status */}
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

            {/* Step label */}
            <div>
              <p className="text-sm font-semibold">
                <span className="text-muted-foreground mr-1">Step {index + 1}:</span>
                {step.label}
              </p>
              <p className={`text-xs ${color} flex items-center gap-1`}>
                {icon}
                {step.agent}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Clock className="size-3" />
              {step.duration_ms < 1000
                ? `${step.duration_ms}ms`
                : `${(step.duration_ms / 1000).toFixed(1)}s`}
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
        ) : (
          <>
            <JsonBlock data={step.output} expanded={expanded} />
            <Button
              variant="ghost"
              size="sm"
              className="mt-2 text-xs text-muted-foreground"
              onClick={() => setExpanded((e) => !e)}
            >
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

function RecommendationCard({
  result,
  visible,
}: {
  result: PipelineResult
  visible: boolean
}) {
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
              <p className="text-xs text-muted-foreground mb-3">Risk factors: none</p>
            )}

            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-4">
              <Clock className="size-3" />
              Total pipeline: {(result.total_duration_ms / 1000).toFixed(2)}s
              <Separator orientation="vertical" className="h-3" />
              Final status: <span className="font-medium">{result.final_status.replace("_", " ")}</span>
            </div>

            <div className="flex gap-2">
              <Button size="sm" asChild>
                <Link href="/approvals">View in Approvals →</Link>
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
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground bg-muted/40 rounded-lg px-4 py-2">
      <span className="font-medium text-foreground">
        Total: {(result.total_duration_ms / 1000).toFixed(2)}s
      </span>
      <span className="text-muted-foreground/50">|</span>
      {result.steps.map((s) => (
        <span key={s.step}>
          {s.label}:{" "}
          <span className="font-medium text-foreground">
            {s.duration_ms < 1000 ? `${s.duration_ms}ms` : `${(s.duration_ms / 1000).toFixed(1)}s`}
          </span>
        </span>
      ))}
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

  // Auto-run on mount
  React.useEffect(() => {
    if (!invoiceId) return
    runPipeline.mutate(invoiceId, {
      onSuccess: (data) => {
        setResult(data)
        // Animate steps appearing one by one
        data.steps.forEach((_, i) => {
          setTimeout(() => {
            setVisibleSteps(i + 1)
          }, i * 350)
        })
        // Show recommendation card after all steps
        setTimeout(() => {
          setShowRecommendation(true)
        }, data.steps.length * 350 + 200)
      },
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [invoiceId])

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
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
              <span className="text-sm text-muted-foreground">— {result.invoice_number}</span>
            )}
          </div>
        </div>
        {result && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setResult(null)
              setVisibleSteps(0)
              setShowRecommendation(false)
              runPipeline.mutate(invoiceId, {
                onSuccess: (data) => {
                  setResult(data)
                  data.steps.forEach((_, i) => {
                    setTimeout(() => setVisibleSteps(i + 1), i * 350)
                  })
                  setTimeout(() => setShowRecommendation(true), data.steps.length * 350 + 200)
                },
              })
            }}
          >
            ↺ Re-run
          </Button>
        )}
      </div>

      {/* Running indicator */}
      {runPipeline.isPending && (
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="py-6">
            <div className="flex items-center gap-4">
              <Loader2 className="size-6 text-primary animate-spin shrink-0" />
              <div>
                <p className="font-semibold">Running Agent Pipeline...</p>
                <p className="text-sm text-muted-foreground mt-0.5">
                  Chaining: OCR Extraction → Document Classification → 3-Way Match → Approval Recommendation
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
              <Button
                size="sm"
                variant="outline"
                className="ml-auto"
                onClick={() => runPipeline.mutate(invoiceId)}
              >
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
            <StepCard
              key={step.step}
              step={step}
              index={i}
              visible={i < visibleSteps}
            />
          ))}

          {/* Recommendation card */}
          <RecommendationCard result={result} visible={showRecommendation} />

          {/* Timing bar */}
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
