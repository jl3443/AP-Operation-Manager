"use client"

import * as React from "react"
import {
  Search,
  Plus,
  MoreHorizontal,
  Eye,
  Pencil,
  Trash2,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Loader2,
} from "lucide-react"
import { toast } from "sonner"

import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { cn } from "@/lib/utils"
import type { Vendor, VendorStatus, RiskLevel } from "@/lib/types"
import {
  useVendors,
  useCreateVendor,
  useUpdateVendor,
  useDeleteVendor,
} from "@/hooks/use-vendors"

// ---------------------------------------------------------------------------
// Config maps
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Form state type
// ---------------------------------------------------------------------------

interface VendorFormState {
  name: string
  vendor_code: string
  city: string
  state: string
  country: string
  payment_terms_code: string
  status: string
  risk_level: string
}

const emptyForm: VendorFormState = {
  name: "",
  vendor_code: "",
  city: "",
  state: "",
  country: "US",
  payment_terms_code: "Net30",
  status: "active",
  risk_level: "low",
}

// ---------------------------------------------------------------------------
// VendorDialog — shared for create & edit
// ---------------------------------------------------------------------------

function VendorDialog({
  open,
  onOpenChange,
  vendor,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  vendor: Vendor | null // null = create mode
}) {
  const isEdit = vendor !== null

  const [form, setForm] = React.useState<VendorFormState>(emptyForm)

  // Reset form whenever the dialog opens or the vendor changes
  React.useEffect(() => {
    if (open) {
      if (vendor) {
        setForm({
          name: vendor.name,
          vendor_code: vendor.vendor_code,
          city: vendor.city ?? "",
          state: vendor.state ?? "",
          country: vendor.country ?? "US",
          payment_terms_code: vendor.payment_terms_code ?? "Net30",
          status: vendor.status,
          risk_level: vendor.risk_level,
        })
      } else {
        setForm(emptyForm)
      }
    }
  }, [open, vendor])

  const createVendor = useCreateVendor()
  const updateVendor = useUpdateVendor()

  const isPending = createVendor.isPending || updateVendor.isPending

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!form.name.trim() || !form.vendor_code.trim()) {
      toast.error("Name and vendor code are required")
      return
    }

    const payload = {
      name: form.name.trim(),
      vendor_code: form.vendor_code.trim(),
      city: form.city.trim() || undefined,
      state: form.state.trim() || undefined,
      country: form.country.trim() || undefined,
      payment_terms_code: form.payment_terms_code || undefined,
      status: form.status || undefined,
      risk_level: form.risk_level || undefined,
    }

    if (isEdit) {
      updateVendor.mutate(
        { id: vendor.id, ...payload },
        {
          onSuccess: () => {
            toast.success(`Vendor "${payload.name}" updated`)
            onOpenChange(false)
          },
          onError: (err) => {
            toast.error(`Update failed: ${err.message}`)
          },
        },
      )
    } else {
      createVendor.mutate(payload, {
        onSuccess: () => {
          toast.success(`Vendor "${payload.name}" created`)
          onOpenChange(false)
        },
        onError: (err) => {
          toast.error(`Create failed: ${err.message}`)
        },
      })
    }
  }

  const setField = <K extends keyof VendorFormState>(
    key: K,
    value: VendorFormState[K],
  ) => setForm((prev) => ({ ...prev, [key]: value }))

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Vendor" : "Add Vendor"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update the vendor details below."
              : "Fill in the details to create a new vendor."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="grid gap-4 py-2">
          {/* Name */}
          <div className="grid gap-2">
            <Label htmlFor="vendor-name">
              Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="vendor-name"
              value={form.name}
              onChange={(e) => setField("name", e.target.value)}
              placeholder="Acme Corp"
              required
            />
          </div>

          {/* Vendor Code */}
          <div className="grid gap-2">
            <Label htmlFor="vendor-code">
              Vendor Code <span className="text-destructive">*</span>
            </Label>
            <Input
              id="vendor-code"
              value={form.vendor_code}
              onChange={(e) => setField("vendor_code", e.target.value)}
              placeholder="V-1001"
              required
            />
          </div>

          {/* City / State row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="vendor-city">City</Label>
              <Input
                id="vendor-city"
                value={form.city}
                onChange={(e) => setField("city", e.target.value)}
                placeholder="New York"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="vendor-state">State</Label>
              <Input
                id="vendor-state"
                value={form.state}
                onChange={(e) => setField("state", e.target.value)}
                placeholder="NY"
              />
            </div>
          </div>

          {/* Country */}
          <div className="grid gap-2">
            <Label htmlFor="vendor-country">Country</Label>
            <Input
              id="vendor-country"
              value={form.country}
              onChange={(e) => setField("country", e.target.value)}
              placeholder="US"
            />
          </div>

          {/* Payment Terms */}
          <div className="grid gap-2">
            <Label>Payment Terms</Label>
            <Select
              value={form.payment_terms_code}
              onValueChange={(v) => setField("payment_terms_code", v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select terms" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Net15">Net 15</SelectItem>
                <SelectItem value="Net30">Net 30</SelectItem>
                <SelectItem value="Net45">Net 45</SelectItem>
                <SelectItem value="Net60">Net 60</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Status / Risk row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label>Status</Label>
              <Select
                value={form.status}
                onValueChange={(v) => setField("status", v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="on_hold">On Hold</SelectItem>
                  <SelectItem value="blocked">Blocked</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label>Risk Level</Label>
              <Select
                value={form.risk_level}
                onValueChange={(v) => setField("risk_level", v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select risk" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="size-4 animate-spin" />}
              {isEdit ? "Save Changes" : "Create Vendor"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Delete confirmation dialog
// ---------------------------------------------------------------------------

function DeleteVendorDialog({
  open,
  onOpenChange,
  vendor,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  vendor: Vendor | null
}) {
  const deleteVendor = useDeleteVendor()

  const handleDelete = () => {
    if (!vendor) return
    deleteVendor.mutate(vendor.id, {
      onSuccess: () => {
        toast.success(`Vendor "${vendor.name}" deleted`)
        onOpenChange(false)
      },
      onError: (err) => {
        toast.error(`Delete failed: ${err.message}`)
      },
    })
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Vendor</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete vendor{" "}
            <span className="font-semibold">&ldquo;{vendor?.name}&rdquo;</span>?
            This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleteVendor.isPending}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={deleteVendor.isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {deleteVendor.isPending && (
              <Loader2 className="size-4 animate-spin" />
            )}
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function VendorsPage() {
  const [search, setSearch] = React.useState("")
  const [statusFilter, setStatusFilter] = React.useState<string | undefined>(undefined)
  const [riskFilter, setRiskFilter] = React.useState<string | undefined>(undefined)

  // Dialog state
  const [vendorDialogOpen, setVendorDialogOpen] = React.useState(false)
  const [editingVendor, setEditingVendor] = React.useState<Vendor | null>(null)

  // Delete dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false)
  const [deletingVendor, setDeletingVendor] = React.useState<Vendor | null>(null)

  const { data, isLoading } = useVendors({
    search,
    status: statusFilter,
    risk_level: riskFilter,
  })

  const openCreateDialog = () => {
    setEditingVendor(null)
    setVendorDialogOpen(true)
  }

  const openEditDialog = (vendor: Vendor) => {
    setEditingVendor(vendor)
    setVendorDialogOpen(true)
  }

  const openDeleteDialog = (vendor: Vendor) => {
    setDeletingVendor(vendor)
    setDeleteDialogOpen(true)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Vendor Management"
        description="Manage vendor master data and risk profiles"
      >
        <Button size="sm" onClick={openCreateDialog}>
          <Plus className="size-4" />
          Add Vendor
        </Button>
      </PageHeader>

      {/* Filter Bar */}
      <Card className="py-3">
        <CardContent className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="Search vendors..."
              className="pl-9 h-8"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select
            onValueChange={(value) =>
              setStatusFilter(value === "all" ? undefined : value)
            }
          >
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
          <Select
            onValueChange={(value) =>
              setRiskFilter(value === "all" ? undefined : value)
            }
          >
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
          {isLoading ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              Loading vendors...
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Vendor Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Risk</TableHead>
                  <TableHead>Terms</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.items.map((vendor) => {
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
                        {[vendor.city, vendor.state].filter(Boolean).join(", ") || "\u2014"}
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
                        {vendor.payment_terms_code ?? "\u2014"}
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
                            <DropdownMenuItem onClick={() => openEditDialog(vendor)}>
                              <Pencil className="size-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-destructive focus:text-destructive"
                              onClick={() => openDeleteDialog(vendor)}
                            >
                              <Trash2 className="size-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Vendor Create / Edit Dialog */}
      <VendorDialog
        open={vendorDialogOpen}
        onOpenChange={setVendorDialogOpen}
        vendor={editingVendor}
      />

      {/* Delete Confirmation Dialog */}
      <DeleteVendorDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        vendor={deletingVendor}
      />
    </div>
  )
}
