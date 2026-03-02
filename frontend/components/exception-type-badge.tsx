import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { ExceptionType } from "@/lib/types"

const exceptionConfig: Record<ExceptionType, { label: string; className: string }> = {
  missing_po: {
    label: "Missing PO",
    className: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300",
  },
  amount_variance: {
    label: "Amount Variance",
    className: "bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950 dark:text-orange-300",
  },
  quantity_variance: {
    label: "Qty Variance",
    className: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300",
  },
  duplicate_invoice: {
    label: "Duplicate",
    className: "bg-pink-50 text-pink-700 border-pink-200 dark:bg-pink-950 dark:text-pink-300",
  },
  vendor_mismatch: {
    label: "Vendor Mismatch",
    className: "bg-violet-50 text-violet-700 border-violet-200 dark:bg-violet-950 dark:text-violet-300",
  },
  tax_variance: {
    label: "Tax Variance",
    className: "bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950 dark:text-indigo-300",
  },
  expired_po: {
    label: "Expired PO",
    className: "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950 dark:text-rose-300",
  },
  prepayment: {
    label: "Prepayment",
    className: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300",
  },
  currency_variance: {
    label: "Currency Var.",
    className: "bg-cyan-50 text-cyan-700 border-cyan-200 dark:bg-cyan-950 dark:text-cyan-300",
  },
  contract_price_variance: {
    label: "Contract Price",
    className: "bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950 dark:text-teal-300",
  },
  vendor_on_hold: {
    label: "Vendor On-Hold",
    className: "bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-950 dark:text-yellow-300",
  },
  partial_delivery_overrun: {
    label: "Delivery Overrun",
    className: "bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-950 dark:text-slate-300",
  },
}

interface ExceptionTypeBadgeProps {
  type: ExceptionType
  className?: string
}

export function ExceptionTypeBadge({ type, className }: ExceptionTypeBadgeProps) {
  const config = exceptionConfig[type]

  return (
    <Badge variant="outline" className={cn(config?.className, className)}>
      {config?.label ?? type}
    </Badge>
  )
}
