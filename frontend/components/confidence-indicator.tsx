import { cn } from "@/lib/utils"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"

interface ConfidenceIndicatorProps {
  confidence: number // 0-100
  className?: string
  showLabel?: boolean
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 90) return "bg-green-500"
  if (confidence >= 70) return "bg-amber-500"
  return "bg-red-500"
}

function getConfidenceLabel(confidence: number): string {
  if (confidence >= 90) return "High"
  if (confidence >= 70) return "Medium"
  return "Low"
}

export function ConfidenceIndicator({
  confidence,
  className,
  showLabel = false,
}: ConfidenceIndicatorProps) {
  const color = getConfidenceColor(confidence)
  const label = getConfidenceLabel(confidence)

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className={cn("flex items-center gap-1.5", className)}>
          <span
            className={cn("inline-block size-2.5 rounded-full shrink-0", color)}
            aria-label={`${label} confidence: ${confidence}%`}
          />
          {showLabel && (
            <span className="text-xs text-muted-foreground">
              {confidence}%
            </span>
          )}
        </div>
      </TooltipTrigger>
      <TooltipContent>
        <p>AI Confidence: {confidence}% ({label})</p>
      </TooltipContent>
    </Tooltip>
  )
}
