"use client"

import * as React from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { toast } from "sonner"
import {
  ArrowLeft,
  FileText,
  CheckCircle,
  XCircle,
  MessageSquare,
  Send,
  AlertTriangle,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Play,
  Loader2,
  Sparkles,
  Zap,
} from "lucide-react"

import { useInvoice, useMatchInvoice, useExtractInvoice } from "@/hooks/use-invoices"
import { InvoiceStatusBadge } from "@/components/invoice-status-badge"
import { InvoiceProgressStepper } from "@/components/invoice-progress-stepper"
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
  const router = useRouter()
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

  const subtotal = invoice.line_items.reduce((sum, li) => sum + li.line_total, 0)

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
          {/* Run full agent pipeline (primary action) */}
          <Button
            size="sm"
            variant="outline"
            className="border-primary/40 text-primary hover:bg-primary/10"
            onClick={() => router.push(`/invoices/${invoiceId}/pipeline`)}
          >
            <Zap className="size-4" />
            Run Pipeline
          </Button>
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
                <Sparkles className="size-4" />
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

      {/* Pipeline Progress Stepper */}
      <Card>
        <CardContent className="py-4">
          <InvoiceProgressStepper status={invoice.status} />
        </CardContent>
      </Card>

      {/* Split View */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left Panel - Styled Document Preview */}
        <Card className="lg:sticky lg:top-6 py-0">
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
            <div className="bg-gray-100 dark:bg-gray-900 p-6 min-h-[600px] flex items-start justify-center">
              {/* Styled "paper" invoice */}
              <div className="bg-white dark:bg-gray-950 shadow-lg rounded w-full max-w-[520px] p-8 text-sm relative border">
                {/* AI Extracted badge */}
                {invoice.status !== "draft" && (
                  <div className="absolute top-3 right-3">
                    <Badge className="bg-primary text-primary-foreground text-[10px]">
                      <Sparkles className="size-3 mr-1" />
                      AI Extracted
                      {invoice.ocr_confidence_score != null &&
                        ` · ${(invoice.ocr_confidence_score * 100).toFixed(0)}%`}
                    </Badge>
                  </div>
                )}

                {/* Invoice header */}
                <div className="flex justify-between items-start border-b pb-4 mb-4">
                  <div>
                    <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                      INVOICE
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      #{invoice.invoice_number}
                    </p>
                  </div>
                  <div className="text-right text-xs text-gray-600 dark:text-gray-400 space-y-0.5">
                    <p>Date: {invoice.invoice_date}</p>
                    <p>Due: {invoice.due_date}</p>
                    <p>Currency: {invoice.currency}</p>
                  </div>
                </div>

                {/* Vendor info */}
                <div className="mb-4 text-xs text-gray-600 dark:text-gray-400">
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    Vendor: {invoice.vendor?.name ?? `ID ${invoice.vendor_id.slice(0, 8)}`}
                  </p>
                  {invoice.vendor?.vendor_code && (
                    <p>Code: {invoice.vendor.vendor_code}</p>
                  )}
                </div>

                {/* Line items table */}
                {invoice.line_items.length > 0 ? (
                  <table className="w-full text-xs mb-4">
                    <thead>
                      <tr className="border-b text-gray-500">
                        <th className="text-left py-1.5 font-medium">#</th>
                        <th className="text-left py-1.5 font-medium">Description</th>
                        <th className="text-right py-1.5 font-medium">Qty</th>
                        <th className="text-right py-1.5 font-medium">Price</th>
                        <th className="text-right py-1.5 font-medium">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {invoice.line_items.map((li) => (
                        <tr key={li.id} className="border-b border-gray-100 dark:border-gray-800">
                          <td className="py-1.5 text-gray-400">{li.line_number}</td>
                          <td className="py-1.5 text-gray-900 dark:text-gray-100">
                            {li.description ?? "—"}
                          </td>
                          <td className="py-1.5 text-right font-mono">{li.quantity}</td>
                          <td className="py-1.5 text-right font-mono">
                            ${li.unit_price.toFixed(2)}
                          </td>
                          <td className="py-1.5 text-right font-mono font-medium">
                            ${li.line_total.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="text-center py-8 text-gray-400 text-xs">
                    <FileText className="size-8 mx-auto mb-2 opacity-30" />
                    No line items extracted yet
                  </div>
                )}

                {/* Totals */}
                <div className="border-t pt-3 space-y-1 text-xs">
                  {subtotal > 0 && (
                    <div className="flex justify-between text-gray-600 dark:text-gray-400">
                      <span>Subtotal</span>
                      <span className="font-mono">
                        ${subtotal.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  )}
                  {invoice.tax_amount > 0 && (
                    <div className="flex justify-between text-gray-600 dark:text-gray-400">
                      <span>Tax</span>
                      <span className="font-mono">
                        ${invoice.tax_amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  )}
                  {invoice.freight_amount > 0 && (
                    <div className="flex justify-between text-gray-600 dark:text-gray-400">
                      <span>Freight</span>
                      <span className="font-mono">
                        ${invoice.freight_amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between font-bold text-base pt-2 border-t text-gray-900 dark:text-gray-100">
                    <span>Total</span>
                    <span className="font-mono">
                      ${invoice.total_amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
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
