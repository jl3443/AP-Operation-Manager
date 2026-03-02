"use client"

import * as React from "react"
import Link from "next/link"
import {
  CheckCircle,
  XCircle,
  MoreHorizontal,
  Brain,
  ArrowUpRight,
  Eye,
} from "lucide-react"
import { toast } from "sonner"

import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"

// Mock Data
interface PendingApproval {
  id: string
  invoice_number: string
  invoice_id: string
  vendor: string
  amount: number
  submitted_date: string
  ai_recommendation: "approve" | "review" | "reject"
  ai_confidence: number
  approval_level: number
}

const pendingApprovals: PendingApproval[] = [
  { id: "apr-001", invoice_number: "INV-2024-0892", invoice_id: "inv-001", vendor: "Acme Corp", amount: 12450.00, submitted_date: "2024-02-28", ai_recommendation: "approve", ai_confidence: 95, approval_level: 1 },
  { id: "apr-002", invoice_number: "INV-2024-0883", invoice_id: "inv-010", vendor: "FreshFoods Co", amount: 2340.80, submitted_date: "2024-02-28", ai_recommendation: "approve", ai_confidence: 92, approval_level: 1 },
  { id: "apr-003", invoice_number: "INV-2024-0878", invoice_id: "inv-018", vendor: "Steel Works Ltd", amount: 67800.00, submitted_date: "2024-02-27", ai_recommendation: "review", ai_confidence: 68, approval_level: 2 },
  { id: "apr-004", invoice_number: "INV-2024-0870", invoice_id: "inv-019", vendor: "TechParts Ltd", amount: 15420.00, submitted_date: "2024-02-27", ai_recommendation: "approve", ai_confidence: 97, approval_level: 1 },
  { id: "apr-005", invoice_number: "INV-2024-0865", invoice_id: "inv-020", vendor: "Metro Electric", amount: 3890.00, submitted_date: "2024-02-26", ai_recommendation: "reject", ai_confidence: 82, approval_level: 1 },
]

const approvalHistory = [
  { id: "h-001", invoice_number: "INV-2024-0860", vendor: "CloudServ Inc", amount: 7500.00, decision: "approved", decided_by: "Kyle S.", decided_date: "2024-02-26" },
  { id: "h-002", invoice_number: "INV-2024-0858", vendor: "Office Depot", amount: 892.15, decision: "approved", decided_by: "Auto-Approved", decided_date: "2024-02-25" },
  { id: "h-003", invoice_number: "INV-2024-0852", vendor: "PackRight Inc", amount: 4560.00, decision: "rejected", decided_by: "Kyle S.", decided_date: "2024-02-25" },
  { id: "h-004", invoice_number: "INV-2024-0845", vendor: "Acme Corp", amount: 23400.00, decision: "approved", decided_by: "Kyle S.", decided_date: "2024-02-24" },
  { id: "h-005", invoice_number: "INV-2024-0840", vendor: "Global Supply Co", amount: 8920.00, decision: "approved", decided_by: "Auto-Approved", decided_date: "2024-02-24" },
]

const recommendationConfig: Record<string, { label: string; className: string }> = {
  approve: {
    label: "Approve",
    className: "bg-green-50 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300",
  },
  review: {
    label: "Review",
    className: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300",
  },
  reject: {
    label: "Reject",
    className: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300",
  },
}

export default function ApprovalsPage() {
  const [selectedIds, setSelectedIds] = React.useState<Set<string>>(new Set())

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleSelectAll() {
    if (selectedIds.size === pendingApprovals.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(pendingApprovals.map((a) => a.id)))
    }
  }

  function handleBulkApprove() {
    toast.success(`${selectedIds.size} invoices approved`)
    setSelectedIds(new Set())
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Approval Center"
        description="Review and approve invoices"
      />

      <Tabs defaultValue="pending">
        <TabsList>
          <TabsTrigger value="pending">
            Pending ({pendingApprovals.length})
          </TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        {/* Pending Approvals Tab */}
        <TabsContent value="pending" className="space-y-4">
          {/* Bulk Actions */}
          {selectedIds.size > 0 && (
            <Card className="py-3">
              <CardContent className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">{selectedIds.size}</span> invoice(s) selected
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedIds(new Set())}
                  >
                    Clear Selection
                  </Button>
                  <Button size="sm" onClick={handleBulkApprove}>
                    <CheckCircle className="size-4" />
                    Bulk Approve
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          <Card className="py-0">
            <CardContent className="px-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-10">
                      <Checkbox
                        checked={selectedIds.size === pendingApprovals.length && pendingApprovals.length > 0}
                        onCheckedChange={toggleSelectAll}
                      />
                    </TableHead>
                    <TableHead>Invoice #</TableHead>
                    <TableHead>Vendor</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>AI Recommendation</TableHead>
                    <TableHead>Submitted</TableHead>
                    <TableHead>Level</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pendingApprovals.map((approval) => {
                    const rec = recommendationConfig[approval.ai_recommendation]
                    return (
                      <TableRow key={approval.id}>
                        <TableCell>
                          <Checkbox
                            checked={selectedIds.has(approval.id)}
                            onCheckedChange={() => toggleSelect(approval.id)}
                          />
                        </TableCell>
                        <TableCell>
                          <Link
                            href={`/invoices/${approval.invoice_id}`}
                            className="font-medium text-primary hover:underline flex items-center gap-1"
                          >
                            {approval.invoice_number}
                            <ArrowUpRight className="size-3" />
                          </Link>
                        </TableCell>
                        <TableCell className="font-medium">{approval.vendor}</TableCell>
                        <TableCell className="text-right font-mono">
                          ${approval.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Brain className="size-3.5 text-primary" />
                            <Badge variant="outline" className={rec.className}>
                              {rec.label}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              {approval.ai_confidence}%
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {approval.submitted_date}
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className="text-xs">
                            L{approval.approval_level}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              className="text-green-600 hover:text-green-700 hover:bg-green-50"
                              onClick={() => toast.success(`${approval.invoice_number} approved`)}
                            >
                              <CheckCircle className="size-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              onClick={() => toast.error(`${approval.invoice_number} rejected`)}
                            >
                              <XCircle className="size-4" />
                            </Button>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon-sm">
                                  <MoreHorizontal className="size-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem asChild>
                                  <Link href={`/invoices/${approval.invoice_id}`}>
                                    <Eye className="size-4" />
                                    View Details
                                  </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem>Reassign</DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem>Request Info</DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history">
          <Card className="py-0">
            <CardContent className="px-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Invoice #</TableHead>
                    <TableHead>Vendor</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Decision</TableHead>
                    <TableHead>Decided By</TableHead>
                    <TableHead>Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {approvalHistory.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium text-primary">
                        {item.invoice_number}
                      </TableCell>
                      <TableCell className="font-medium">{item.vendor}</TableCell>
                      <TableCell className="text-right font-mono">
                        ${item.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell>
                        {item.decision === "approved" ? (
                          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                            Approved
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                            Rejected
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className={item.decided_by === "Auto-Approved" ? "text-primary italic" : ""}>
                          {item.decided_by}
                        </span>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {item.decided_date}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
