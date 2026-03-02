"use client"

import * as React from "react"
import {
  History,
  Search,
  FileText,
  User,
  CheckCircle,
  AlertTriangle,
  Upload,
  Settings,
  Filter,
} from "lucide-react"

import { PageHeader } from "@/components/page-header"
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

// TODO: Replace with real API when global audit trail endpoint is available.
// Currently only per-invoice audit trail exists at GET /invoices/{id}/audit-trail.
const mockAuditLogs = [
  { id: "log-001", timestamp: "2024-02-28 15:15:32", entity: "Invoice", entity_id: "INV-2024-0892", action: "status_changed", user: "AI System", details: "Status changed from matching to pending_approval", icon: CheckCircle },
  { id: "log-002", timestamp: "2024-02-28 15:15:30", entity: "Match", entity_id: "INV-2024-0892", action: "match_completed", user: "AI System", details: "Three-way match completed with score 98.5%", icon: CheckCircle },
  { id: "log-003", timestamp: "2024-02-28 14:30:00", entity: "Invoice", entity_id: "INV-2024-0892", action: "created", user: "Email Intake", details: "Invoice received via email from acme@corp.com", icon: FileText },
  { id: "log-004", timestamp: "2024-02-28 14:28:15", entity: "Exception", entity_id: "EXC-2024-0156", action: "auto_resolved", user: "AI System", details: "Price variance within tolerance, auto-resolved", icon: AlertTriangle },
  { id: "log-005", timestamp: "2024-02-28 10:15:00", entity: "Import", entity_id: "IMP-002", action: "completed", user: "Kyle S.", details: "Goods receipts import: 189 records imported", icon: Upload },
  { id: "log-006", timestamp: "2024-02-28 09:45:22", entity: "Invoice", entity_id: "INV-2024-0891", action: "extraction_completed", user: "AI System", details: "OCR extraction completed with 92% confidence", icon: FileText },
  { id: "log-007", timestamp: "2024-02-27 16:45:00", entity: "Vendor", entity_id: "V-1004", action: "status_changed", user: "Sarah K.", details: "Vendor status changed from active to on_hold", icon: Settings },
  { id: "log-008", timestamp: "2024-02-27 15:30:00", entity: "Approval", entity_id: "INV-2024-0860", action: "approved", user: "Kyle S.", details: "Invoice approved. Amount: $7,500.00", icon: CheckCircle },
  { id: "log-009", timestamp: "2024-02-27 14:20:00", entity: "Exception", entity_id: "EXC-2024-0155", action: "assigned", user: "System", details: "Exception assigned to John D. based on workload rules", icon: User },
  { id: "log-010", timestamp: "2024-02-27 11:00:00", entity: "Invoice", entity_id: "INV-2024-0890", action: "exception_created", user: "AI System", details: "Price mismatch detected on line 2", icon: AlertTriangle },
]

const actionBadgeConfig: Record<string, { label: string; className: string }> = {
  created: { label: "Created", className: "bg-blue-50 text-blue-700 border-blue-200" },
  status_changed: { label: "Updated", className: "bg-amber-50 text-amber-700 border-amber-200" },
  match_completed: { label: "Matched", className: "bg-green-50 text-green-700 border-green-200" },
  auto_resolved: { label: "Resolved", className: "bg-purple-50 text-purple-700 border-purple-200" },
  completed: { label: "Completed", className: "bg-green-50 text-green-700 border-green-200" },
  extraction_completed: { label: "Extracted", className: "bg-blue-50 text-blue-700 border-blue-200" },
  approved: { label: "Approved", className: "bg-green-50 text-green-700 border-green-200" },
  assigned: { label: "Assigned", className: "bg-slate-100 text-slate-700 border-slate-200" },
  exception_created: { label: "Exception", className: "bg-red-50 text-red-700 border-red-200" },
}

export default function AuditPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit Trail"
        description="Complete log of all system activities and changes"
      >
        <Button variant="outline" size="sm">
          <Filter className="size-4" />
          Export Log
        </Button>
      </PageHeader>

      {/* Filter Bar */}
      <Card className="py-3">
        <CardContent className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="Search by entity, user, action..." className="pl-9 h-8" />
          </div>
          <Select>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Entity Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Entities</SelectItem>
              <SelectItem value="invoice">Invoice</SelectItem>
              <SelectItem value="vendor">Vendor</SelectItem>
              <SelectItem value="exception">Exception</SelectItem>
              <SelectItem value="approval">Approval</SelectItem>
              <SelectItem value="import">Import</SelectItem>
            </SelectContent>
          </Select>
          <Select>
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="User" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Users</SelectItem>
              <SelectItem value="ai">AI System</SelectItem>
              <SelectItem value="kyle">Kyle S.</SelectItem>
              <SelectItem value="sarah">Sarah K.</SelectItem>
              <SelectItem value="john">John D.</SelectItem>
            </SelectContent>
          </Select>
          <Input type="date" className="w-[140px] h-9" />
          <Input type="date" className="w-[140px] h-9" />
        </CardContent>
      </Card>

      {/* Audit Log Table */}
      <Card className="py-0">
        <CardContent className="px-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[180px]">Timestamp</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Entity ID</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockAuditLogs.map((log) => {
                const Icon = log.icon
                const actionBadge = actionBadgeConfig[log.action] || { label: log.action, className: "bg-slate-100 text-slate-700 border-slate-200" }
                return (
                  <TableRow key={log.id}>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {log.timestamp}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="text-xs">
                        {log.entity}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs text-primary">
                      {log.entity_id}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={actionBadge.className}>
                        {actionBadge.label}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className={log.user === "AI System" ? "text-primary font-medium" : ""}>
                        {log.user}
                      </span>
                    </TableCell>
                    <TableCell className="max-w-[300px] truncate text-muted-foreground text-sm">
                      {log.details}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
