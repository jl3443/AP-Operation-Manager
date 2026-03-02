"use client"

import * as React from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { toast } from "sonner"
import {
  ArrowLeft,
  FileText,
  CheckCircle,
  XCircle,
  MessageSquare,
  Send,
  Clock,
  AlertTriangle,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Play,
  Loader2,
} from "lucide-react"

import { useInvoice, useMatchInvoice, useExtractInvoice } from "@/hooks/use-invoices"
import { InvoiceStatusBadge } from "@/components/invoice-status-badge"
import { ConfidenceIndicator } from "@/components/confidence-indicator"
import { KpiCardSkeleton } from "@/components/loading-skeleton"
import { QueryError } from "@/components/query-error"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export default function InvoiceDetailPage() {
  const params = useParams()
  const invoiceId = params.id as string
  const [comment, setComment] = React.useState("")

  const { data: invoice, isLoading, error, refetch } = useInvoice(invoiceId)
  const matchMutation = useMatchInvoice()
  const extractMutation = useExtractInvoice()

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="size-8" />
          <div>
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-32 mt-1" />
          </div>
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-[600px]" />
          <div className="space-y-4">
            <KpiCardSkeleton />
            <KpiCardSkeleton />
            <KpiCardSkeleton />
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return <QueryError error={error} retry={() => refetch()} />
  }

  if (!invoice) {
    return (
      <div className="text-center py-12 text-muted-foreground">Invoice not found</div>
    )
  }

  function handleMatch() {
    matchMutation.mutate(invoiceId, {
      onSuccess: (data) => {
        toast.success(`Match complete: ${data.match_status} (score: ${data.overall_score})`)
      },
      onError: (err) => {
        toast.error(`Match failed: ${err.message}`)
      },
    })
  }

  function handleExtract() {
    extractMutation.mutate(invoiceId, {
      onSuccess: () => {
        toast.success("OCR extraction complete")
      },
      onError: (err) => {
        toast.error(`Extraction failed: ${err.message}`)
      },
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon-sm" asChild>
            <Link href="/invoices">
              <ArrowLeft className="size-4" />
            </Link>
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{invoice.invoice_number}</h1>
              <InvoiceStatusBadge status={invoice.status} />
            </div>
            <p className="text-sm text-muted-foreground mt-0.5">
              Vendor ID: {invoice.vendor_id.slice(0, 8)}...
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {invoice.status === "draft" && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleExtract}
              disabled={extractMutation.isPending}
            >
              {extractMutation.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Play className="size-4" />
              )}
              Extract
            </Button>
          )}
          {(invoice.status === "extracted" || invoice.status === "draft") && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleMatch}
              disabled={matchMutation.isPending}
            >
              {matchMutation.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Play className="size-4" />
              )}
              Run Match
            </Button>
          )}
          <Button variant="outline" size="sm" className="text-destructive hover:text-destructive">
            <XCircle className="size-4" />
            Reject
          </Button>
          <Button size="sm">
            <CheckCircle className="size-4" />
            Approve
          </Button>
        </div>
      </div>

      {/* Split View */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left Panel - Document Viewer */}
        <Card className="lg:sticky lg:top-6 py-0 overflow-hidden">
          <CardHeader className="bg-muted/50 py-3 border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <FileText className="size-4" />
                Document Preview
              </CardTitle>
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="icon-sm"><ZoomOut className="size-3.5" /></Button>
                <Button variant="ghost" size="icon-sm"><ZoomIn className="size-3.5" /></Button>
                <Button variant="ghost" size="icon-sm"><RotateCw className="size-3.5" /></Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="flex items-center justify-center bg-muted/30 h-[600px]">
              <div className="text-center space-y-3">
                <div className="mx-auto rounded-2xl bg-muted p-6">
                  <FileText className="size-12 text-muted-foreground mx-auto" />
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Invoice Document
                  </p>
                  <p className="text-xs text-muted-foreground/70">
                    {invoice.invoice_number}.pdf
                  </p>
                </div>
                <Button variant="outline" size="sm">
                  Open Full Document
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Right Panel - Invoice Details */}
        <div className="space-y-4">
          {/* Invoice Header Info */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Invoice Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="space-y-1">
                  <p className="text-muted-foreground">Invoice Number</p>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{invoice.invoice_number}</p>
                    {invoice.ocr_confidence_score != null && (
                      <ConfidenceIndicator confidence={invoice.ocr_confidence_score * 100} showLabel />
                    )}
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Currency</p>
                  <p className="font-medium">{invoice.currency}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Invoice Date</p>
                  <p className="font-medium">{invoice.invoice_date}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Due Date</p>
                  <p className="font-medium">{invoice.due_date}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Document Type</p>
                  <p className="font-medium capitalize">{invoice.document_type.replaceAll("_", " ")}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Source</p>
                  <Badge variant="secondary" className="text-xs capitalize">
                    {invoice.source_channel}
                  </Badge>
                </div>
                <Separator className="col-span-2 my-1" />
                <div className="space-y-1">
                  <p className="text-muted-foreground">Tax Amount</p>
                  <p className="font-medium font-mono">
                    ${invoice.tax_amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Freight</p>
                  <p className="font-medium font-mono">
                    ${invoice.freight_amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                  </p>
                </div>
                <div className="col-span-2 bg-primary/5 -mx-6 px-6 py-3 border-t">
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-muted-foreground font-medium">Total Amount</p>
                    <p className="text-xl font-bold font-mono">
                      ${invoice.total_amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Line Items */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">
                Line Items ({invoice.line_items.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="px-0">
              {invoice.line_items.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-6">
                  No line items. Run extraction to populate.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-10">#</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Qty</TableHead>
                      <TableHead className="text-right">Unit Price</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                      <TableHead className="w-10"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoice.line_items.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell className="text-muted-foreground">
                          {item.line_number}
                        </TableCell>
                        <TableCell className="font-medium">
                          {item.description ?? "—"}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {item.quantity}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          ${item.unit_price.toFixed(2)}
                        </TableCell>
                        <TableCell className="text-right font-mono font-medium">
                          ${item.line_total.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </TableCell>
                        <TableCell>
                          {item.ai_confidence != null && (
                            <ConfidenceIndicator confidence={item.ai_confidence * 100} />
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {/* Match Results - shows after match is run */}
          {matchMutation.data && (
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">Match Results</CardTitle>
                  <Badge
                    variant="outline"
                    className={
                      matchMutation.data.match_status === "matched"
                        ? "bg-green-50 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300"
                        : "bg-amber-50 text-amber-700 border-amber-200"
                    }
                  >
                    {matchMutation.data.match_status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="space-y-1">
                    <p className="text-muted-foreground">Match Score</p>
                    <p className="text-xl font-bold text-green-600">
                      {matchMutation.data.overall_score}%
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-muted-foreground">Status</p>
                    <p className="font-medium capitalize">
                      {matchMutation.data.match_status.replaceAll("_", " ")}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Status Info */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-3 rounded-lg bg-muted/50 border p-3">
                <Clock className="size-5 text-muted-foreground shrink-0" />
                <div>
                  <p className="text-sm font-medium capitalize">
                    {invoice.status.replaceAll("_", " ")}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Last updated: {new Date(invoice.updated_at).toLocaleString()}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Comments / Collaboration Area */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <MessageSquare className="size-4" />
            Activity & Comments
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground text-center py-4">
            No comments yet. Comments will appear here when exceptions are created for this invoice.
          </p>

          <Separator />

          {/* New Comment (placeholder - wired when exceptions exist) */}
          <div className="flex gap-3">
            <Avatar className="size-8 shrink-0">
              <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                ??
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 space-y-2">
              <Textarea
                placeholder="Add a comment... (available when exceptions exist)"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                className="min-h-[60px]"
              />
              <div className="flex justify-end">
                <Button size="sm" disabled={!comment.trim()}>
                  <Send className="size-3.5" />
                  Comment
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
