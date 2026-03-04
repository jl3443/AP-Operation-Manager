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
} from "recharts"
import { Printer } from "lucide-react"

import {
  useAgingAnalysis,
  useExceptionBreakdown,
  useVendorRiskDistribution,
  useMonthlyComparison,
  useApprovalTurnaround,
} from "@/hooks/use-analytics"
import { AiSummaryCard } from "@/components/ai-summary-card"
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

// -- Compact legend for pie/donut charts --

function PieLegend({ data }: { data: { name: string; fill: string; percentage?: number }[] }) {
  return (
    <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 mt-1">
      {data.map((item) => (
        <div key={item.name} className="flex items-center gap-1.5">
          <span
            className="inline-block size-2.5 rounded-full shrink-0"
            style={{ backgroundColor: item.fill }}
          />
          <span className="text-[11px] text-muted-foreground capitalize">
            {item.name}
            {item.percentage != null && ` (${item.percentage.toFixed(0)}%)`}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function AnalyticsPage() {
  const { data: aging, isLoading: agingLoading } = useAgingAnalysis()
  const { data: exceptions, isLoading: exceptionsLoading } = useExceptionBreakdown()
  const { data: monthly, isLoading: monthlyLoading } = useMonthlyComparison()
  const { data: riskDist, isLoading: riskLoading } = useVendorRiskDistribution()
  const { data: turnaround, isLoading: turnaroundLoading } = useApprovalTurnaround()

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
    window.print()
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Analytics</h1>
          <p className="text-sm text-muted-foreground">
            In-depth analytics across invoices, exceptions, vendors, and approvals.
          </p>
        </div>
        <Button onClick={handleExportPdf} size="sm" variant="outline">
          <Printer className="size-4 mr-2" />
          Export PDF
        </Button>
      </div>

      {/* AI Summary */}
      <AiSummaryCard page="analytics" />

      {/* Row 1: Aging + Exception Breakdown */}
      <div className="grid gap-3 lg:grid-cols-2">
        {/* Invoice Aging Analysis */}
        {agingLoading ? (
          <ChartSkeleton />
        ) : (
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-sm font-medium tracking-tight">Invoice Aging Analysis</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {agingChartData.length === 0 ? (
                <div className="flex items-center justify-center h-[200px] text-sm text-muted-foreground">
                  No data available
                </div>
              ) : (
                <ChartContainer config={agingConfig} className="h-[200px] w-full">
                  <BarChart data={agingChartData} margin={{ left: 10, right: 20 }}>
                    <CartesianGrid vertical={false} strokeDasharray="3 3" />
                    <XAxis
                      dataKey="bucket"
                      tickLine={false}
                      axisLine={false}
                      fontSize={11}
                    />
                    <YAxis tickLine={false} axisLine={false} fontSize={11} />
                    <ChartTooltip content={<ChartTooltipContent />} />
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
            <CardHeader className="py-3">
              <CardTitle className="text-sm font-medium tracking-tight">Exception Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {exceptionChartData.length === 0 ? (
                <div className="flex items-center justify-center h-[200px] text-sm text-muted-foreground">
                  No data available
                </div>
              ) : (
                <>
                  <ChartContainer config={exceptionConfig} className="h-[160px] w-full">
                    <PieChart>
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Pie
                        data={exceptionChartData}
                        dataKey="count"
                        nameKey="name"
                        innerRadius={40}
                        outerRadius={68}
                        paddingAngle={2}
                      >
                        {exceptionChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ChartContainer>
                  <PieLegend data={exceptionChartData} />
                </>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Row 2: Monthly + Vendor Risk + Approval Turnaround */}
      <div className="grid gap-3 lg:grid-cols-3">
        {/* Monthly Invoice Comparison */}
        {monthlyLoading ? (
          <ChartSkeleton />
        ) : (
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-sm font-medium tracking-tight">Monthly Comparison</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {monthlyChartData.length === 0 ? (
                <div className="flex items-center justify-center h-[200px] text-sm text-muted-foreground">
                  No data available
                </div>
              ) : (
                <ChartContainer config={monthlyConfig} className="h-[200px] w-full">
                  <BarChart data={monthlyChartData} margin={{ left: 10, right: 20 }}>
                    <CartesianGrid vertical={false} strokeDasharray="3 3" />
                    <XAxis
                      dataKey="month"
                      tickLine={false}
                      axisLine={false}
                      fontSize={11}
                    />
                    <YAxis tickLine={false} axisLine={false} fontSize={11} />
                    <ChartTooltip content={<ChartTooltipContent />} />
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
            <CardHeader className="py-3">
              <CardTitle className="text-sm font-medium tracking-tight">Vendor Risk</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {riskChartData.length === 0 ? (
                <div className="flex items-center justify-center h-[200px] text-sm text-muted-foreground">
                  No data available
                </div>
              ) : (
                <>
                  <ChartContainer config={riskConfig} className="h-[160px] w-full">
                    <PieChart>
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Pie
                        data={riskChartData}
                        dataKey="count"
                        nameKey="name"
                        innerRadius={40}
                        outerRadius={68}
                        paddingAngle={2}
                      >
                        {riskChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ChartContainer>
                  <PieLegend data={riskChartData} />
                </>
              )}
            </CardContent>
          </Card>
        )}

        {/* Approval Turnaround Time */}
        {turnaroundLoading ? (
          <ChartSkeleton />
        ) : (
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-sm font-medium tracking-tight">Approval Turnaround</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {turnaroundChartData.length === 0 ? (
                <div className="flex items-center justify-center h-[200px] text-sm text-muted-foreground">
                  No data available
                </div>
              ) : (
                <ChartContainer config={turnaroundConfig} className="h-[200px] w-full">
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
                      fontSize={11}
                    />
                    <YAxis tickLine={false} axisLine={false} fontSize={11} />
                    <ChartTooltip content={<ChartTooltipContent />} />
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
    </div>
  )
}
