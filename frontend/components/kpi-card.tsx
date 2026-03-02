import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { ArrowDown, ArrowUp, Minus } from "lucide-react"

interface KpiCardProps {
  title: string
  value: string | number
  icon: React.ElementType
  trend?: {
    value: number
    label: string
  }
  className?: string
}

export function KpiCard({ title, value, icon: Icon, trend, className }: KpiCardProps) {
  return (
    <Card className={cn("gap-0 py-4", className)}>
      <CardContent className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground font-medium">{title}</p>
          <p className="text-2xl font-bold tracking-tight">{value}</p>
          {trend && (
            <div className="flex items-center gap-1 text-xs">
              {trend.value > 0 ? (
                <ArrowUp className="size-3 text-green-600" />
              ) : trend.value < 0 ? (
                <ArrowDown className="size-3 text-red-600" />
              ) : (
                <Minus className="size-3 text-muted-foreground" />
              )}
              <span
                className={cn(
                  "font-medium",
                  trend.value > 0 && "text-green-600",
                  trend.value < 0 && "text-red-600",
                  trend.value === 0 && "text-muted-foreground",
                )}
              >
                {Math.abs(trend.value)}%
              </span>
              <span className="text-muted-foreground">{trend.label}</span>
            </div>
          )}
        </div>
        <div className="rounded-lg bg-primary/10 p-2.5">
          <Icon className="size-5 text-primary" />
        </div>
      </CardContent>
    </Card>
  )
}
