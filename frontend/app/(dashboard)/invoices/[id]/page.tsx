"use client"

import * as React from "react"
import Link from "next/link"
import {
  ArrowLeft,
  FileText,
  CheckCircle,
  XCircle,
  MessageSquare,
  Send,
  Clock,
  Link2,
  AlertTriangle,
  ZoomIn,
  ZoomOut,
  RotateCw,
} from "lucide-react"

import { PageHeader } from "@/components/page-header"
import { InvoiceStatusBadge } from "@/components/invoice-status-badge"
import { ConfidenceIndicator } from "@/components/confidence-indicator"
import { ExceptionTypeBadge } from "@/components/exception-type-badge"
import { SeverityIcon } from "@/components/severity-icon"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

// Mock invoice data
const invoice = {
  id: "inv-001",
  number: "INV-2024-0892",
  vendor: "Acme Corp",
  vendor_code: "V-1001",
  invoice_date: "2024-02-28",
  due_date: "2024-03-28",
  received_date: "2024-02-28",
  total_amount: 12450.0,
  subtotal: 11318.18,
  tax_amount: 1131.82,
  currency: "USD",
  status: "pending_approval" as const,
  source: "email",
  po_number: "PO-2024-4521",
  ocr_confidence: 96,
  payment_terms: "Net 30",
}

const lineItems = [
  { line: 1, description: "Industrial Widget A-100", qty: 50, unitPrice: 45.00, total: 2250.00, poLine: 1, confidence: 98 },
  { line: 2, description: "Connector Cable Type-C", qty: 200, unitPrice: 12.50, total: 2500.00, poLine: 2, confidence: 95 },
  { line: 3, description: "Mounting Bracket XL", qty: 100, unitPrice: 28.68, total: 2868.18, poLine: 3, confidence: 92 },
  { line: 4, description: "Precision Sensor Unit", qty: 25, unitPrice: 148.00, total: 3700.00, poLine: 4, confidence: 97 },
]

const matchResult = {
  match_type: "three_way" as const,
  match_status: "matched" as const,
  overall_score: 98.5,
  po_number: "PO-2024-4521",
  grn_number: "GRN-2024-0890",
  price_variance: 0.2,
  quantity_variance: 0.0,
}

const exceptions = [
  {
    id: "exc-001",
    type: "amount_variance" as const,
    severity: "low" as const,
    description: "Line 3 unit price differs by $0.18 from PO (within tolerance)",
    status: "auto_resolved" as const,
  },
]

const comments = [
  {
    id: "c1",
    user: "Sarah K.",
    initials: "SK",
    content: "Invoice matches PO-4521. All line items verified. Recommending approval.",
    timestamp: "2024-02-28 14:30",
    isAI: true,
  },
  {
    id: "c2",
    user: "John D.",
    initials: "JD",
    content: "Confirmed receipt of goods. GRN-0890 matches quantities.",
    timestamp: "2024-02-28 15:12",
    isAI: false,
  },
  {
    id: "c3",
    user: "AI Assistant",
    initials: "AI",
    content: "Three-way match completed. Score: 98.5%. Minor price variance on line 3 auto-resolved (within 1% tolerance). Ready for approval.",
    timestamp: "2024-02-28 15:15",
    isAI: true,
  },
]

export default function InvoiceDetailPage() {
  const [comment, setComment] = React.useState("")

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
              <h1 className="text-2xl font-bold">{invoice.number}</h1>
              <InvoiceStatusBadge status={invoice.status} />
            </div>
            <p className="text-sm text-muted-foreground mt-0.5">
              {invoice.vendor} &middot; {invoice.vendor_code}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <MessageSquare className="size-4" />
            Request Info
          </Button>
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
                    {invoice.number}.pdf
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
                    <p className="font-medium">{invoice.number}</p>
                    <ConfidenceIndicator confidence={invoice.ocr_confidence} showLabel />
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Vendor</p>
                  <p className="font-medium">{invoice.vendor}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Invoice Date</p>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{invoice.invoice_date}</p>
                    <ConfidenceIndicator confidence={98} />
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Due Date</p>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{invoice.due_date}</p>
                    <ConfidenceIndicator confidence={97} />
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">PO Number</p>
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-primary">{invoice.po_number}</p>
                    <Link2 className="size-3.5 text-primary" />
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Payment Terms</p>
                  <p className="font-medium">{invoice.payment_terms}</p>
                </div>
                <Separator className="col-span-2 my-1" />
                <div className="space-y-1">
                  <p className="text-muted-foreground">Subtotal</p>
                  <p className="font-medium font-mono">
                    ${invoice.subtotal.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Tax</p>
                  <p className="font-medium font-mono">
                    ${invoice.tax_amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
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
              <CardTitle className="text-base">Line Items</CardTitle>
            </CardHeader>
            <CardContent className="px-0">
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
                  {lineItems.map((item) => (
                    <TableRow key={item.line}>
                      <TableCell className="text-muted-foreground">
                        {item.line}
                      </TableCell>
                      <TableCell className="font-medium">
                        {item.description}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {item.qty}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        ${item.unitPrice.toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right font-mono font-medium">
                        ${item.total.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell>
                        <ConfidenceIndicator confidence={item.confidence} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Match Results */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Match Results</CardTitle>
                <Badge
                  variant="outline"
                  className="bg-green-50 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300"
                >
                  {matchResult.match_type === "three_way" ? "3-Way Match" : "2-Way Match"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="space-y-1">
                  <p className="text-muted-foreground">Match Score</p>
                  <p className="text-xl font-bold text-green-600">
                    {matchResult.overall_score}%
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Status</p>
                  <Badge
                    variant="outline"
                    className="bg-green-50 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300"
                  >
                    Matched
                  </Badge>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Purchase Order</p>
                  <p className="font-medium text-primary">{matchResult.po_number}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Goods Receipt</p>
                  <p className="font-medium text-primary">{matchResult.grn_number}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Price Variance</p>
                  <p className="font-medium">{matchResult.price_variance}%</p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Quantity Variance</p>
                  <p className="font-medium">{matchResult.quantity_variance}%</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Exceptions */}
          {exceptions.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <AlertTriangle className="size-4 text-amber-500" />
                  Exceptions ({exceptions.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {exceptions.map((exc) => (
                  <div
                    key={exc.id}
                    className="flex items-start gap-3 rounded-lg border p-3"
                  >
                    <SeverityIcon severity={exc.severity} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <ExceptionTypeBadge type={exc.type} />
                        <Badge
                          variant="outline"
                          className="bg-green-50 text-green-700 border-green-200 text-[10px]"
                        >
                          Auto-Resolved
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        {exc.description}
                      </p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Approval Status */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Approval</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-3 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 p-3">
                <Clock className="size-5 text-amber-600 shrink-0" />
                <div>
                  <p className="text-sm font-medium">Pending Approval</p>
                  <p className="text-xs text-muted-foreground">
                    Assigned to Kyle S. &middot; Level 1 approval required for amounts over $10,000
                  </p>
                </div>
              </div>
              <div className="mt-3 rounded-lg bg-primary/5 border p-3">
                <p className="text-xs text-muted-foreground mb-1">AI Recommendation</p>
                <div className="flex items-center gap-2">
                  <Badge className="bg-green-600 text-white">Approve</Badge>
                  <span className="text-sm font-medium">95% confidence</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  3-way match verified, all variances within tolerance, vendor in good standing.
                </p>
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
          {comments.map((c) => (
            <div key={c.id} className="flex gap-3">
              <Avatar className="size-8 shrink-0">
                <AvatarFallback
                  className={
                    c.isAI
                      ? "bg-primary text-primary-foreground text-xs"
                      : "bg-secondary text-secondary-foreground text-xs"
                  }
                >
                  {c.initials}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{c.user}</span>
                  {c.isAI && (
                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                      AI
                    </Badge>
                  )}
                  <span className="text-xs text-muted-foreground">
                    {c.timestamp}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {c.content}
                </p>
              </div>
            </div>
          ))}

          <Separator />

          {/* New Comment */}
          <div className="flex gap-3">
            <Avatar className="size-8 shrink-0">
              <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                KS
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 space-y-2">
              <Textarea
                placeholder="Add a comment... Use @mention to tag someone"
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
