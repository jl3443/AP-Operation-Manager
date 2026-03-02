"use client"

import {
  Bar,
  BarChart,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts"
import { Download, Loader2 } from "lucide-react"
import { toast } from "sonner"

import {
  useAgingAnalysis,
  useExceptionBreakdown,
  useVendorRiskDistribution,
  useMonthlyComparison,
  useApprovalTurnaround,
  useExportPdfReport,
} from "@/hooks/use-analytics"
import { ChartSkeleton } from "@/components/loading-skeleton"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"

// -- Color schemes --

const agingColors: Record<string, string> = {
  Current: "oklch(0.55 0.15 145)",
  "1-30 Days": "oklch(0.65 0.15 85)",
  "31-60 Days": "oklch(0.60 0.15 55)",
  "61-90 Days": "oklch(0.55 0.15 30)",
  "90+ Days": "oklch(0.50 0.18 15)",
}

const exceptionColors = [
  "oklch(0.55 0.15 255)",
  "oklch(0.60 0.12 220)",
  "oklch(0.55 0.12 195)",
  "oklch(0.58 0.12 165)",
  "oklch(0.50 0.15 145)",
  "oklch(0.60 0.15 55)",
  "oklch(0.55 0.15 30)",
  "oklch(0.50 0.18 15)",
]

const riskColors: Record<string, string> = {
  low: "oklch(0.55 0.15 145)",
  medium: "oklch(0.65 0.15 85)",
  high: "oklch(0.50 0.18 15)",
}

// -- Chart configs --

const agingConfig = {
  count: { label: "Invoices" },
  amount: { label: "Amount" },
} satisfies ChartConfig

const exceptionConfig = {
  count: { label: "Count" },
} satisfies ChartConfig

const monthlyConfig = {
  invoice_count: { label: "Invoice Count", color: "oklch(0.55 0.15 255)" },
} satisfies ChartConfig

const riskConfig = {
  count: { label: "Count" },
} satisfies ChartConfig

const turnaroundConfig = {
  avg_hours: { label: "Avg Hours", color: "oklch(0.55 0.15 255)" },
} satisfies ChartConfig

// -- Custom label renderer for donut charts --

function renderPieLabel({
  name,
  percentage,
  x,
  y,
}: {
  name: string
  percentage: number
  x: number
  y: number
}) {
  return (
    <text x={x} y={y} textAnchor="middle" dominantBaseline="central" className="text-xs fill-foreground">
      {`${name} (${percentage.toFixed(1)}%)`}
    </text>
  )
}

export default function AnalyticsPage() {
  const { data: aging, isLoading: agingLoading } = useAgingAnalysis()
  const { data: exceptions, isLoading: exceptionsLoading } = useExceptionBreakdown()
  const { data: monthly, isLoading: monthlyLoading } = useMonthlyComparison()
  const { data: riskDist, isLoading: riskLoading } = useVendorRiskDistribution()
  const { data: turnaround, isLoading: turnaroundLoading } = useApprovalTurnaround()
  const exportPdf = useExportPdfReport()

  // -- Transform data --

  const agingChartData =
    aging?.buckets.map((b) => ({
      bucket: b.bucket,
      count: b.count,
      amount: b.amount,
      fill: agingColors[b.bucket] ?? "oklch(0.60 0.10 250)",
    })) ?? []

  const exceptionChartData =
    exceptions?.map((e, i) => ({
      name: e.exception_type.replaceAll("_", " "),
      count: e.count,
      percentage: e.percentage,
      fill: exceptionColors[i % exceptionColors.length],
    })) ?? []

  const monthlyChartData =
    monthly?.map((m) => ({
      month: m.month,
      invoice_count: m.invoice_count,
      total_amount: m.total_amount,
    })) ?? []

  const riskChartData =
    riskDist?.map((r) => ({
      name: r.risk_level,
      count: r.count,
      percentage: r.percentage,
      fill: riskColors[r.risk_level] ?? "oklch(0.60 0.10 250)",
    })) ?? []

  const turnaroundChartData =
    turnaround?.map((t) => ({
      level: `Level ${t.level}`,
      avg_hours: t.avg_hours,
      total_tasks: t.total_tasks,
    })) ?? []

  function handleExportPdf() {
    exportPdf.mutate(undefined, {
      onSuccess: () => {
        toast.success("PDF report downloaded successfully")
      },
      onError: () => {
        toast.error("Failed to export PDF report")
      },
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          In-depth analytics across invoices, exceptions, vendors, and approvals.
        </p>
        <Button onClick={handleExportPdf} disabled={exportPdf.isPending} size="sm">
          {exportPdf.isPending ? (
            <Loader2 className="size-4 animate-spin mr-2" />
          ) : (
            <Download className="size-4 mr-2" />
          )}
          Export PDF Report
        </Button>
      </div>

      {/* Row 1: Aging + Exception Breakdown */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Invoice Aging Analysis */}
        {agingLoading ? (
          <ChartSkeleton />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Invoice Aging Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              {agingChartData.length === 0 ? (
                <div className="flex items-center justify-center h-[300px] text-sm text-muted-foreground">
                  No data available
                </div>
              ) : (
                <ChartContainer config={agingConfig} className="h-[300px] w-full">
                  <BarChart data={agingChartData} margin={{ left: 10, right: 20 }}>
                    <CartesianGrid vertical={false} strokeDasharray="3 3" />
                    <XAxis
                      dataKey="bucket"
                      tickLine={false}
                      axisLine={false}
                      fontSize={12}
                    />
                    <YAxis tickLine={false} axisLine={false} fontSize={12} />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Legend />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ChartContainer>
              )}
            </CardContent>
          </Card>
        )}

        {/* Exception Breakdown by Type */}
        {exceptionsLoading ? (
          <ChartSkeleton />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Exception Breakdown by Type</CardTitle>
            </CardHeader>
            <CardContent>
              {exceptionChartData.length === 0 ? (
                <div className="flex items-center justify-center h-[300px] text-sm text-muted-foreground">
                  No data available
                </div>
              ) : (
                <ChartContainer config={exceptionConfig} className="h-[300px] w-full">
                  <PieChart>
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Pie
                      data={exceptionChartData}
                      dataKey="count"
                      nameKey="name"
                      innerRadius={60}
                      outerRadius={100}
                      label={({ name, percentage, x, y }) =>
                        renderPieLabel({ name, percentage, x, y })
                      }
                    >
                      {exceptionChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                  </PieChart>
                </ChartContainer>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Row 2: Monthly Comparison + Vendor Risk */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Monthly Invoice Comparison */}
        {monthlyLoading ? (
          <ChartSkeleton />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Monthly Invoice Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              {monthlyChartData.length === 0 ? (
                <div className="flex items-center justify-center h-[300px] text-sm text-muted-foreground">
                  No data available
                </div>
              ) : (
                <ChartContainer config={monthlyConfig} className="h-[300px] w-full">
                  <BarChart data={monthlyChartData} margin={{ left: 10, right: 20 }}>
                    <CartesianGrid vertical={false} strokeDasharray="3 3" />
                    <XAxis
                      dataKey="month"
                      tickLine={false}
                      axisLine={false}
                      fontSize={12}
                    />
                    <YAxis tickLine={false} axisLine={false} fontSize={12} />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Legend />
                    <Bar
                      dataKey="invoice_count"
                      fill="var(--color-invoice_count)"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ChartContainer>
              )}
            </CardContent>
          </Card>
        )}

        {/* Vendor Risk Distribution */}
        {riskLoading ? (
          <ChartSkeleton />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Vendor Risk Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              {riskChartData.length === 0 ? (
                <div className="flex items-center justify-center h-[300px] text-sm text-muted-foreground">
                  No data available
                </div>
              ) : (
                <ChartContainer config={riskConfig} className="h-[300px] w-full">
                  <PieChart>
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Pie
                      data={riskChartData}
                      dataKey="count"
                      nameKey="name"
                      innerRadius={60}
                      outerRadius={100}
                      label={({ name, percentage, x, y }) =>
                        renderPieLabel({ name, percentage, x, y })
                      }
                    >
                      {riskChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                  </PieChart>
                </ChartContainer>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Row 3: Approval Turnaround */}
      {turnaroundLoading ? (
        <ChartSkeleton />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Approval Turnaround Time</CardTitle>
          </CardHeader>
          <CardContent>
            {turnaroundChartData.length === 0 ? (
              <div className="flex items-center justify-center h-[300px] text-sm text-muted-foreground">
                No data available
              </div>
            ) : (
              <ChartContainer config={turnaroundConfig} className="h-[300px] w-full">
                <BarChart
                  data={turnaroundChartData}
                  layout="horizontal"
                  margin={{ left: 10, right: 20 }}
                >
                  <CartesianGrid vertical={false} strokeDasharray="3 3" />
                  <XAxis
                    dataKey="level"
                    tickLine={false}
                    axisLine={false}
                    fontSize={12}
                  />
                  <YAxis tickLine={false} axisLine={false} fontSize={12} />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Legend />
                  <Bar
                    dataKey="avg_hours"
                    fill="var(--color-avg_hours)"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ChartContainer>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
