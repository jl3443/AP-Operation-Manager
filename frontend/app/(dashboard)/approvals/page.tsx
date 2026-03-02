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
  Loader2,
} from "lucide-react"
import { toast } from "sonner"

import {
  usePendingApprovals,
  useApprovalHistory,
  useApproveTask,
  useRejectTask,
  useBatchApprove,
} from "@/hooks/use-approvals"
import { PageHeader } from "@/components/page-header"
import { TableSkeleton } from "@/components/loading-skeleton"
import { QueryError } from "@/components/query-error"
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

  const { data: pending, isLoading: pendingLoading, error: pendingError, refetch: refetchPending } = usePendingApprovals()
  const { data: history, isLoading: historyLoading, error: historyError, refetch: refetchHistory } = useApprovalHistory()
  const approveMutation = useApproveTask()
  const rejectMutation = useRejectTask()
  const batchApproveMutation = useBatchApprove()

  const pendingList = pending ?? []

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleSelectAll() {
    if (selectedIds.size === pendingList.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(pendingList.map((a) => a.id)))
    }
  }

  function handleApprove(taskId: string) {
    approveMutation.mutate(
      { taskId },
      {
        onSuccess: () => toast.success("Invoice approved"),
        onError: (err) => toast.error(`Approval failed: ${err.message}`),
      }
    )
  }

  function handleReject(taskId: string) {
    rejectMutation.mutate(
      { taskId },
      {
        onSuccess: () => toast.info("Invoice rejected"),
        onError: (err) => toast.error(`Rejection failed: ${err.message}`),
      }
    )
  }

  function handleBulkApprove() {
    batchApproveMutation.mutate(
      { task_ids: Array.from(selectedIds) },
      {
        onSuccess: (data) => {
          toast.success(`${data.approved} invoice(s) approved`)
          setSelectedIds(new Set())
        },
        onError: (err) => toast.error(`Bulk approve failed: ${err.message}`),
      }
    )
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
            Pending ({pendingList.length})
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
                  <Button
                    size="sm"
                    onClick={handleBulkApprove}
                    disabled={batchApproveMutation.isPending}
                  >
                    {batchApproveMutation.isPending ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <CheckCircle className="size-4" />
                    )}
                    Bulk Approve
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          <Card className="py-0">
            <CardContent className="px-0">
              {pendingError ? (
                <div className="p-6">
                  <QueryError error={pendingError} retry={() => refetchPending()} />
                </div>
              ) : pendingLoading ? (
                <div className="p-6">
                  <TableSkeleton rows={5} cols={7} />
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-10">
                        <Checkbox
                          checked={selectedIds.size === pendingList.length && pendingList.length > 0}
                          onCheckedChange={toggleSelectAll}
                        />
                      </TableHead>
                      <TableHead>Invoice</TableHead>
                      <TableHead>AI Recommendation</TableHead>
                      <TableHead>Submitted</TableHead>
                      <TableHead>Level</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingList.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-muted-foreground py-12">
                          No pending approvals. All caught up!
                        </TableCell>
                      </TableRow>
                    )}
                    {pendingList.map((approval) => {
                      const rec = approval.ai_recommendation
                        ? recommendationConfig[approval.ai_recommendation]
                        : null
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
                              {approval.invoice_id.slice(0, 8)}...
                              <ArrowUpRight className="size-3" />
                            </Link>
                          </TableCell>
                          <TableCell>
                            {rec ? (
                              <div className="flex items-center gap-2">
                                <Brain className="size-3.5 text-primary" />
                                <Badge variant="outline" className={rec.className}>
                                  {rec.label}
                                </Badge>
                                {approval.ai_recommendation_reason && (
                                  <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                                    {approval.ai_recommendation_reason}
                                  </span>
                                )}
                              </div>
                            ) : (
                              <span className="text-muted-foreground text-sm">—</span>
                            )}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {new Date(approval.created_at).toLocaleDateString()}
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
                                onClick={() => handleApprove(approval.id)}
                                disabled={approveMutation.isPending}
                              >
                                <CheckCircle className="size-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                onClick={() => handleReject(approval.id)}
                                disabled={rejectMutation.isPending}
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
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history">
          <Card className="py-0">
            <CardContent className="px-0">
              {historyError ? (
                <div className="p-6">
                  <QueryError error={historyError} retry={() => refetchHistory()} />
                </div>
              ) : historyLoading ? (
                <div className="p-6">
                  <TableSkeleton rows={5} cols={5} />
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Invoice</TableHead>
                      <TableHead>Decision</TableHead>
                      <TableHead>Level</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Comments</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(history ?? []).length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-muted-foreground py-12">
                          No approval history yet.
                        </TableCell>
                      </TableRow>
                    )}
                    {(history ?? []).map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>
                          <Link
                            href={`/invoices/${item.invoice_id}`}
                            className="font-medium text-primary hover:underline"
                          >
                            {item.invoice_id.slice(0, 8)}...
                          </Link>
                        </TableCell>
                        <TableCell>
                          {item.status === "approved" ? (
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
                          <Badge variant="secondary" className="text-xs">
                            L{item.approval_level}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {item.decision_at
                            ? new Date(item.decision_at).toLocaleDateString()
                            : "—"}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm truncate max-w-[200px]">
                          {item.comments ?? "—"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
