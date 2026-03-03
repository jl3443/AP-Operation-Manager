"use client"

import { CheckCircle, Circle, AlertTriangle } from "lucide-react"
import { cn } from "@/lib/utils"

const STEPS = [
  { key: "draft", label: "Draft" },
  { key: "extracted", label: "Extracted" },
  { key: "matching", label: "Matching" },
  { key: "pending_approval", label: "Pending Approval" },
  { key: "approved", label: "Approved" },
  { key: "posted", label: "Posted" },
] as const

const STATUS_ORDER: Record<string, number> = {
  draft: 0,
  extracted: 1,
  matching: 2,
  exception: 2,
  pending_approval: 3,
  approved: 4,
  rejected: 4,
  posted: 5,
}

export function InvoiceProgressStepper({ status }: { status: string }) {
  const currentIndex = STATUS_ORDER[status] ?? 0
  const isException = status === "exception"
  const isRejected = status === "rejected"

  return (
    <div className="flex items-center gap-1 w-full">
      {STEPS.map((step, i) => {
        const isCompleted = i < currentIndex
        const isCurrent = i === currentIndex
        const showWarning = isCurrent && (isException || isRejected)

        return (
          <div key={step.key} className="flex items-center flex-1 last:flex-none">
            <div className="flex flex-col items-center gap-1">
              {isCompleted ? (
                <CheckCircle className="size-5 text-green-500 shrink-0" />
              ) : showWarning ? (
                <AlertTriangle className="size-5 text-amber-500 shrink-0" />
              ) : isCurrent ? (
                <Circle className="size-5 text-primary fill-primary/20 shrink-0" />
              ) : (
                <Circle className="size-5 text-muted-foreground/30 shrink-0" />
              )}
              <span
                className={cn(
                  "text-[10px] whitespace-nowrap",
                  isCompleted && "text-green-600 dark:text-green-400 font-medium",
                  isCurrent && !showWarning && "text-primary font-semibold",
                  showWarning && "text-amber-600 dark:text-amber-400 font-semibold",
                  !isCompleted && !isCurrent && "text-muted-foreground/50",
                )}
              >
                {showWarning
                  ? isException
                    ? "Exception"
                    : "Rejected"
                  : step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={cn(
                  "h-0.5 flex-1 mx-2 mt-[-16px]",
                  i < currentIndex
                    ? "bg-green-500"
                    : "bg-muted-foreground/15",
                )}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
