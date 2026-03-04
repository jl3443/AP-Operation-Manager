"use client"

import { Sparkles } from "lucide-react"
import { useAiSummary } from "@/hooks/use-analytics"
import { Skeleton } from "@/components/ui/skeleton"

export function AiSummaryCard({ page }: { page: "analytics" | "dashboard" }) {
  const { data, isLoading, isError } = useAiSummary(page)

  return (
    <div className="relative rounded-lg border bg-gradient-to-r from-blue-50/80 to-purple-50/80 dark:from-blue-950/30 dark:to-purple-950/30 px-4 py-3">
      <div className="flex items-start gap-3">
        <div className="rounded-md bg-gradient-to-br from-blue-500 to-purple-500 p-1.5 mt-0.5 shrink-0">
          <Sparkles className="size-3.5 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
            AI Insights
          </p>
          {isLoading ? (
            <div className="space-y-1.5">
              <Skeleton className="h-3.5 w-full" />
              <Skeleton className="h-3.5 w-4/5" />
              <Skeleton className="h-3.5 w-3/5" />
            </div>
          ) : isError ? (
            <p className="text-sm text-muted-foreground leading-relaxed">
              Unable to generate AI insights at this time.
            </p>
          ) : (
            <p className="text-sm leading-relaxed text-foreground/80">
              {data?.summary}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
