"use client"

import {
  FileText,
  Clock,
  AlertTriangle,
  TrendingUp,
  ArrowRight,
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
import { useInvoices } from "@/hooks/use-invoices"
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
  const { data: invoiceData, isLoading: invoicesLoading } = useInvoices({
    page: 1,
    page_size: 5,
    sort_by: "created_at",
    sort_order: "desc",
  })

  const funnelChartData = funnel?.stages.map((s) => ({
    stage: s.stage.charAt(0).toUpperCase() + s.stage.slice(1).replaceAll("_", " "),
    count: s.count,
    fill: funnelColors[s.stage] ?? "oklch(0.60 0.10 250)",
  })) ?? []

  const vendorChartData = topVendors?.map((v, i) => ({
    name: v.vendor_name,
    invoices: v.invoice_count,
    fill: vendorColors[i % vendorColors.length],
  })) ?? []

  const vendorConfigDynamic: ChartConfig = {
    invoices: { label: "Invoices" },
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

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpisLoading ? (
          <>
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
          </>
        )}
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Invoice Processing Funnel */}
        {funnelLoading ? (
          <ChartSkeleton />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Invoice Processing Funnel</CardTitle>
            </CardHeader>
            <CardContent>
              <ChartContainer config={funnelConfig} className="h-[250px] w-full">
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
                    fontSize={12}
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
            <CardHeader>
              <CardTitle className="text-base">Invoice Volume Trend</CardTitle>
            </CardHeader>
            <CardContent>
              {trendChartData.length === 0 ? (
                <div className="flex items-center justify-center h-[250px] text-sm text-muted-foreground">
                  No trend data available
                </div>
              ) : (
                <ChartContainer config={trendConfig} className="h-[250px] w-full">
                  <LineChart data={trendChartData} margin={{ left: 10, right: 20, top: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickLine={false}
                      axisLine={false}
                      fontSize={12}
                    />
                    <YAxis
                      tickLine={false}
                      axisLine={false}
                      fontSize={12}
                    />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Line
                      dataKey="value"
                      type="monotone"
                      stroke="var(--color-value)"
                      strokeWidth={2}
                      dot={{ fill: "var(--color-value)", r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ChartContainer>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Bottom Row */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Recent Invoices */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Recent Invoices</CardTitle>
            <CardAction>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/invoices" className="gap-1">
                  View All <ArrowRight className="size-3" />
                </Link>
              </Button>
            </CardAction>
          </CardHeader>
          <CardContent>
            {invoicesLoading ? (
              <TableSkeleton rows={5} cols={4} />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Invoice #</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {invoiceData?.items.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                        No invoices yet. Upload or import data to get started.
                      </TableCell>
                    </TableRow>
                  )}
                  {invoiceData?.items.map((invoice) => (
                    <TableRow key={invoice.id}>
                      <TableCell>
                        <Link
                          href={`/invoices/${invoice.id}`}
                          className="font-medium text-primary hover:underline"
                        >
                          {invoice.invoice_number}
                        </Link>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {invoice.invoice_date}
                      </TableCell>
                      <TableCell className="text-right font-mono">
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

        {/* Top Vendors */}
        {vendorsLoading ? (
          <ChartSkeleton />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Top Vendors by Volume</CardTitle>
            </CardHeader>
            <CardContent>
              {vendorChartData.length === 0 ? (
                <div className="flex items-center justify-center h-[280px] text-sm text-muted-foreground">
                  No vendor data available
                </div>
              ) : (
                <ChartContainer config={vendorConfigDynamic} className="h-[280px] w-full">
                  <BarChart data={vendorChartData} margin={{ left: 0, right: 10 }}>
                    <CartesianGrid vertical={false} strokeDasharray="3 3" />
                    <XAxis
                      dataKey="name"
                      tickLine={false}
                      axisLine={false}
                      fontSize={11}
                      angle={-20}
                      textAnchor="end"
                      height={50}
                    />
                    <YAxis tickLine={false} axisLine={false} fontSize={12} />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Bar dataKey="invoices" radius={[4, 4, 0, 0]} />
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
