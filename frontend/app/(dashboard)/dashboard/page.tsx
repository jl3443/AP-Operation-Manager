"use client"

import {
  FileText,
  Clock,
  AlertTriangle,
  TrendingUp,
  Building2,
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
  ResponsiveContainer,
} from "recharts"

import { KpiCard } from "@/components/kpi-card"
import { InvoiceStatusBadge } from "@/components/invoice-status-badge"
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

// -- Mock Data --

const funnelData = [
  { stage: "Received", count: 1245, fill: "var(--color-received)" },
  { stage: "Extracted", count: 1180, fill: "var(--color-extracted)" },
  { stage: "Matched", count: 1020, fill: "var(--color-matched)" },
  { stage: "Approved", count: 945, fill: "var(--color-approved)" },
  { stage: "Posted", count: 890, fill: "var(--color-posted)" },
]

const funnelConfig = {
  count: { label: "Invoices" },
  received: { label: "Received", color: "oklch(0.65 0.15 255)" },
  extracted: { label: "Extracted", color: "oklch(0.60 0.15 220)" },
  matched: { label: "Matched", color: "oklch(0.55 0.15 195)" },
  approved: { label: "Approved", color: "oklch(0.55 0.15 160)" },
  posted: { label: "Posted", color: "oklch(0.50 0.15 145)" },
} satisfies ChartConfig

const automationData = [
  { month: "Jul", rate: 62 },
  { month: "Aug", rate: 65 },
  { month: "Sep", rate: 68 },
  { month: "Oct", rate: 71 },
  { month: "Nov", rate: 75 },
  { month: "Dec", rate: 78 },
  { month: "Jan", rate: 80 },
  { month: "Feb", rate: 83 },
]

const automationConfig = {
  rate: { label: "Automation Rate %", color: "oklch(0.55 0.15 160)" },
} satisfies ChartConfig

const recentInvoices = [
  {
    id: "inv-001",
    number: "INV-2024-0892",
    vendor: "Acme Corp",
    date: "2024-02-28",
    amount: 12450.0,
    status: "pending_approval" as const,
    source: "email",
  },
  {
    id: "inv-002",
    number: "INV-2024-0891",
    vendor: "TechParts Ltd",
    date: "2024-02-28",
    amount: 3280.5,
    status: "matching" as const,
    source: "manual",
  },
  {
    id: "inv-003",
    number: "INV-2024-0890",
    vendor: "Global Supply Co",
    date: "2024-02-27",
    amount: 45670.0,
    status: "exception" as const,
    source: "email",
  },
  {
    id: "inv-004",
    number: "INV-2024-0889",
    vendor: "Office Depot",
    date: "2024-02-27",
    amount: 892.15,
    status: "approved" as const,
    source: "api",
  },
  {
    id: "inv-005",
    number: "INV-2024-0888",
    vendor: "CloudServ Inc",
    date: "2024-02-26",
    amount: 7500.0,
    status: "posted" as const,
    source: "csv",
  },
]

const topVendors = [
  { name: "Acme Corp", invoices: 89, fill: "var(--color-acme)" },
  { name: "TechParts", invoices: 67, fill: "var(--color-techparts)" },
  { name: "Global Supply", invoices: 54, fill: "var(--color-global)" },
  { name: "Office Depot", invoices: 42, fill: "var(--color-office)" },
  { name: "CloudServ", invoices: 38, fill: "var(--color-cloudserv)" },
]

const vendorConfig = {
  invoices: { label: "Invoices" },
  acme: { label: "Acme Corp", color: "oklch(0.55 0.15 255)" },
  techparts: { label: "TechParts", color: "oklch(0.60 0.12 220)" },
  global: { label: "Global Supply", color: "oklch(0.55 0.12 195)" },
  office: { label: "Office Depot", color: "oklch(0.58 0.12 165)" },
  cloudserv: { label: "CloudServ", color: "oklch(0.50 0.12 145)" },
} satisfies ChartConfig

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Total Invoices"
          value="1,245"
          icon={FileText}
          trend={{ value: 12, label: "vs last month" }}
        />
        <KpiCard
          title="Pending"
          value="38"
          icon={Clock}
          trend={{ value: -8, label: "vs last month" }}
        />
        <KpiCard
          title="Exception Rate"
          value="4.2%"
          icon={AlertTriangle}
          trend={{ value: -15, label: "vs last month" }}
        />
        <KpiCard
          title="Avg Cycle Time"
          value="1.8 days"
          icon={TrendingUp}
          trend={{ value: -22, label: "vs last month" }}
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Invoice Processing Funnel */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Invoice Processing Funnel</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={funnelConfig} className="h-[250px] w-full">
              <BarChart
                data={funnelData}
                layout="vertical"
                margin={{ left: 10, right: 20 }}
              >
                <CartesianGrid horizontal={false} strokeDasharray="3 3" />
                <YAxis
                  dataKey="stage"
                  type="category"
                  tickLine={false}
                  axisLine={false}
                  width={80}
                  fontSize={12}
                />
                <XAxis type="number" hide />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Bar dataKey="count" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ChartContainer>
          </CardContent>
        </Card>

        {/* Automation Rate Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Automation Rate Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={automationConfig} className="h-[250px] w-full">
              <LineChart data={automationData} margin={{ left: 10, right: 20, top: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="month"
                  tickLine={false}
                  axisLine={false}
                  fontSize={12}
                />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  fontSize={12}
                  domain={[50, 100]}
                  tickFormatter={(v) => `${v}%`}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line
                  dataKey="rate"
                  type="monotone"
                  stroke="var(--color-rate)"
                  strokeWidth={2}
                  dot={{ fill: "var(--color-rate)", r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ChartContainer>
          </CardContent>
        </Card>
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
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Invoice #</TableHead>
                  <TableHead>Vendor</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentInvoices.map((invoice) => (
                  <TableRow key={invoice.id}>
                    <TableCell>
                      <Link
                        href={`/invoices/${invoice.id}`}
                        className="font-medium text-primary hover:underline"
                      >
                        {invoice.number}
                      </Link>
                    </TableCell>
                    <TableCell>{invoice.vendor}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {invoice.date}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      ${invoice.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                    </TableCell>
                    <TableCell>
                      <InvoiceStatusBadge status={invoice.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Top Vendors */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top Vendors by Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={vendorConfig} className="h-[280px] w-full">
              <BarChart data={topVendors} margin={{ left: 0, right: 10 }}>
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
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
