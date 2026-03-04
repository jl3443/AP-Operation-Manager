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
  COMPARE_LINE_ITEMS: "Compare Invoice vs PO Lines",
  CHECK_TOLERANCE: "Check Tolerance Configuration",
  CALCULATE_VARIANCE_BREAKDOWN: "Breakdown Variance by Category",
  RECALCULATE_INVOICE_TOTAL: "Recalculate Invoice Total",
  RECALC_LINE_TOTALS: "Recalculate Line Totals",
  RECALC_TAX: "Recalculate Tax",
  SEARCH_PO_CANDIDATES: "Search for Matching POs",
  AUTO_LINK_PO: "Auto-Link PO Lines",
  CHECK_GRN_STATUS: "Check Goods Receipt Status",
  VERIFY_VENDOR_DETAILS: "Verify Vendor Details",
  SUGGEST_VENDOR_ALIAS: "Suggest Vendor Alias",
  LINK_INVOICE_VENDOR: "Link Invoice to Vendor",
  CHECK_VENDOR_COMPLIANCE: "Check Vendor Compliance",
  FIND_POSSIBLE_DUPLICATES: "Check for Duplicates",
  LOCK_INVOICE_FOR_PAYMENT: "Lock Invoice (Prevent Payment)",
  DRAFT_VENDOR_EMAIL: "Draft Email to Vendor",
  DRAFT_INTERNAL_MESSAGE: "Draft Internal Message",
  CREATE_HUMAN_TASK: "Create Task for Team",
  REASSIGN_EXCEPTION: "Reassign Exception",
  ESCALATE_TO_MANAGER: "Escalate to Manager",
  LOOKUP_POLICY_RULES: "Look Up Policy Rules",
  PROPOSE_AUTO_RESOLVE: "Propose Auto-Resolution",
  CLOSE_EXCEPTION: "Close Exception",
  PROCEED_TO_APPROVAL: "Move to Approval",
  FETCH_FX_RATE: "Fetch Exchange Rate",
  CONVERT_AMOUNTS: "Convert Currency Amounts",
  NORMALIZE_UOM: "Normalize Unit of Measure",
  RERUN_OCR: "Re-Extract from PDF",
  RERUN_MATCH: "Re-run Invoice Matching",
  PATCH_INVOICE_FIELDS: "Update Invoice Fields",
  PROPOSE_TERMS_OVERRIDE: "Propose Payment Terms Fix",
  CREATE_WAIT_TIMER: "Set Follow-up Timer",
  WAIT_FOR_REPLY: "Waiting for Reply",
  SUMMARIZE_FINDINGS: "Summarize Findings",
}

export function friendlyActionType(type: string): string {
  return ACTION_LABELS[type] || type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
}

export function summarizeResult(action: AutomationAction): string | null {
  const r = action.result_json
  if (!r) return null
  if (r.error) return `Error: ${r.error}`
  if (r.subject && r.body) return `Email draft ready: "${r.subject}"`
  if (r.explanation) return String(r.explanation).slice(0, 200)
  if (r.summary) return String(r.summary).slice(0, 200)
  if (r.comparisons) return `${r.lines_matched} lines match, ${r.lines_mismatched} mismatch (diff: $${r.total_diff})`
  if (r.within_any_tolerance != null) return r.within_any_tolerance ? `Within tolerance (${r.variance_pct}%)` : `Exceeds tolerance (${r.variance_pct}%)`
  if (r.variances) { const v = r.variances as Record<string, number>; return `Subtotal diff: $${v.subtotal_diff}, Tax: $${v.tax_component}` }
  if (r.computed_total != null && r.current_total != null) return `Computed: $${r.computed_total} vs Current: $${r.current_total} (diff: $${r.difference})`
  if (r.lines) return `${(r.lines as unknown[]).length} lines recalculated`
  if (r.candidates) return `${(r.candidates as unknown[]).length} PO candidates found`
  if (r.lines_linked != null) return `${r.lines_linked}/${r.total_lines} lines linked to PO`
  if (r.grn_found != null) return r.grn_found ? `${(r.grn_records as unknown[])?.length} GRN records found` : "No GRN records"
  if (r.vendor_name && r.vendor_status) return `${r.vendor_name} (${r.vendor_status}, risk: ${r.risk_level})`
  if (r.is_duplicate != null) return r.is_duplicate ? `Possible duplicate (${Number(r.confidence) * 100}%)` : "No duplicates found"
  if (r.can_auto_resolve != null) return r.can_auto_resolve ? `Can auto-resolve: ${r.reason}` : `Manual needed: ${r.reason}`
  if (r.match_status) return `Match: ${r.match_status} (score: ${r.overall_score}%)`
  if (r.escalated) return `Escalated to ${r.assigned_to}`
  if (r.locked) return "Invoice locked for payment"
  if (r.task_created) return `Task created: ${r.description}`
  if (r.reassigned) return `Reassigned to ${r.queue}`
  if (r.patched) return `Fields updated: ${Object.keys(r.patched).join(", ")}`
  if (r.message) return String(r.message)
  if (r.status) return `Status: ${r.status}`
  if (r.note) return String(r.note)
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
