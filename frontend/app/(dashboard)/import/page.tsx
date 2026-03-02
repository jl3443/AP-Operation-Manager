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
} from "lucide-react"
import { toast } from "sonner"

import {
  useImportPurchaseOrders,
  useImportGoodsReceipts,
  useImportVendors,
} from "@/hooks/use-import"
import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
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

interface ImportRecord {
  id: string
  type: string
  status: "completed" | "failed"
  records: number
  failed: number
  date: string
  errors?: string[]
}

const importCards = [
  {
    key: "purchase_orders" as const,
    title: "Purchase Orders",
    description: "Import purchase orders from your ERP system to enable automated invoice matching.",
    icon: Package,
    templateName: "purchase_orders_template.csv",
    fields: "PO Number, Vendor Code, Line Items, Quantities, Prices",
  },
  {
    key: "goods_receipts" as const,
    title: "Goods Receipts",
    description: "Import goods receipt notes (GRNs) for three-way matching with invoices and POs.",
    icon: Truck,
    templateName: "goods_receipts_template.csv",
    fields: "GRN Number, PO Number, Vendor Code, Received Quantities",
  },
  {
    key: "vendors" as const,
    title: "Vendor Master Data",
    description: "Import or update your vendor master data including payment terms and banking info.",
    icon: Building2,
    templateName: "vendor_master_template.csv",
    fields: "Vendor Code, Name, Address, Tax ID, Payment Terms",
  },
]

const statusConfig = {
  completed: { icon: CheckCircle, className: "text-green-600", label: "Completed" },
  failed: { icon: XCircle, className: "text-red-600", label: "Failed" },
}

export default function ImportPage() {
  const fileInputRefs = React.useRef<Record<number, HTMLInputElement | null>>({})
  const [importHistory, setImportHistory] = React.useState<ImportRecord[]>([])

  const poMutation = useImportPurchaseOrders()
  const grMutation = useImportGoodsReceipts()
  const vendorMutation = useImportVendors()

  const mutations = {
    purchase_orders: poMutation,
    goods_receipts: grMutation,
    vendors: vendorMutation,
  }

  function handleUpload(index: number) {
    fileInputRefs.current[index]?.click()
  }

  function handleFileChange(cardKey: "purchase_orders" | "goods_receipts" | "vendors", title: string, index: number) {
    const fileInput = fileInputRefs.current[index]
    const file = fileInput?.files?.[0]
    if (!file) return

    const mutation = mutations[cardKey]

    mutation.mutate(file, {
      onSuccess: (data) => {
        const record: ImportRecord = {
          id: `imp-${Date.now()}`,
          type: title,
          status: data.errors > 0 && data.created === 0 ? "failed" : "completed",
          records: data.created,
          failed: data.errors,
          date: new Date().toLocaleString(),
          errors: data.error_details,
        }
        setImportHistory((prev) => [record, ...prev])
        toast.success(`${title}: ${data.created} record(s) imported${data.errors > 0 ? `, ${data.errors} error(s)` : ""}`)
      },
      onError: (err) => {
        const record: ImportRecord = {
          id: `imp-${Date.now()}`,
          type: title,
          status: "failed",
          records: 0,
          failed: 0,
          date: new Date().toLocaleString(),
        }
        setImportHistory((prev) => [record, ...prev])
        toast.error(`${title} import failed: ${err.message}`)
      },
    })

    // Reset input so re-selecting the same file triggers onChange
    if (fileInput) fileInput.value = ""
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
          const mutation = mutations[card.key]
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
                  disabled={mutation.isPending}
                >
                  {mutation.isPending ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    <Upload className="size-3.5" />
                  )}
                  {mutation.isPending ? "Importing..." : "Upload"}
                </Button>
                <input
                  ref={(el) => { fileInputRefs.current[index] = el }}
                  type="file"
                  accept=".csv,.xlsx"
                  className="hidden"
                  onChange={() => handleFileChange(card.key, card.title, index)}
                />
              </CardFooter>
            </Card>
          )
        })}
      </div>

      {/* Import History (session-local) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <FileSpreadsheet className="size-4" />
            Import History
          </CardTitle>
        </CardHeader>
        <CardContent className="px-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Records Created</TableHead>
                <TableHead className="text-right">Errors</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {importHistory.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground py-12">
                    No imports yet this session. Upload a CSV file above to get started.
                  </TableCell>
                </TableRow>
              )}
              {importHistory.map((imp) => {
                const status = statusConfig[imp.status]
                const StatusIcon = status.icon
                return (
                  <TableRow key={imp.id}>
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
