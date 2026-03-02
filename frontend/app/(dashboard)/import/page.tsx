"use client"

import * as React from "react"
import {
  Upload,
  FileSpreadsheet,
  Download,
  Package,
  Truck,
  Building2,
  CheckCircle,
  XCircle,
  Loader2,
  Clock,
} from "lucide-react"
import { toast } from "sonner"

import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const importCards = [
  {
    title: "Purchase Orders",
    description: "Import purchase orders from your ERP system to enable automated invoice matching.",
    icon: Package,
    templateName: "purchase_orders_template.csv",
    fields: "PO Number, Vendor Code, Line Items, Quantities, Prices",
  },
  {
    title: "Goods Receipts",
    description: "Import goods receipt notes (GRNs) for three-way matching with invoices and POs.",
    icon: Truck,
    templateName: "goods_receipts_template.csv",
    fields: "GRN Number, PO Number, Vendor Code, Received Quantities",
  },
  {
    title: "Vendor Master Data",
    description: "Import or update your vendor master data including payment terms and banking info.",
    icon: Building2,
    templateName: "vendor_master_template.csv",
    fields: "Vendor Code, Name, Address, Tax ID, Payment Terms",
  },
]

const recentImports = [
  { id: "imp-001", type: "Purchase Orders", status: "completed", records: 245, failed: 2, date: "2024-02-28 14:30", duration: "12s" },
  { id: "imp-002", type: "Goods Receipts", status: "completed", records: 189, failed: 0, date: "2024-02-28 10:15", duration: "8s" },
  { id: "imp-003", type: "Vendor Master Data", status: "completed", records: 45, failed: 1, date: "2024-02-27 16:45", duration: "3s" },
  { id: "imp-004", type: "Purchase Orders", status: "failed", records: 0, failed: 312, date: "2024-02-27 09:00", duration: "1s" },
  { id: "imp-005", type: "Goods Receipts", status: "processing", records: 156, failed: 0, date: "2024-02-26 11:30", duration: "..." },
]

const statusConfig: Record<string, { icon: React.ElementType; className: string; label: string }> = {
  completed: { icon: CheckCircle, className: "text-green-600", label: "Completed" },
  failed: { icon: XCircle, className: "text-red-600", label: "Failed" },
  processing: { icon: Loader2, className: "text-primary animate-spin", label: "Processing" },
  pending: { icon: Clock, className: "text-amber-600", label: "Pending" },
}

export default function ImportPage() {
  const fileInputRefs = React.useRef<Record<number, HTMLInputElement | null>>({})

  function handleUpload(index: number) {
    fileInputRefs.current[index]?.click()
  }

  function handleFileChange(type: string) {
    toast.success(`${type} file uploaded successfully. Processing started.`)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Data Import"
        description="Import master data from your ERP system"
      />

      {/* Import Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {importCards.map((card, index) => {
          const Icon = card.icon
          return (
            <Card key={card.title}>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-primary/10 p-2.5">
                    <Icon className="size-5 text-primary" />
                  </div>
                  <CardTitle className="text-base">{card.title}</CardTitle>
                </div>
                <CardDescription className="mt-2">
                  {card.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">Fields: </span>
                  {card.fields}
                </div>
              </CardContent>
              <CardFooter className="flex gap-2">
                <Button variant="outline" size="sm" className="flex-1">
                  <Download className="size-3.5" />
                  Template
                </Button>
                <Button
                  size="sm"
                  className="flex-1"
                  onClick={() => handleUpload(index)}
                >
                  <Upload className="size-3.5" />
                  Upload
                </Button>
                <input
                  ref={(el) => { fileInputRefs.current[index] = el }}
                  type="file"
                  accept=".csv,.xlsx"
                  className="hidden"
                  onChange={() => handleFileChange(card.title)}
                />
              </CardFooter>
            </Card>
          )
        })}
      </div>

      {/* Recent Imports */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <FileSpreadsheet className="size-4" />
            Recent Imports
          </CardTitle>
        </CardHeader>
        <CardContent className="px-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Job ID</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Records</TableHead>
                <TableHead className="text-right">Failed</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Duration</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recentImports.map((imp) => {
                const status = statusConfig[imp.status]
                const StatusIcon = status.icon
                return (
                  <TableRow key={imp.id}>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {imp.id}
                    </TableCell>
                    <TableCell className="font-medium">{imp.type}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <StatusIcon className={`size-3.5 ${status.className}`} />
                        <span className="text-sm">{status.label}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {imp.records.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      {imp.failed > 0 ? (
                        <span className="text-red-600 font-mono">{imp.failed}</span>
                      ) : (
                        <span className="text-muted-foreground font-mono">0</span>
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {imp.date}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {imp.duration}
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
