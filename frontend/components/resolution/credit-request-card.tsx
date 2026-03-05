"use client"

import * as React from "react"
import { CheckCircle2, FileText, Loader2 } from "lucide-react"
import { toast } from "sonner"

import { apiPost } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { EmailConfirmationDialog } from "@/components/email/email-confirmation-dialog"
import { useEmail } from "@/hooks/use-email"
import type { AutomationAction } from "@/lib/types"

interface OverrunLine {
  line_number: number
  description: string
  invoiced_qty: number
  po_qty: number
  excess_qty: number
  unit_price: number
  credit_amount: number
}

interface CreditResult {
  credit_request_number?: string
  vendor_name?: string
  invoice_number?: string
  invoice_date?: string
  overrun_lines?: OverrunLine[]
  total_credit_amount?: number
  narrative?: string
  status?: string
}

export function CreditRequestCard({
  action,
  invoiceId,
  onApproved,
}: {
  action: AutomationAction
  invoiceId: string
  onApproved?: () => void
}) {
  const [approved, setApproved] = React.useState(false)
  const [isLoadingPreview, setIsLoadingPreview] = React.useState(false)
  const { preview, isLoadingConfirm, fetchCreditApprovalPreview, sendCreditApprovalEmail } = useEmail(invoiceId)
  const result = (action.result_json || {}) as CreditResult

  const {
    credit_request_number = "CR-???",
    vendor_name = "Unknown",
    invoice_number = "",
    invoice_date = "",
    overrun_lines = [],
    total_credit_amount = 0,
    narrative = "",
  } = result

  if (approved) {
    return (
      <Card className="border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950/30">
        <CardContent className="py-4 flex items-center gap-3">
          <CheckCircle2 className="size-5 text-green-600 shrink-0" />
          <div>
            <p className="text-sm font-medium text-green-800 dark:text-green-200">
              Credit Request Approved
            </p>
            <p className="text-xs text-green-600 dark:text-green-400">
              {credit_request_number} — ${total_credit_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })} credit to {vendor_name}
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-purple-200 bg-purple-50/50 dark:border-purple-800 dark:bg-purple-950/30">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <FileText className="size-4 text-purple-600" />
          Credit Request: {credit_request_number}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Header info */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-muted-foreground">Vendor:</span>{" "}
            <span className="font-medium">{vendor_name}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Date:</span>{" "}
            <span className="font-medium">{new Date().toLocaleDateString()}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Invoice Ref:</span>{" "}
            <span className="font-medium">{invoice_number}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Invoice Date:</span>{" "}
            <span className="font-medium">{invoice_date}</span>
          </div>
        </div>

        {/* Overrun table */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b bg-purple-100/50 dark:bg-purple-900/20">
                <th className="text-left py-1.5 px-2 font-medium">Line</th>
                <th className="text-left py-1.5 px-2 font-medium">Description</th>
                <th className="text-right py-1.5 px-2 font-medium">Invoiced</th>
                <th className="text-right py-1.5 px-2 font-medium">PO Qty</th>
                <th className="text-right py-1.5 px-2 font-medium">Excess</th>
                <th className="text-right py-1.5 px-2 font-medium">Unit Price</th>
                <th className="text-right py-1.5 px-2 font-medium">Credit</th>
              </tr>
            </thead>
            <tbody>
              {overrun_lines.map((line) => (
                <tr key={line.line_number} className="border-b">
                  <td className="py-1.5 px-2">{line.line_number}</td>
                  <td className="py-1.5 px-2 truncate max-w-[120px]">{line.description}</td>
                  <td className="text-right py-1.5 px-2 font-mono">{line.invoiced_qty}</td>
                  <td className="text-right py-1.5 px-2 font-mono">{line.po_qty}</td>
                  <td className="text-right py-1.5 px-2 font-mono text-red-600 font-semibold">
                    +{line.excess_qty}
                  </td>
                  <td className="text-right py-1.5 px-2 font-mono">
                    ${line.unit_price.toFixed(2)}
                  </td>
                  <td className="text-right py-1.5 px-2 font-mono font-semibold text-purple-700 dark:text-purple-400">
                    ${line.credit_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-2 font-semibold">
                <td colSpan={6} className="text-right py-2 px-2">Total Credit:</td>
                <td className="text-right py-2 px-2 font-mono text-purple-700 dark:text-purple-400">
                  ${total_credit_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        {/* AI narrative */}
        {narrative && (
          <div className="bg-white dark:bg-slate-900 rounded-lg border p-3">
            <p className="text-xs text-muted-foreground font-medium mb-1">Justification</p>
            <p className="text-sm text-foreground leading-relaxed">{narrative}</p>
          </div>
        )}

        <Button
          size="sm"
          className="bg-purple-600 hover:bg-purple-700 w-full"
          disabled={approved || isLoadingPreview}
          onClick={async () => {
            setIsLoadingPreview(true)
            try {
              // Fetch email preview
              await fetchCreditApprovalPreview({
                credit_amount: total_credit_amount,
                action_id: action.id,
              })
            } catch (error) {
              toast.error(error instanceof Error ? error.message : "Failed to load email preview")
            } finally {
              setIsLoadingPreview(false)
            }
          }}
        >
          {isLoadingPreview ? (
            <>
              <Loader2 className="size-3.5 mr-1.5 animate-spin" />
              Loading Preview...
            </>
          ) : (
            <>
              <CheckCircle2 className="size-3.5 mr-1.5" />
              Approve Credit Request
            </>
          )}
        </Button>

        {/* Email confirmation dialog */}
        <EmailConfirmationDialog
          open={!!preview}
          preview={preview}
          isLoading={isLoadingConfirm}
          onConfirm={async (to, subject, body) => {
            await sendCreditApprovalEmail(
              to,
              subject,
              body,
              action.id,
              total_credit_amount
            )
            setApproved(true)
            toast.success("Credit request approved and email sent")
            onApproved?.()
          }}
          onCancel={() => {
            // Clear preview and close dialog (preview becomes null via hook state)
          }}
        />
      </CardContent>
    </Card>
  )
}
