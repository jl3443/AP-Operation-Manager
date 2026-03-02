"use client"

import * as React from "react"
import Link from "next/link"
import {
  Plus,
  Search,
  Filter,
  Download,
  MoreHorizontal,
  Eye,
  Pencil,
  Trash2,
} from "lucide-react"

import { PageHeader } from "@/components/page-header"
import { InvoiceStatusBadge } from "@/components/invoice-status-badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from "@/components/ui/pagination"
import { Card, CardContent } from "@/components/ui/card"
import type { InvoiceStatus, SourceChannel } from "@/lib/types"

// Mock Data
const mockInvoices: Array<{
  id: string
  number: string
  vendor: string
  date: string
  due_date: string
  amount: number
  status: InvoiceStatus
  source: SourceChannel
  confidence: number
}> = [
  { id: "inv-001", number: "INV-2024-0892", vendor: "Acme Corp", date: "2024-02-28", due_date: "2024-03-28", amount: 12450.00, status: "pending_approval", source: "email", confidence: 96 },
  { id: "inv-002", number: "INV-2024-0891", vendor: "TechParts Ltd", date: "2024-02-28", due_date: "2024-03-30", amount: 3280.50, status: "extracted", source: "manual", confidence: 92 },
  { id: "inv-003", number: "INV-2024-0890", vendor: "Global Supply Co", date: "2024-02-27", due_date: "2024-03-27", amount: 45670.00, status: "exception", source: "email", confidence: 67 },
  { id: "inv-004", number: "INV-2024-0889", vendor: "Office Depot", date: "2024-02-27", due_date: "2024-04-01", amount: 892.15, status: "approved", source: "api", confidence: 99 },
  { id: "inv-005", number: "INV-2024-0888", vendor: "CloudServ Inc", date: "2024-02-26", due_date: "2024-03-26", amount: 7500.00, status: "posted", source: "csv", confidence: 98 },
  { id: "inv-006", number: "INV-2024-0887", vendor: "Steel Works Ltd", date: "2024-02-26", due_date: "2024-03-28", amount: 23100.00, status: "matching", source: "email", confidence: 89 },
  { id: "inv-007", number: "INV-2024-0886", vendor: "PackRight Inc", date: "2024-02-25", due_date: "2024-03-25", amount: 1560.00, status: "draft", source: "manual", confidence: 75 },
  { id: "inv-008", number: "INV-2024-0885", vendor: "Metro Electric", date: "2024-02-25", due_date: "2024-03-27", amount: 8420.00, status: "approved", source: "email", confidence: 94 },
  { id: "inv-009", number: "INV-2024-0884", vendor: "Acme Corp", date: "2024-02-24", due_date: "2024-03-24", amount: 5670.00, status: "posted", source: "api", confidence: 97 },
  { id: "inv-010", number: "INV-2024-0883", vendor: "FreshFoods Co", date: "2024-02-24", due_date: "2024-03-26", amount: 2340.80, status: "pending_approval", source: "manual", confidence: 91 },
]

const sourceLabels: Record<SourceChannel, string> = {
  manual: "Manual",
  email: "Email",
  api: "API",
  csv: "CSV",
}

export default function InvoicesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Invoices"
        description="Manage and track all incoming invoices"
      >
        <Button variant="outline" size="sm">
          <Download className="size-4" />
          Export
        </Button>
        <Button size="sm" asChild>
          <Link href="/invoices/upload">
            <Plus className="size-4" />
            Upload Invoice
          </Link>
        </Button>
      </PageHeader>

      {/* Filter Bar */}
      <Card className="py-3">
        <CardContent className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="Search by invoice #, vendor..." className="pl-9 h-8" />
          </div>
          <Select>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="All Statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="extracted">Extracted</SelectItem>
              <SelectItem value="matching">Matching</SelectItem>
              <SelectItem value="exception">Exception</SelectItem>
              <SelectItem value="pending_approval">Pending Approval</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="posted">Posted</SelectItem>
            </SelectContent>
          </Select>
          <Select>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="All Sources" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sources</SelectItem>
              <SelectItem value="manual">Manual</SelectItem>
              <SelectItem value="email">Email</SelectItem>
              <SelectItem value="api">API</SelectItem>
              <SelectItem value="csv">CSV</SelectItem>
            </SelectContent>
          </Select>
          <Input type="date" className="w-[140px] h-9" placeholder="From Date" />
          <Input type="date" className="w-[140px] h-9" placeholder="To Date" />
          <Button variant="outline" size="sm">
            <Filter className="size-4" />
            More Filters
          </Button>
        </CardContent>
      </Card>

      {/* Data Table */}
      <Card className="py-0">
        <CardContent className="px-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Invoice #</TableHead>
                <TableHead>Vendor</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Source</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockInvoices.map((invoice) => (
                <TableRow key={invoice.id}>
                  <TableCell>
                    <Link
                      href={`/invoices/${invoice.id}`}
                      className="font-medium text-primary hover:underline"
                    >
                      {invoice.number}
                    </Link>
                  </TableCell>
                  <TableCell className="font-medium">{invoice.vendor}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {invoice.date}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    ${invoice.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                  </TableCell>
                  <TableCell>
                    <InvoiceStatusBadge status={invoice.status} />
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="text-xs">
                      {sourceLabels[invoice.source]}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon-sm">
                          <MoreHorizontal className="size-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem asChild>
                          <Link href={`/invoices/${invoice.id}`}>
                            <Eye className="size-4" />
                            View Details
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Pencil className="size-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem variant="destructive">
                          <Trash2 className="size-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Showing <span className="font-medium">1-10</span> of{" "}
          <span className="font-medium">1,245</span> invoices
        </p>
        <Pagination className="w-auto mx-0">
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious href="#" />
            </PaginationItem>
            <PaginationItem>
              <PaginationLink href="#" isActive>
                1
              </PaginationLink>
            </PaginationItem>
            <PaginationItem>
              <PaginationLink href="#">2</PaginationLink>
            </PaginationItem>
            <PaginationItem>
              <PaginationLink href="#">3</PaginationLink>
            </PaginationItem>
            <PaginationItem>
              <PaginationEllipsis />
            </PaginationItem>
            <PaginationItem>
              <PaginationLink href="#">125</PaginationLink>
            </PaginationItem>
            <PaginationItem>
              <PaginationNext href="#" />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      </div>
    </div>
  )
}
