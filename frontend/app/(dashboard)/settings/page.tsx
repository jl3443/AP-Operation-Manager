"use client"

import * as React from "react"
import {
  Settings,
  User,
  Bell,
  Shield,
  Sliders,
  Building,
  Brain,
  Loader2,
} from "lucide-react"
import { toast } from "sonner"

import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useTolerances, useUpdateTolerance } from "@/hooks/use-settings"

export default function SettingsPage() {
  const { data: tolerances, isLoading: tolLoading } = useTolerances()
  const updateTolerance = useUpdateTolerance()

  // Find global tolerance config (fallback to first)
  const globalTol = tolerances?.find((t) => t.scope === "global") ?? tolerances?.[0]

  const [amtPct, setAmtPct] = React.useState("")
  const [amtAbs, setAmtAbs] = React.useState("")
  const [qtyPct, setQtyPct] = React.useState("")

  // Sync form state when data loads
  React.useEffect(() => {
    if (globalTol) {
      setAmtPct(String(globalTol.amount_tolerance_pct))
      setAmtAbs(String(globalTol.amount_tolerance_abs))
      setQtyPct(String(globalTol.quantity_tolerance_pct))
    }
  }, [globalTol])

  function handleSaveTolerances() {
    if (!globalTol) return
    updateTolerance.mutate(
      {
        id: globalTol.id,
        amount_tolerance_pct: parseFloat(amtPct) || 0,
        amount_tolerance_abs: parseFloat(amtAbs) || 0,
        quantity_tolerance_pct: parseFloat(qtyPct) || 0,
      },
      {
        onSuccess: () => toast.success("Tolerance settings saved"),
        onError: () => toast.error("Failed to save tolerance settings"),
      },
    )
  }
  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Configure system preferences and processing rules"
      />

      <Tabs defaultValue="general" className="space-y-4">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="processing">Processing Rules</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="ai">AI Settings</TabsTrigger>
        </TabsList>

        {/* General Settings */}
        <TabsContent value="general" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Building className="size-4" />
                Organization
              </CardTitle>
              <CardDescription>
                Configure your company and department settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Company Name</Label>
                  <Input defaultValue="Acme Industries Inc." />
                </div>
                <div className="space-y-2">
                  <Label>Default Currency</Label>
                  <Select defaultValue="usd">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="usd">USD - US Dollar</SelectItem>
                      <SelectItem value="eur">EUR - Euro</SelectItem>
                      <SelectItem value="gbp">GBP - British Pound</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Fiscal Year Start</Label>
                  <Select defaultValue="jan">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="jan">January</SelectItem>
                      <SelectItem value="apr">April</SelectItem>
                      <SelectItem value="jul">July</SelectItem>
                      <SelectItem value="oct">October</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Time Zone</Label>
                  <Select defaultValue="est">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="est">Eastern (EST)</SelectItem>
                      <SelectItem value="cst">Central (CST)</SelectItem>
                      <SelectItem value="pst">Pacific (PST)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex justify-end">
                <Button>Save Changes</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Processing Rules */}
        <TabsContent value="processing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Sliders className="size-4" />
                Matching Tolerances
              </CardTitle>
              <CardDescription>
                Set acceptable variance thresholds for automated matching
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {tolLoading ? (
                <div className="flex items-center justify-center py-8 text-muted-foreground">
                  <Loader2 className="size-4 animate-spin mr-2" />
                  Loading tolerances...
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Price Variance Tolerance (%)</Label>
                      <Input
                        type="number"
                        value={amtPct}
                        onChange={(e) => setAmtPct(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Quantity Variance Tolerance (%)</Label>
                      <Input
                        type="number"
                        value={qtyPct}
                        onChange={(e) => setQtyPct(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Amount Variance Tolerance ($)</Label>
                      <Input
                        type="number"
                        value={amtAbs}
                        onChange={(e) => setAmtAbs(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Tax Variance Tolerance (%)</Label>
                      <Input type="number" defaultValue="1" />
                    </div>
                  </div>
                  <Separator />
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Auto-approve within tolerance</Label>
                        <p className="text-xs text-muted-foreground">
                          Automatically approve invoices that match within tolerance thresholds
                        </p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Auto-resolve minor exceptions</Label>
                        <p className="text-xs text-muted-foreground">
                          Automatically resolve exceptions below the tolerance threshold
                        </p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Duplicate detection</Label>
                        <p className="text-xs text-muted-foreground">
                          Flag potential duplicate invoices based on vendor, amount, and date
                        </p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <Button
                      onClick={handleSaveTolerances}
                      disabled={updateTolerance.isPending}
                    >
                      {updateTolerance.isPending && (
                        <Loader2 className="size-4 animate-spin" />
                      )}
                      Save Changes
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Shield className="size-4" />
                Approval Thresholds
              </CardTitle>
              <CardDescription>
                Set approval levels based on invoice amounts
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Auto-Approve Limit ($)</Label>
                  <Input type="number" defaultValue="500" />
                  <p className="text-xs text-muted-foreground">
                    Invoices below this amount are auto-approved
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Level 1 Approval Limit ($)</Label>
                  <Input type="number" defaultValue="25000" />
                  <p className="text-xs text-muted-foreground">
                    Invoices below this amount need L1 approval only
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Level 2 Approval Limit ($)</Label>
                  <Input type="number" defaultValue="100000" />
                  <p className="text-xs text-muted-foreground">
                    Invoices below this amount need L2 approval
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>SLA Deadline (hours)</Label>
                  <Input type="number" defaultValue="48" />
                  <p className="text-xs text-muted-foreground">
                    Maximum time before an exception is escalated
                  </p>
                </div>
              </div>
              <div className="flex justify-end">
                <Button>Save Changes</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications */}
        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Bell className="size-4" />
                Notification Preferences
              </CardTitle>
              <CardDescription>
                Choose what notifications you receive
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { label: "New invoice received", desc: "When a new invoice is ingested into the system" },
                { label: "Exception created", desc: "When a new exception is flagged during matching" },
                { label: "Approval required", desc: "When an invoice is assigned to you for approval" },
                { label: "SLA at risk", desc: "When an exception is approaching its SLA deadline" },
                { label: "Import completed", desc: "When a data import job finishes processing" },
                { label: "AI auto-actions", desc: "When AI automatically resolves or approves items" },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between">
                  <div>
                    <Label>{item.label}</Label>
                    <p className="text-xs text-muted-foreground">{item.desc}</p>
                  </div>
                  <Switch defaultChecked />
                </div>
              ))}
              <div className="flex justify-end">
                <Button>Save Preferences</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Settings */}
        <TabsContent value="ai" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Brain className="size-4" />
                AI Configuration
              </CardTitle>
              <CardDescription>
                Configure AI-powered features and confidence thresholds
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>OCR Confidence Threshold (%)</Label>
                  <Input type="number" defaultValue="85" />
                  <p className="text-xs text-muted-foreground">
                    Fields below this confidence will be flagged for review
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Auto-Approve AI Confidence (%)</Label>
                  <Input type="number" defaultValue="95" />
                  <p className="text-xs text-muted-foreground">
                    Minimum AI confidence to enable auto-approval
                  </p>
                </div>
              </div>
              <Separator />
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>AI-powered field extraction</Label>
                    <p className="text-xs text-muted-foreground">
                      Use AI to extract invoice fields from documents
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>AI approval recommendations</Label>
                    <p className="text-xs text-muted-foreground">
                      Show AI recommendations alongside approval requests
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>AI exception routing</Label>
                    <p className="text-xs text-muted-foreground">
                      Let AI assign exceptions to the best-suited team member
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Anomaly detection</Label>
                    <p className="text-xs text-muted-foreground">
                      AI-powered detection of unusual invoices or patterns
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
              </div>
              <div className="flex justify-end">
                <Button>Save Configuration</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
