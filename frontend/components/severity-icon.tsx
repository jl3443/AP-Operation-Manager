import {
  AlertCircle,
  AlertTriangle,
  ArrowDown,
  Flame,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { ExceptionSeverity } from "@/lib/types"

const severityConfig: Record<
  ExceptionSeverity,
  { icon: React.ElementType; className: string; label: string }
> = {
  low: {
    icon: ArrowDown,
    className: "text-blue-500",
    label: "Low",
  },
  medium: {
    icon: AlertTriangle,
    className: "text-amber-500",
    label: "Medium",
  },
  high: {
    icon: AlertCircle,
    className: "text-orange-500",
    label: "High",
  },
  critical: {
    icon: Flame,
    className: "text-red-500",
    label: "Critical",
  },
}

interface SeverityIconProps {
  severity: ExceptionSeverity
  showLabel?: boolean
  className?: string
}

export function SeverityIcon({ severity, showLabel = false, className }: SeverityIconProps) {
  const config = severityConfig[severity]
  const Icon = config.icon

  return (
    <div className={cn("flex items-center gap-1.5", className)}>
      <Icon className={cn("size-4", config.className)} />
      {showLabel && (
        <span className={cn("text-sm font-medium", config.className)}>
          {config.label}
        </span>
      )}
    </div>
  )
}
