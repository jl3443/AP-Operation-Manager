"use client"

import * as React from "react"
import Link from "next/link"
import {
  AlertTriangle,
  Search,
  Filter,
  Clock,
  User,
  CheckCircle2,
  ArrowUpRight,
} from "lucide-react"

import { PageHeader } from "@/components/page-header"
import { ExceptionTypeBadge } from "@/components/exception-type-badge"
import { SeverityIcon } from "@/components/severity-icon"
import { InvoiceStatusBadge } from "@/components/invoice-status-badge"
import { KpiCard } from "@/components/kpi-card"
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
import type { ExceptionType, ExceptionSeverity, ExceptionStatus } from "@/lib/types"

// Mock Data
const mockExceptions: Array<{
  id: string
  invoice_number: string
  invoice_id: string
  vendor: string
  exception_type: ExceptionType
  severity: ExceptionSeverity
  amount: number
  age_days: number
  assigned_to: string
  status: ExceptionStatus
  description: string
}> = [
  { id: "exc-001", invoice_number: "INV-2024-0890", invoice_id: "inv-003", vendor: "Global Supply Co", exception_type: "amount_variance", severity: "high", amount: 45670.00, age_days: 2, assigned_to: "Sarah K.", status: "in_progress", description: "Line 2 unit price $15.00 vs PO $12.50" },
  { id: "exc-002", invoice_number: "INV-2024-0875", invoice_id: "inv-011", vendor: "Metro Electric", exception_type: "missing_po", severity: "medium", amount: 8420.00, age_days: 5, assigned_to: "John D.", status: "assigned", description: "No matching PO found for this invoice" },
  { id: "exc-003", invoice_number: "INV-2024-0868", invoice_id: "inv-012", vendor: "PackRight Inc", exception_type: "duplicate_invoice", severity: "critical", amount: 1560.00, age_days: 1, assigned_to: "Unassigned", status: "open", description: "Possible duplicate of INV-2024-0850" },
  { id: "exc-004", invoice_number: "INV-2024-0862", invoice_id: "inv-013", vendor: "Acme Corp", exception_type: "quantity_variance", severity: "medium", amount: 22340.00, age_days: 3, assigned_to: "Sarah K.", status: "in_progress", description: "Received 45 units vs invoiced 50 units" },
  { id: "exc-005", invoice_number: "INV-2024-0855", invoice_id: "inv-014", vendor: "TechParts Ltd", exception_type: "expired_po", severity: "low", amount: 3280.50, age_days: 7, assigned_to: "Mike R.", status: "assigned", description: "PO-4518 expired, GRN pending" },
  { id: "exc-006", invoice_number: "INV-2024-0848", invoice_id: "inv-015", vendor: "Steel Works Ltd", exception_type: "amount_variance", severity: "high", amount: 67800.00, age_days: 4, assigned_to: "John D.", status: "escalated", description: "Invoice total exceeds PO by 8.2% (tolerance: 5%)" },
  { id: "exc-007", invoice_number: "INV-2024-0841", invoice_id: "inv-016", vendor: "CloudServ Inc", exception_type: "tax_variance", severity: "low", amount: 7500.00, age_days: 6, assigned_to: "Sarah K.", status: "in_progress", description: "Tax rate 10% vs expected 8.5%" },
  { id: "exc-008", invoice_number: "INV-2024-0836", invoice_id: "inv-017", vendor: "FreshFoods Co", exception_type: "vendor_mismatch", severity: "medium", amount: 4230.00, age_days: 2, assigned_to: "Unassigned", status: "open", description: "Invoice vendor name doesn't match PO vendor" },
]

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
  auto_resolved: { label: "Auto-Resolved", className: "bg-purple-50 text-purple-700 border-purple-200" },
}

export default function ExceptionsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Exception Queue"
        description="Review and resolve invoice processing exceptions"
      />

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Open"
          value="12"
          icon={AlertTriangle}
          trend={{ value: -5, label: "vs last week" }}
        />
        <KpiCard
          title="Assigned"
          value="8"
          icon={User}
          trend={{ value: 2, label: "vs last week" }}
        />
        <KpiCard
          title="In Progress"
          value="6"
          icon={Clock}
          trend={{ value: 10, label: "vs last week" }}
        />
        <KpiCard
          title="Resolved (MTD)"
          value="45"
          icon={CheckCircle2}
          trend={{ value: 18, label: "vs last month" }}
        />
      </div>

      {/* Filter Bar */}
      <Card className="py-3">
        <CardContent className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="Search exceptions..." className="pl-9 h-8" />
          </div>
          <Select>
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
            </SelectContent>
          </Select>
          <Select>
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
          <Select>
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
          <Select>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Assigned To" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Users</SelectItem>
              <SelectItem value="sarah">Sarah K.</SelectItem>
              <SelectItem value="john">John D.</SelectItem>
              <SelectItem value="mike">Mike R.</SelectItem>
              <SelectItem value="unassigned">Unassigned</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Exception Table */}
      <Card className="py-0">
        <CardContent className="px-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Invoice #</TableHead>
                <TableHead>Vendor</TableHead>
                <TableHead>Exception Type</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Age</TableHead>
                <TableHead>Assigned To</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>SLA</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockExceptions.map((exc) => (
                <TableRow key={exc.id} className="cursor-pointer">
                  <TableCell>
                    <Link
                      href={`/invoices/${exc.invoice_id}`}
                      className="font-medium text-primary hover:underline flex items-center gap-1"
                    >
                      {exc.invoice_number}
                      <ArrowUpRight className="size-3" />
                    </Link>
                  </TableCell>
                  <TableCell className="font-medium">{exc.vendor}</TableCell>
                  <TableCell>
                    <ExceptionTypeBadge type={exc.exception_type} />
                  </TableCell>
                  <TableCell>
                    <SeverityIcon severity={exc.severity} showLabel />
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    ${exc.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {exc.age_days}d
                  </TableCell>
                  <TableCell>
                    <span className={cn(
                      "text-sm",
                      exc.assigned_to === "Unassigned" && "text-muted-foreground italic"
                    )}>
                      {exc.assigned_to}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={statusLabels[exc.status].className}
                    >
                      {statusLabels[exc.status].label}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <SLAIndicator ageDays={exc.age_days} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
