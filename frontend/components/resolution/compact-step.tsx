"use client"

import {
  CheckCircle2,
  Loader2,
  Shield,
  XCircle,
} from "lucide-react"

import { cn } from "@/lib/utils"
import type { AutomationAction } from "@/lib/types"

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ACTION_LABELS: Record<string, string> = {
  GENERATE_EXPLANATION: "Generate Variance Explanation",
  DRAFT_VENDOR_EMAIL: "Draft Email to Vendor",
  DRAFT_INTERNAL_MESSAGE: "Draft Internal Message",
  CHECK_GRN_STATUS: "Check Goods Receipt Status",
  SEARCH_PO_CANDIDATES: "Search for Matching POs",
  RERUN_MATCH: "Re-run Invoice Matching",
  LOCK_INVOICE_FOR_PAYMENT: "Lock Invoice (Prevent Payment)",
  CREATE_HUMAN_TASK: "Create Task for Team",
  CREATE_WAIT_TIMER: "Set Follow-up Timer",
  CLOSE_EXCEPTION: "Close Exception",
  PROCEED_TO_APPROVAL: "Move to Approval",
  FIND_POSSIBLE_DUPLICATES: "Check for Duplicates",
  RECALCULATE_INVOICE_TOTAL: "Recalculate Invoice Total",
  NORMALIZE_UOM: "Normalize Unit of Measure",
  SUGGEST_VENDOR_ALIAS: "Suggest Vendor Alias",
  LINK_INVOICE_VENDOR: "Link Invoice to Vendor",
  PROPOSE_AUTO_RESOLVE: "Propose Auto-Resolution",
  REASSIGN_EXCEPTION: "Reassign Exception",
  FETCH_FX_RATE: "Fetch Exchange Rate",
  CONVERT_AMOUNTS: "Convert Currency Amounts",
  RECALC_TAX: "Recalculate Tax",
  PATCH_INVOICE_FIELDS: "Update Invoice Fields",
  CHECK_VENDOR_COMPLIANCE: "Check Vendor Compliance",
}

export function friendlyActionType(type: string): string {
  return ACTION_LABELS[type] || type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
}

export function summarizeResult(action: AutomationAction): string | null {
  const r = action.result_json
  if (!r) return null
  if (r.subject && r.body) return `Email draft ready: "${r.subject}"`
  if (r.explanation) return String(r.explanation)
  if (r.summary) return String(r.summary)
  if (r.grn_status) return `GRN status: ${r.grn_status}`
  if (r.message) return String(r.message)
  if (r.status) return `Status: ${r.status}`
  return null
}

// ---------------------------------------------------------------------------
// Step dot
// ---------------------------------------------------------------------------

function StepDot({ action }: { action: AutomationAction }) {
  if (action.status === "done")
    return <div className="size-5 rounded-full bg-green-500 flex items-center justify-center"><CheckCircle2 className="size-3 text-white" /></div>
  if (action.status === "failed")
    return <div className="size-5 rounded-full bg-red-500 flex items-center justify-center"><XCircle className="size-3 text-white" /></div>
  if (action.status === "running")
    return <div className="size-5 rounded-full bg-blue-500 flex items-center justify-center"><Loader2 className="size-3 text-white animate-spin" /></div>
  if (action.status === "awaiting_approval")
    return <div className="size-5 rounded bg-amber-400 flex items-center justify-center rotate-45"><Shield className="size-3 text-white -rotate-45" /></div>
  return <div className="size-5 rounded-full bg-slate-200 flex items-center justify-center"><span className="text-[9px] font-bold text-slate-500">{action.step_id.replace("S", "")}</span></div>
}

// ---------------------------------------------------------------------------
// Compact step row
// ---------------------------------------------------------------------------

export function CompactStep({ action, isLast }: { action: AutomationAction; isLast: boolean }) {
  const summary = summarizeResult(action)

  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <StepDot action={action} />
        {!isLast && <div className="w-px flex-1 bg-border min-h-[12px]" />}
      </div>
      <div className={cn("flex-1 min-w-0", !isLast && "pb-3")}>
        <div className="flex items-center justify-between gap-2">
          <span className={cn("text-sm", action.status === "done" ? "text-muted-foreground" : "font-medium")}>
            {friendlyActionType(action.action_type)}
          </span>
          {action.status === "done" && <CheckCircle2 className="size-3.5 text-green-500 shrink-0" />}
          {action.status === "failed" && <span className="text-[10px] text-red-500">Failed</span>}
        </div>
        {summary && <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{summary}</p>}
        {action.error_message && <p className="text-xs text-red-500 mt-0.5">{action.error_message}</p>}
      </div>
    </div>
  )
}
