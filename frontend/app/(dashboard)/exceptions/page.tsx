"use client"

import * as React from "react"
import Link from "next/link"
import {
  AlertTriangle,
  Search,
  Clock,
  User,
  CheckCircle2,
  ArrowUpRight,
} from "lucide-react"

import { useExceptions } from "@/hooks/use-exceptions"
import { PageHeader } from "@/components/page-header"
import { ExceptionTypeBadge } from "@/components/exception-type-badge"
import { SeverityIcon } from "@/components/severity-icon"
import { KpiCard } from "@/components/kpi-card"
import { KpiCardSkeleton, TableSkeleton } from "@/components/loading-skeleton"
import { QueryError } from "@/components/query-error"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import type { ExceptionStatus } from "@/lib/types"

function SLAIndicator({ ageDays }: { ageDays: number }) {
  if (ageDays < 1) {
    return (
      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 text-[10px]">
        &lt;24h
      </Badge>
    )
  }
  if (ageDays <= 2) {
    return (
      <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200 text-[10px]">
        {ageDays}d
      </Badge>
    )
  }
  return (
    <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200 text-[10px]">
      {ageDays}d
    </Badge>
  )
}

const statusLabels: Record<ExceptionStatus, { label: string; className: string }> = {
  open: { label: "Open", className: "bg-slate-100 text-slate-700 border-slate-200" },
  assigned: { label: "Assigned", className: "bg-blue-50 text-blue-700 border-blue-200" },
  in_progress: { label: "In Progress", className: "bg-amber-50 text-amber-700 border-amber-200" },
  resolved: { label: "Resolved", className: "bg-green-50 text-green-700 border-green-200" },
  escalated: { label: "Escalated", className: "bg-red-50 text-red-700 border-red-200" },
}

export default function ExceptionsPage() {
  const [page, setPage] = React.useState(1)
  const [statusFilter, setStatusFilter] = React.useState<string | undefined>()
  const [severityFilter, setSeverityFilter] = React.useState<string | undefined>()
  const [typeFilter, setTypeFilter] = React.useState<string | undefined>()

  const { data, isLoading, error, refetch } = useExceptions({
    page,
    page_size: 20,
    status: statusFilter,
    severity: severityFilter,
    exception_type: typeFilter,
  })

  const items = data?.items ?? []
  const openCount = items.filter((e) => e.status === "open").length
  const assignedCount = items.filter((e) => e.status === "assigned").length
  const inProgressCount = items.filter((e) => e.status === "in_progress").length
  const resolvedCount = items.filter((e) => e.status === "resolved").length

  function getAgeDays(createdAt: string): number {
    const created = new Date(createdAt)
    const now = new Date()
    return Math.floor((now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24))
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Exception Queue"
        description="Review and resolve invoice processing exceptions"
      />

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {isLoading ? (
          <>
            <KpiCardSkeleton />
            <KpiCardSkeleton />
            <KpiCardSkeleton />
            <KpiCardSkeleton />
          </>
        ) : (
          <>
            <KpiCard title="Open" value={openCount.toString()} icon={AlertTriangle} />
            <KpiCard title="Assigned" value={assignedCount.toString()} icon={User} />
            <KpiCard title="In Progress" value={inProgressCount.toString()} icon={Clock} />
            <KpiCard title="Resolved" value={resolvedCount.toString()} icon={CheckCircle2} />
          </>
        )}
      </div>

      {/* Filter Bar */}
      <Card className="py-3">
        <CardContent className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
{/* TODO: Wire when backend adds search param to GET /exceptions */}
            <Input placeholder="Search exceptions..." className="pl-9 h-8" disabled />
          </div>
          <Select
            value={typeFilter ?? "all"}
            onValueChange={(v) => { setTypeFilter(v === "all" ? undefined : v); setPage(1) }}
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Exception Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="amount_variance">Amount Variance</SelectItem>
              <SelectItem value="quantity_variance">Qty Variance</SelectItem>
              <SelectItem value="missing_po">Missing PO</SelectItem>
              <SelectItem value="duplicate_invoice">Duplicate</SelectItem>
              <SelectItem value="vendor_mismatch">Vendor Mismatch</SelectItem>
              <SelectItem value="tax_variance">Tax Variance</SelectItem>
              <SelectItem value="expired_po">Expired PO</SelectItem>
            </SelectContent>
          </Select>
          <Select
            value={severityFilter ?? "all"}
            onValueChange={(v) => { setSeverityFilter(v === "all" ? undefined : v); setPage(1) }}
          >
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="Severity" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Severity</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
          <Select
            value={statusFilter ?? "all"}
            onValueChange={(v) => { setStatusFilter(v === "all" ? undefined : v); setPage(1) }}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="open">Open</SelectItem>
              <SelectItem value="assigned">Assigned</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="escalated">Escalated</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Exception Table */}
      <Card className="py-0">
        <CardContent className="px-0">
          {error ? (
            <div className="p-6">
              <QueryError error={error} retry={() => refetch()} />
            </div>
          ) : isLoading ? (
            <div className="p-6">
              <TableSkeleton rows={8} cols={7} />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Invoice</TableHead>
                  <TableHead>Exception Type</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Age</TableHead>
                  <TableHead>Assigned To</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>SLA</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground py-12">
                      No exceptions found. Exceptions will appear here when invoice matches detect issues.
                    </TableCell>
                  </TableRow>
                )}
                {items.map((exc) => {
                  const ageDays = getAgeDays(exc.created_at)
                  return (
                    <TableRow key={exc.id} className="cursor-pointer group">
                      <TableCell>
                        <Link
                          href={`/exceptions/${exc.id}`}
                          className="font-medium text-primary hover:underline flex items-center gap-1"
                        >
                          {exc.invoice_id.slice(0, 8)}...
                          <ArrowUpRight className="size-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </Link>
                      </TableCell>
                      <TableCell>
                        <ExceptionTypeBadge type={exc.exception_type} />
                      </TableCell>
                      <TableCell>
                        <SeverityIcon severity={exc.severity} showLabel />
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {ageDays}d
                      </TableCell>
                      <TableCell>
                        <span className={cn(
                          "text-sm",
                          !exc.assigned_to && "text-muted-foreground italic"
                        )}>
                          {exc.assigned_to ? exc.assigned_to.slice(0, 8) + "..." : "Unassigned"}
                        </span>
                      </TableCell>
                      <TableCell>
                        {statusLabels[exc.status] && (
                          <Badge
                            variant="outline"
                            className={statusLabels[exc.status].className}
                          >
                            {statusLabels[exc.status].label}
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <SLAIndicator ageDays={ageDays} />
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
