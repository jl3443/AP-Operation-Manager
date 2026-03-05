"use client"

import {
  FileText,
  Clock,
  AlertTriangle,
  TrendingUp,
  ArrowRight,
  Zap,
  Timer,
  Printer,
  Sparkles,
  BrainCircuit,
  CheckCircle2,
  XCircle,
  DollarSign,
} from "lucide-react"
import Link from "next/link"
import {
  Bar,
  BarChart,
  Line,
  LineChart,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts"

import { useDashboardKPIs, useFunnelData, useTopVendors, useTrends } from "@/hooks/use-dashboard"
import { useTouchlessRate } from "@/hooks/use-compliance"
import { useInvoices } from "@/hooks/use-invoices"
import { useAiSummary } from "@/hooks/use-analytics"
import { KpiCard } from "@/components/kpi-card"
import { InvoiceStatusBadge } from "@/components/invoice-status-badge"
import { KpiCardSkeleton, ChartSkeleton, TableSkeleton } from "@/components/loading-skeleton"
import { QueryError } from "@/components/query-error"
import { Card, CardContent, CardHeader, CardTitle, CardAction } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"

const funnelColors: Record<string, string> = {
  draft: "oklch(0.70 0.10 250)",
  extracted: "oklch(0.65 0.15 255)",
  matching: "oklch(0.60 0.15 220)",
  exception: "oklch(0.60 0.15 30)",
  pending_approval: "oklch(0.55 0.15 55)",
  approved: "oklch(0.55 0.15 160)",
  rejected: "oklch(0.55 0.15 15)",
  posted: "oklch(0.50 0.15 145)",
}

const funnelConfig = {
  count: { label: "Invoices" },
  amount: { label: "Amount ($)" },
  draft: { label: "Draft", color: funnelColors.draft },
  extracted: { label: "Extracted", color: funnelColors.extracted },
  matching: { label: "Matching", color: funnelColors.matching },
  exception: { label: "Exception", color: funnelColors.exception },
  pending_approval: { label: "Pending Approval", color: funnelColors.pending_approval },
  approved: { label: "Approved", color: funnelColors.approved },
  rejected: { label: "Rejected", color: funnelColors.rejected },
  posted: { label: "Posted", color: funnelColors.posted },
} satisfies ChartConfig

const trendConfig = {
  value: { label: "Invoice Count", color: "oklch(0.55 0.15 160)" },
} satisfies ChartConfig

const vendorColors = [
  "oklch(0.55 0.15 255)",
  "oklch(0.60 0.12 220)",
  "oklch(0.55 0.12 195)",
  "oklch(0.58 0.12 165)",
  "oklch(0.50 0.12 145)",
]

export default function DashboardPage() {
  const { data: kpis, isLoading: kpisLoading, error: kpisError, refetch: refetchKpis } = useDashboardKPIs()
  const { data: funnel, isLoading: funnelLoading } = useFunnelData()
  const { data: topVendors, isLoading: vendorsLoading } = useTopVendors(5)
  const { data: trends, isLoading: trendsLoading } = useTrends(180)
  const { data: touchless, isLoading: touchlessLoading } = useTouchlessRate()
  const { data: invoiceData, isLoading: invoicesLoading } = useInvoices({
    page: 1,
    page_size: 2,
    sort_by: "created_at",
    sort_order: "desc",
  })
  const { data: aiSummary, isLoading: aiLoading } = useAiSummary("dashboard")
  const funnelChartData = funnel?.stages.map((s) => ({
    stage: s.stage.charAt(0).toUpperCase() + s.stage.slice(1).replaceAll("_", " "),
    count: s.count,
    amount: s.amount,
    fill: funnelColors[s.stage] ?? "oklch(0.60 0.10 250)",
  })) ?? []

  const vendorChartData = topVendors?.map((v, i) => ({
    name: v.vendor_name,
    invoices: v.invoice_count,
    amount: v.total_amount,
    fill: vendorColors[i % vendorColors.length],
  })) ?? []

  const vendorConfigDynamic: ChartConfig = {
    invoices: { label: "Invoices" },
    amount: { label: "Amount ($)" },
    ...Object.fromEntries(
      (topVendors ?? []).map((v, i) => [
        v.vendor_name.toLowerCase().replace(/\s+/g, ""),
        { label: v.vendor_name, color: vendorColors[i % vendorColors.length] },
      ])
    ),
  }

  const trendChartData = (trends?.[0]?.data_points ?? []).map((p) => ({
    date: new Date(p.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    value: p.value,
  }))

  function handleExportPdf() {
    window.print()
  }

  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>
        </div>
        <Button onClick={handleExportPdf} size="sm" variant="outline">
          <Printer className="size-4 mr-2" />
          Export PDF
        </Button>
      </div>

      {/* AI Insights Hero */}
      <Card className="overflow-hidden border-0 shadow-sm bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 text-white">
        <CardContent className="py-4 px-5">
          <div className="flex items-start gap-4">
            <div className="rounded-xl bg-white/10 backdrop-blur-sm p-2.5 shrink-0 ring-1 ring-white/20">
              <BrainCircuit className="size-5 text-blue-300" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1.5">
                <h3 className="text-sm font-semibold tracking-tight text-white/90">AI Insights</h3>
                <Sparkles className="size-3.5 text-amber-300" />
              </div>
              {aiLoading ? (
                <div className="space-y-1.5">
                  <div className="h-3.5 w-full rounded bg-white/10 animate-pulse" />
                  <div className="h-3.5 w-3/4 rounded bg-white/10 animate-pulse" />
                </div>
              ) : (
                <p className="text-sm leading-relaxed text-blue-100/80">
                  {aiSummary?.summary ?? "AI insights will appear once data is available."}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* KPI Cards */}
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {kpisLoading ? (
          <>
            <KpiCardSkeleton />
            <KpiCardSkeleton />
            <KpiCardSkeleton />
            <KpiCardSkeleton />
            <KpiCardSkeleton />
            <KpiCardSkeleton />
          </>
        ) : kpisError ? (
          <div className="col-span-full">
            <QueryError error={kpisError} retry={() => refetchKpis()} />
          </div>
        ) : (
          <>
            <KpiCard
              title="Total Invoices"
              value={kpis?.total_invoices.toLocaleString() ?? "0"}
              icon={FileText}
            />
            <KpiCard
              title="Pending Approval"
              value={kpis?.pending_approval.toString() ?? "0"}
              icon={Clock}
            />
            <KpiCard
              title="Open Exceptions"
              value={kpis?.open_exceptions.toString() ?? "0"}
              icon={AlertTriangle}
            />
            <KpiCard
              title="Match Rate"
              value={`${kpis?.match_rate_pct.toFixed(1) ?? "0"}%`}
              icon={TrendingUp}
            />
            <KpiCard
              title="Touchless Rate"
              value={`${touchless?.rate.toFixed(1) ?? "0"}%`}
              icon={Zap}
            />
            <KpiCard
              title="Avg Cycle Time"
              value={`${touchless?.cycle_time_avg_hours.toFixed(1) ?? "0"}h`}
              icon={Timer}
            />
          </>
        )}
      </div>

      {/* Amount KPI Cards */}
      <div className="grid gap-2 sm:grid-cols-3">
        {kpisLoading ? (
          <>
            <KpiCardSkeleton />
            <KpiCardSkeleton />
            <KpiCardSkeleton />
          </>
        ) : (
          <>
            <KpiCard
              title="Pending Amount"
              value={`$${(kpis?.total_amount_pending ?? 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              icon={DollarSign}
            />
            <KpiCard
              title="Approved Amount"
              value={`$${(kpis?.total_amount_approved ?? 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              icon={CheckCircle2}
            />
            <KpiCard
              title="Rejected Amount"
              value={`$${(kpis?.total_amount_rejected ?? 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              icon={XCircle}
            />
          </>
        )}
      </div>

      {/* Charts Row: Funnel + Trend + Top Vendors */}
      <div className="grid gap-2 lg:grid-cols-3">
        {/* Invoice Processing Funnel */}
        {funnelLoading ? (
          <ChartSkeleton />
        ) : (
          <Card>
            <CardHeader className="py-2">
              <CardTitle className="text-sm font-medium tracking-tight">Processing Funnel</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <ChartContainer config={funnelConfig} className="h-[140px] w-full">
                <BarChart
                  data={funnelChartData}
                  layout="vertical"
                  margin={{ left: 10, right: 20 }}
                >
                  <CartesianGrid horizontal={false} strokeDasharray="3 3" />
                  <YAxis
                    dataKey="stage"
                    type="category"
                    tickLine={false}
                    axisLine={false}
                    width={100}
                    fontSize={11}
                  />
                  <XAxis type="number" hide />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ChartContainer>
            </CardContent>
          </Card>
        )}

        {/* Invoice Volume Trend */}
        {trendsLoading ? (
          <ChartSkeleton />
        ) : (
          <Card>
            <CardHeader className="py-2">
              <CardTitle className="text-sm font-medium tracking-tight">Volume Trend</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {trendChartData.length === 0 ? (
                <div className="flex items-center justify-center h-[140px] text-sm text-muted-foreground">
                  No trend data available
                </div>
              ) : (
                <ChartContainer config={trendConfig} className="h-[140px] w-full">
                  <LineChart data={trendChartData} margin={{ left: 10, right: 20, top: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickLine={false}
                      axisLine={false}
                      fontSize={11}
                    />
                    <YAxis
                      tickLine={false}
                      axisLine={false}
                      fontSize={11}
                    />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Line
                      dataKey="value"
                      type="monotone"
                      stroke="var(--color-value)"
                      strokeWidth={2}
                      dot={{ fill: "var(--color-value)", r: 3 }}
                      activeDot={{ r: 5 }}
                    />
                  </LineChart>
                </ChartContainer>
              )}
            </CardContent>
          </Card>
        )}

        {/* Top Vendors */}
        {vendorsLoading ? (
          <ChartSkeleton />
        ) : (
          <Card>
            <CardHeader className="py-2">
              <CardTitle className="text-sm font-medium tracking-tight">Top Vendors</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {vendorChartData.length === 0 ? (
                <div className="flex items-center justify-center h-[140px] text-sm text-muted-foreground">
                  No vendor data available
                </div>
              ) : (
                <ChartContainer config={vendorConfigDynamic} className="h-[140px] w-full">
                  <BarChart data={vendorChartData} margin={{ left: 0, right: 10 }}>
                    <CartesianGrid vertical={false} strokeDasharray="3 3" />
                    <XAxis
                      dataKey="name"
                      tickLine={false}
                      axisLine={false}
                      fontSize={10}
                      angle={-15}
                      textAnchor="end"
                      height={40}
                    />
                    <YAxis tickLine={false} axisLine={false} fontSize={11} />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Bar dataKey="invoices" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ChartContainer>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Recent Invoices Table */}
      <Card>
        <CardHeader className="py-2">
          <CardTitle className="text-sm font-medium tracking-tight">Recent Invoices</CardTitle>
          <CardAction>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/invoices" className="gap-1 text-xs">
                View All <ArrowRight className="size-3" />
              </Link>
            </Button>
          </CardAction>
        </CardHeader>
        <CardContent className="pt-0">
          {invoicesLoading ? (
            <TableSkeleton rows={2} cols={4} />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Invoice #</TableHead>
                  <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Date</TableHead>
                  <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground text-right">Amount</TableHead>
                  <TableHead className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invoiceData?.items.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground py-6">
                      No invoices yet. Upload or import data to get started.
                    </TableCell>
                  </TableRow>
                )}
                {invoiceData?.items.map((invoice) => (
                  <TableRow key={invoice.id}>
                    <TableCell>
                      <Link
                        href={`/invoices/${invoice.id}`}
                        className="text-sm font-medium text-primary hover:underline"
                      >
                        {invoice.invoice_number}
                      </Link>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {invoice.invoice_date}
                    </TableCell>
                    <TableCell className="text-right text-sm font-mono tabular-nums">
                      ${invoice.total_amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                    </TableCell>
                    <TableCell>
                      <InvoiceStatusBadge status={invoice.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
