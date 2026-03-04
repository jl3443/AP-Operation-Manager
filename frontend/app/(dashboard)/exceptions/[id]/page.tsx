"use client"

import * as React from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import {
  ArrowLeft,
  Bot,
  CheckCircle2,
  FileText,
  Loader2,
  MessageSquare,
  RotateCcw,
  Sparkles,
  XCircle,
  Zap,
} from "lucide-react"
import { toast } from "sonner"

import {
  useException,
  useResolutionPlan,
  useGenerateResolutionPlan,
  useRerunMatch,
} from "@/hooks/use-exceptions"
import { ExceptionTypeBadge } from "@/components/exception-type-badge"
import { SeverityIcon } from "@/components/severity-icon"
import { CompactStep, friendlyActionType, summarizeResult } from "@/components/resolution/compact-step"
import { ApprovalCheckpoint } from "@/components/resolution/approval-checkpoint"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"
import type { AutomationAction, ActionStatus, PlanStatus } from "@/lib/types"

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STATUS_STYLES: Record<string, string> = {
  open: "bg-slate-100 text-slate-700",
  resolved: "bg-green-50 text-green-700",
  escalated: "bg-red-50 text-red-700",
  assigned: "bg-blue-50 text-blue-700",
  in_progress: "bg-amber-50 text-amber-700",
}

const PLAN_STATUS: Record<PlanStatus, { label: string; color: string }> = {
  draft: { label: "Draft", color: "bg-slate-100 text-slate-700" },
  approved: { label: "In Progress", color: "bg-blue-100 text-blue-700" },
  executing: { label: "Executing", color: "bg-amber-100 text-amber-700" },
  completed: { label: "Completed", color: "bg-green-100 text-green-700" },
  failed: { label: "Failed", color: "bg-red-100 text-red-700" },
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function ExceptionDetailPage() {
  const params = useParams()
  const router = useRouter()
  const exceptionId = params.id as string
  const [autoGenTriggered, setAutoGenTriggered] = React.useState(false)

  const { data: exception, isLoading, error, refetch: refetchException } = useException(exceptionId)
  const {
    data: plan,
    isLoading: planLoading,
    error: planError,
    refetch: refetchPlan,
  } = useResolutionPlan(exceptionId)

  const generatePlan = useGenerateResolutionPlan()
  const rerunMatch = useRerunMatch()

  // Auto-generate plan if none exists
  React.useEffect(() => {
    if (!planLoading && planError && !autoGenTriggered && !generatePlan.isPending && exception && exception.status !== "resolved") {
      setAutoGenTriggered(true)
      generatePlan.mutate(exceptionId, {
        onSuccess: () => { refetchPlan(); refetchException() },
      })
    }
  }, [planLoading, planError, autoGenTriggered, exception])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !exception) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/exceptions")}>
          <ArrowLeft className="size-4 mr-1" /> Back
        </Button>
        <Card className="p-8 text-center text-muted-foreground">Exception not found.</Card>
      </div>
    )
  }

  const hasPlan = !!plan && !planError
  const isGenerating = generatePlan.isPending || (planLoading && !hasPlan) || (!hasPlan && autoGenTriggered && !generatePlan.isError)

  const sortedActions = hasPlan
    ? [...plan.actions].sort((a, b) => {
        const numA = parseInt(a.step_id.replace(/\D/g, "") || "0")
        const numB = parseInt(b.step_id.replace(/\D/g, "") || "0")
        return numA - numB
      })
    : []

  // Find the action awaiting approval (the blocking step)
  const blockingAction = sortedActions.find((a) => a.status === "awaiting_approval")
  const completedActions = sortedActions.filter((a) => a.status === "done" || a.status === "skipped")
  const pendingActions = sortedActions.filter((a) => a.status === "pending")
  const failedActions = sortedActions.filter((a) => a.status === "failed")
  const doneCount = completedActions.length
  const totalSteps = sortedActions.length
  const allDone = doneCount === totalSteps && totalSteps > 0

  const handleRefresh = () => {
    refetchPlan()
    refetchException()
  }

  return (
    <div className="space-y-5">
      {/* ─── Header ─── */}
      <div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground mb-2">
          <Link href="/exceptions" className="hover:text-foreground transition-colors">Exceptions</Link>
          <span>/</span>
          <span className="text-foreground">{exception.id.slice(0, 8)}</span>
        </div>

        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <Button variant="ghost" size="icon" className="size-8 shrink-0" onClick={() => router.push("/exceptions")}>
              <ArrowLeft className="size-4" />
            </Button>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <ExceptionTypeBadge type={exception.exception_type} />
                <SeverityIcon severity={exception.severity} showLabel />
                <Badge variant="outline" className={cn("text-xs", STATUS_STYLES[exception.status])}>
                  {exception.status.replace("_", " ").toUpperCase()}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Invoice {exception.invoice_id.slice(0, 8)}... &middot; Created {new Date(exception.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <Link href={`/invoices/${exception.invoice_id}`}>
            <Button variant="outline" size="sm"><FileText className="size-3.5 mr-1" /> View Invoice</Button>
          </Link>
        </div>
      </div>

      <Separator />

      {/* ─── Two-column layout ─── */}
      <div className="grid gap-6 md:grid-cols-2">

        {/* ── LEFT: Context ── */}
        <div className="space-y-4">
          {/* AI Diagnosis */}
          {hasPlan && plan.diagnosis && (
            <Card className="border-l-4 border-l-violet-500">
              <CardContent className="py-4">
                <div className="flex items-start gap-3">
                  {plan.confidence != null && (
                    <div className="shrink-0 flex flex-col items-center">
                      <div className={cn(
                        "text-lg font-bold",
                        plan.confidence >= 0.8 ? "text-green-600" : plan.confidence >= 0.6 ? "text-amber-600" : "text-red-600"
                      )}>
                        {Math.round(plan.confidence * 100)}%
                      </div>
                      <span className="text-[9px] text-muted-foreground">confidence</span>
                    </div>
                  )}
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-violet-600 flex items-center gap-1 mb-1">
                      <Sparkles className="size-3" /> AI Diagnosis
                    </p>
                    <p className="text-sm leading-relaxed">{plan.diagnosis}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Exception context cards */}
          {exception.ai_suggested_resolution && (
            <Card>
              <CardContent className="py-3">
                <p className="text-xs font-medium text-muted-foreground mb-1 flex items-center gap-1"><Bot className="size-3" /> Initial Analysis</p>
                <p className="text-sm text-muted-foreground leading-relaxed">{exception.ai_suggested_resolution}</p>
              </CardContent>
            </Card>
          )}

          {/* Metadata */}
          <Card>
            <CardContent className="py-3">
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                <div>
                  <dt className="text-xs text-muted-foreground">Exception ID</dt>
                  <dd className="font-mono text-xs">{exception.id.slice(0, 16)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Created</dt>
                  <dd className="text-xs">{new Date(exception.created_at).toLocaleString()}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Assigned To</dt>
                  <dd className="text-xs">{exception.assigned_to || <span className="italic text-muted-foreground">Unassigned</span>}</dd>
                </div>
                {exception.resolved_at && (
                  <div>
                    <dt className="text-xs text-muted-foreground">Resolved</dt>
                    <dd className="text-xs">{new Date(exception.resolved_at).toLocaleString()}</dd>
                  </div>
                )}
              </dl>
            </CardContent>
          </Card>

          {/* Activity */}
          {exception.comments && exception.comments.length > 0 && (
            <Card>
              <CardHeader className="pb-2 pt-3">
                <CardTitle className="text-xs flex items-center gap-1.5">
                  <MessageSquare className="size-3.5 text-slate-400" /> Activity ({exception.comments.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="divide-y">
                {exception.comments.map((c) => (
                  <div key={c.id} className="py-2 text-xs">
                    <span className="text-muted-foreground">{new Date(c.created_at).toLocaleString()}</span>
                    <p className="mt-0.5">{c.comment_text}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        {/* ── RIGHT: Resolution Flow ── */}
        <div className="space-y-4">

          {/* Generating state */}
          {isGenerating && (
            <Card className="border-violet-200 bg-violet-50/30">
              <CardContent className="py-10 text-center space-y-3">
                <div className="relative mx-auto w-12 h-12">
                  <Loader2 className="size-12 animate-spin text-violet-400" />
                  <Sparkles className="size-5 text-violet-600 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                </div>
                <p className="text-sm font-medium text-violet-700">Analyzing & Executing...</p>
                <p className="text-xs text-violet-500">AI is generating a plan and running automated steps</p>
              </CardContent>
            </Card>
          )}

          {/* Generation failed */}
          {!isGenerating && !hasPlan && generatePlan.isError && (
            <Card className="border-dashed">
              <CardContent className="py-8 text-center space-y-3">
                <XCircle className="size-8 mx-auto text-muted-foreground/40" />
                <p className="text-sm text-muted-foreground">Could not generate a resolution plan.</p>
                <Button variant="outline" size="sm" onClick={() => { setAutoGenTriggered(false); generatePlan.reset() }}>
                  <RotateCcw className="size-3.5 mr-1" /> Retry
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Plan loaded */}
          {hasPlan && (
            <>
              {/* Status bar */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="size-4 text-violet-500" />
                  <span className="text-sm font-medium">Resolution Plan</span>
                  <Badge className={cn("text-[10px]", PLAN_STATUS[plan.status]?.color)}>
                    {PLAN_STATUS[plan.status]?.label}
                  </Badge>
                </div>
                <span className="text-xs text-muted-foreground">{doneCount}/{totalSteps} steps</span>
              </div>

              {/* Progress bar */}
              {totalSteps > 0 && (
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-500",
                      allDone ? "bg-green-500" : failedActions.length > 0 ? "bg-red-400" : "bg-violet-500"
                    )}
                    style={{ width: `${Math.round((doneCount / totalSteps) * 100)}%` }}
                  />
                </div>
              )}

              {/* Completed steps (collapsed) */}
              {completedActions.length > 0 && (
                <Card>
                  <CardContent className="py-3">
                    {completedActions.map((action, idx) => (
                      <CompactStep
                        key={action.id}
                        action={action}
                        isLast={idx === completedActions.length - 1 && !blockingAction}
                      />
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* Blocking step — the main interaction */}
              {blockingAction && (
                <ApprovalCheckpoint
                  action={blockingAction}
                  exceptionId={exceptionId}
                  onComplete={handleRefresh}
                />
              )}

              {/* Remaining pending steps */}
              {pendingActions.length > 0 && (
                <Card className={blockingAction ? "opacity-50" : ""}>
                  <CardContent className="py-3">
                    {pendingActions.map((action, idx) => (
                      <CompactStep key={action.id} action={action} isLast={idx === pendingActions.length - 1} />
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* Failed steps */}
              {failedActions.length > 0 && (
                <Card className="border-red-200">
                  <CardContent className="py-3">
                    {failedActions.map((action, idx) => (
                      <CompactStep key={action.id} action={action} isLast={idx === failedActions.length - 1} />
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* All done → Re-run match */}
              {allDone && exception.status !== "resolved" && (
                <Card className="border-green-300 bg-green-50/50">
                  <CardContent className="py-4 text-center space-y-3">
                    <CheckCircle2 className="size-8 mx-auto text-green-500" />
                    <div>
                      <p className="text-sm font-medium text-green-700">All steps completed</p>
                      <p className="text-xs text-green-600 mt-0.5">Ready to re-run matching to verify the resolution</p>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => {
                        rerunMatch.mutate(exceptionId, {
                          onSuccess: (result: Record<string, unknown>) => {
                            if (result.exception_resolved) {
                              toast.success("Match passed! Exception resolved.")
                            } else {
                              toast.info(`Match: ${result.match_status} (score: ${result.overall_score}%)`)
                            }
                            handleRefresh()
                          },
                          onError: (err) => toast.error(String(err)),
                        })
                      }}
                      disabled={rerunMatch.isPending}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      {rerunMatch.isPending ? <Loader2 className="size-3 mr-1.5 animate-spin" /> : <RotateCcw className="size-3 mr-1.5" />}
                      Re-Run 3-Way Match
                    </Button>
                  </CardContent>
                </Card>
              )}

              {/* Resolved state */}
              {exception.status === "resolved" && (
                <Card className="border-green-300 bg-green-50/50">
                  <CardContent className="py-4 text-center space-y-2">
                    <CheckCircle2 className="size-10 mx-auto text-green-500" />
                    <p className="text-sm font-medium text-green-700">Exception Resolved</p>
                    {exception.resolution_notes && (
                      <p className="text-xs text-green-600">{exception.resolution_notes}</p>
                    )}
                    <Link href={`/invoices/${exception.invoice_id}`}>
                      <Button size="sm" variant="outline" className="mt-2">
                        <FileText className="size-3 mr-1.5" /> View Invoice for Approval
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
