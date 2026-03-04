"use client"

import { CheckCircle, Clock, Sparkles } from "lucide-react"
import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

export function AutoApprovedCard({
  totalDuration,
  invoiceId,
  postedAt,
}: {
  totalDuration: number
  invoiceId: string
  postedAt?: string
}) {
  const seconds = (totalDuration / 1000).toFixed(1)

  return (
    <Card className="border-green-300 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/40 dark:to-emerald-950/30 dark:border-green-700">
      <CardContent className="py-6 text-center space-y-3">
        <div className="flex justify-center">
          <div className="size-14 rounded-full bg-green-100 dark:bg-green-900/50 flex items-center justify-center">
            <Sparkles className="size-7 text-green-600 dark:text-green-400" />
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-green-800 dark:text-green-200">
            Touchless Processing Complete
          </h3>
          <p className="text-sm text-green-600 dark:text-green-400 mt-1">
            Invoice auto-approved and posted to ledger — zero manual intervention
          </p>
        </div>

        <div className="flex items-center justify-center gap-4 text-xs text-green-700 dark:text-green-300">
          <div className="flex items-center gap-1">
            <Clock className="size-3.5" />
            <span>{seconds}s total</span>
          </div>
          {postedAt && (
            <div className="flex items-center gap-1">
              <CheckCircle className="size-3.5" />
              <span>Posted {new Date(postedAt).toLocaleString()}</span>
            </div>
          )}
        </div>

        <Link href={`/invoices/${invoiceId}`}>
          <Button variant="outline" size="sm" className="border-green-300 text-green-700 hover:bg-green-100 dark:border-green-700 dark:text-green-300 dark:hover:bg-green-900/30">
            View Invoice
          </Button>
        </Link>
      </CardContent>
    </Card>
  )
}
