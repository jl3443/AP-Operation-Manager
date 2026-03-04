"use client"

import * as React from "react"
import { Calculator, CheckCircle2, Loader2 } from "lucide-react"
import { toast } from "sonner"

import { useApplyCorrections } from "@/hooks/use-invoices"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { AutomationAction } from "@/lib/types"

interface RecalcLine {
  line_number: number
  computed: number
  current: number
  match: boolean
}

interface RecalcTotalResult {
  computed_total: number
  current_total: number
  difference: number
  totals_match: boolean
}

export function RecalculationCard({
  lineRecalcAction,
  totalRecalcAction,
  invoiceId,
  onAccepted,
}: {
  lineRecalcAction: AutomationAction
  totalRecalcAction?: AutomationAction
  invoiceId: string
  onAccepted?: () => void
}) {
  const [accepted, setAccepted] = React.useState(false)
  const applyCorrections = useApplyCorrections()

  const lineResult = lineRecalcAction.result_json as { lines?: RecalcLine[] } | undefined
  const totalResult = totalRecalcAction?.result_json as RecalcTotalResult | undefined

  const lines = lineResult?.lines || []
  const mismatched = lines.filter((l) => !l.match)

  if (accepted) {
    return (
      <Card className="border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950/30">
        <CardContent className="py-4 flex items-center gap-3">
          <CheckCircle2 className="size-5 text-green-600 shrink-0" />
          <div>
            <p className="text-sm font-medium text-green-800 dark:text-green-200">
              Corrections Applied
            </p>
            <p className="text-xs text-green-600 dark:text-green-400">
              {mismatched.length} line(s) corrected — invoice total recalculated
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-950/30">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Calculator className="size-4 text-amber-600" />
          Data Mismatch — Recalculation
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Comparison table */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b">
                <th className="text-left py-1.5 px-2 font-medium">Line</th>
                <th className="text-right py-1.5 px-2 font-medium">Original Total</th>
                <th className="text-right py-1.5 px-2 font-medium">Corrected Total</th>
                <th className="text-right py-1.5 px-2 font-medium">Difference</th>
              </tr>
            </thead>
            <tbody>
              {lines.map((line) => (
                <tr
                  key={line.line_number}
                  className={cn(
                    "border-b",
                    !line.match && "bg-red-50 dark:bg-red-950/20"
                  )}
                >
                  <td className="py-1.5 px-2">{line.line_number}</td>
                  <td className="text-right py-1.5 px-2 font-mono">
                    ${line.current.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="text-right py-1.5 px-2 font-mono">
                    ${line.computed.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td
                    className={cn(
                      "text-right py-1.5 px-2 font-mono",
                      !line.match && "text-red-600 font-semibold"
                    )}
                  >
                    {line.match ? "—" : `$${(line.computed - line.current).toFixed(2)}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Summary row */}
        {totalResult && (
          <div className="flex items-center justify-between rounded-lg bg-white dark:bg-slate-900 border px-3 py-2">
            <div className="text-xs">
              <span className="text-muted-foreground">Old Total:</span>{" "}
              <span className="font-mono font-semibold">
                ${totalResult.current_total.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="text-xs font-bold">→</div>
            <div className="text-xs">
              <span className="text-muted-foreground">New Total:</span>{" "}
              <span className="font-mono font-semibold text-green-600">
                ${totalResult.computed_total.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="text-xs">
              <span className="text-muted-foreground">Diff:</span>{" "}
              <span className="font-mono font-semibold text-red-600">
                ${totalResult.difference.toFixed(2)}
              </span>
            </div>
          </div>
        )}

        <Button
          size="sm"
          className="bg-amber-600 hover:bg-amber-700 w-full"
          disabled={applyCorrections.isPending}
          onClick={() => {
            applyCorrections.mutate(
              { invoiceId },
              {
                onSuccess: () => {
                  setAccepted(true)
                  toast.success("Corrections applied to invoice")
                  onAccepted?.()
                },
                onError: (err) => toast.error(String(err)),
              }
            )
          }}
        >
          {applyCorrections.isPending ? (
            <Loader2 className="size-3.5 mr-1.5 animate-spin" />
          ) : (
            <CheckCircle2 className="size-3.5 mr-1.5" />
          )}
          Accept Corrections
        </Button>
      </CardContent>
    </Card>
  )
}
