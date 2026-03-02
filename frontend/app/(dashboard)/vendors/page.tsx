"use client"

import * as React from "react"
import Link from "next/link"
import {
  Building2,
  Search,
  Plus,
  MoreHorizontal,
  Eye,
  Pencil,
  Shield,
  ShieldAlert,
  ShieldCheck,
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"
import type { VendorStatus, RiskLevel } from "@/lib/types"

const mockVendors: Array<{
  id: string
  vendor_code: string
  name: string
  city: string
  state: string
  status: VendorStatus
  risk_level: RiskLevel
  payment_terms: string
  total_invoices: number
  open_balance: number
}> = [
  { id: "v-001", vendor_code: "V-1001", name: "Acme Corp", city: "New York", state: "NY", status: "active", risk_level: "low", payment_terms: "Net 30", total_invoices: 89, open_balance: 45230.00 },
  { id: "v-002", vendor_code: "V-1002", name: "TechParts Ltd", city: "San Jose", state: "CA", status: "active", risk_level: "low", payment_terms: "Net 45", total_invoices: 67, open_balance: 18750.50 },
  { id: "v-003", vendor_code: "V-1003", name: "Global Supply Co", city: "Chicago", state: "IL", status: "active", risk_level: "medium", payment_terms: "Net 30", total_invoices: 54, open_balance: 67800.00 },
  { id: "v-004", vendor_code: "V-1004", name: "Steel Works Ltd", city: "Pittsburgh", state: "PA", status: "on_hold", risk_level: "high", payment_terms: "Net 15", total_invoices: 42, open_balance: 23100.00 },
  { id: "v-005", vendor_code: "V-1005", name: "Office Depot", city: "Boca Raton", state: "FL", status: "active", risk_level: "low", payment_terms: "Net 30", total_invoices: 38, open_balance: 892.15 },
  { id: "v-006", vendor_code: "V-1006", name: "CloudServ Inc", city: "Seattle", state: "WA", status: "active", risk_level: "low", payment_terms: "Net 30", total_invoices: 35, open_balance: 15000.00 },
  { id: "v-007", vendor_code: "V-1007", name: "Metro Electric", city: "Dallas", state: "TX", status: "blocked", risk_level: "high", payment_terms: "Net 30", total_invoices: 28, open_balance: 0.00 },
  { id: "v-008", vendor_code: "V-1008", name: "PackRight Inc", city: "Denver", state: "CO", status: "active", risk_level: "medium", payment_terms: "Net 60", total_invoices: 22, open_balance: 4560.00 },
]

const statusConfig: Record<VendorStatus, { label: string; className: string }> = {
  active: { label: "Active", className: "bg-green-50 text-green-700 border-green-200" },
  on_hold: { label: "On Hold", className: "bg-amber-50 text-amber-700 border-amber-200" },
  blocked: { label: "Blocked", className: "bg-red-50 text-red-700 border-red-200" },
}

const riskConfig: Record<RiskLevel, { icon: React.ElementType; label: string; className: string }> = {
  low: { icon: ShieldCheck, label: "Low", className: "text-green-600" },
  medium: { icon: Shield, label: "Medium", className: "text-amber-600" },
  high: { icon: ShieldAlert, label: "High", className: "text-red-600" },
}

export default function VendorsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Vendor Management"
        description="Manage vendor master data and risk profiles"
      >
        <Button size="sm">
          <Plus className="size-4" />
          Add Vendor
        </Button>
      </PageHeader>

      {/* Filter Bar */}
      <Card className="py-3">
        <CardContent className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="Search vendors..." className="pl-9 h-8" />
          </div>
          <Select>
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="on_hold">On Hold</SelectItem>
              <SelectItem value="blocked">Blocked</SelectItem>
            </SelectContent>
          </Select>
          <Select>
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="Risk Level" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Risk</SelectItem>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="high">High</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Vendor Table */}
      <Card className="py-0">
        <CardContent className="px-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Vendor Code</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Terms</TableHead>
                <TableHead className="text-right">Invoices</TableHead>
                <TableHead className="text-right">Open Balance</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockVendors.map((vendor) => {
                const status = statusConfig[vendor.status]
                const risk = riskConfig[vendor.risk_level]
                const RiskIcon = risk.icon
                return (
                  <TableRow key={vendor.id}>
                    <TableCell className="font-mono text-xs">
                      {vendor.vendor_code}
                    </TableCell>
                    <TableCell className="font-medium">{vendor.name}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {vendor.city}, {vendor.state}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={status.className}>
                        {status.label}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <RiskIcon className={cn("size-4", risk.className)} />
                        <span className={cn("text-sm", risk.className)}>
                          {risk.label}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {vendor.payment_terms}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {vendor.total_invoices}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      ${vendor.open_balance.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon-sm">
                            <MoreHorizontal className="size-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>
                            <Eye className="size-4" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Pencil className="size-4" />
                            Edit
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
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
