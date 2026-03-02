"use client"

import * as React from "react"
import {
  Search,
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
import { useAuditLogs } from "@/hooks/use-audit"
import type { AuditLog } from "@/lib/types"

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
  uploaded: { label: "Uploaded", className: "bg-indigo-50 text-indigo-700 border-indigo-200" },
  matched: { label: "Matched", className: "bg-green-50 text-green-700 border-green-200" },
  ocr_extracted: { label: "OCR Extracted", className: "bg-cyan-50 text-cyan-700 border-cyan-200" },
  risk_level_changed: { label: "Risk Changed", className: "bg-orange-50 text-orange-700 border-orange-200" },
  ai_recommendation: { label: "AI Recommendation", className: "bg-violet-50 text-violet-700 border-violet-200" },
}

function formatTimestamp(ts: string): string {
  try {
    const date = new Date(ts)
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    })
  } catch {
    return ts
  }
}

function formatDetails(log: AuditLog): string {
  const parts: string[] = []

  if (log.changes && Object.keys(log.changes).length > 0) {
    for (const [key, value] of Object.entries(log.changes)) {
      if (typeof value === "object" && value !== null && "from" in value && "to" in value) {
        const change = value as { from: unknown; to: unknown }
        parts.push(`${key}: ${String(change.from)} -> ${String(change.to)}`)
      } else {
        parts.push(`${key}: ${String(value)}`)
      }
    }
  }

  if (log.evidence && Object.keys(log.evidence).length > 0) {
    for (const [key, value] of Object.entries(log.evidence)) {
      parts.push(`${key}: ${String(value)}`)
    }
  }

  return parts.join("; ") || "\u2014"
}

export default function AuditPage() {
  const [page, setPage] = React.useState(1)
  const [entityType, setEntityType] = React.useState<string | undefined>(undefined)
  const [actorName, setActorName] = React.useState<string | undefined>(undefined)
  const [dateFrom, setDateFrom] = React.useState<string | undefined>(undefined)
  const [dateTo, setDateTo] = React.useState<string | undefined>(undefined)

  const { data, isLoading, isError } = useAuditLogs({
    page,
    entity_type: entityType,
    actor_name: actorName,
    date_from: dateFrom,
    date_to: dateTo,
  })

  const logs = data?.items ?? []
  const totalPages = data?.total_pages ?? 1

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
            <Input
              placeholder="Search by user / actor name..."
              className="pl-9 h-8"
              value={actorName ?? ""}
              onChange={(e) => {
                setActorName(e.target.value === "" ? undefined : e.target.value)
                setPage(1)
              }}
            />
          </div>
          <Select
            value={entityType ?? "all"}
            onValueChange={(value) => {
              setEntityType(value === "all" ? undefined : value)
              setPage(1)
            }}
          >
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
          <Input
            type="date"
            className="w-[140px] h-9"
            value={dateFrom ?? ""}
            onChange={(e) => {
              setDateFrom(e.target.value === "" ? undefined : e.target.value)
              setPage(1)
            }}
          />
          <Input
            type="date"
            className="w-[140px] h-9"
            value={dateTo ?? ""}
            onChange={(e) => {
              setDateTo(e.target.value === "" ? undefined : e.target.value)
              setPage(1)
            }}
          />
        </CardContent>
      </Card>

      {/* Audit Log Table */}
      <Card className="py-0">
        <CardContent className="px-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              Loading audit logs...
            </div>
          ) : isError ? (
            <div className="flex items-center justify-center py-12 text-destructive">
              Failed to load audit logs. Please try again.
            </div>
          ) : logs.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              No audit logs found.
            </div>
          ) : (
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
                {logs.map((log) => {
                  const actionBadge = actionBadgeConfig[log.action] || {
                    label: log.action,
                    className: "bg-slate-100 text-slate-700 border-slate-200",
                  }
                  return (
                    <TableRow key={log.id}>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {formatTimestamp(log.timestamp)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="text-xs capitalize">
                          {log.entity_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-primary">
                        {log.entity_id.substring(0, 8)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={actionBadge.className}>
                          {actionBadge.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span
                          className={
                            log.actor_type === "ai_agent" || log.actor_type === "system"
                              ? "text-primary font-medium"
                              : ""
                          }
                        >
                          {log.actor_name ?? log.actor_type}
                        </span>
                      </TableCell>
                      <TableCell className="max-w-[300px] truncate text-muted-foreground text-sm">
                        {formatDetails(log)}
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {data && data.total > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Page <span className="font-medium">{page}</span> of{" "}
            <span className="font-medium">{totalPages}</span>
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
