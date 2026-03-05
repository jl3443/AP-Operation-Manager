"use client"

import * as React from "react"
import { CheckCircle2, Edit3, Loader2, Mail, Send } from "lucide-react"
import { toast } from "sonner"

import { useSimulateSendEmail } from "@/hooks/use-invoices"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import type { AutomationAction } from "@/lib/types"

export function EmailDraftCard({
  action,
  invoiceId,
  onSent,
}: {
  action: AutomationAction
  invoiceId: string
  onSent?: () => void
}) {
  const result = action.result_json as {
    to?: string
    subject?: string
    body?: string
    vendor_name?: string
    status?: string
  } | undefined

  const [editing, setEditing] = React.useState(false)
  const [sent, setSent] = React.useState(false)
  const [to, setTo] = React.useState(result?.to || "")
  const [subject, setSubject] = React.useState(result?.subject || "")
  const [body, setBody] = React.useState(result?.body || "")

  const sendEmail = useSimulateSendEmail()

  if (sent) {
    return (
      <Card className="border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950/30">
        <CardContent className="py-4 flex items-center gap-3">
          <CheckCircle2 className="size-5 text-green-600 shrink-0" />
          <div>
            <p className="text-sm font-medium text-green-800 dark:text-green-200">
              Email Sent Successfully
            </p>
            <p className="text-xs text-green-600 dark:text-green-400">
              Email sent to {to} — awaiting vendor response
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/30">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Mail className="size-4 text-blue-600" />
            Vendor Email Draft
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setEditing(!editing)}
            className="text-xs"
          >
            <Edit3 className="size-3 mr-1" />
            {editing ? "Preview" : "Edit"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {editing ? (
          <>
            <div className="space-y-1.5">
              <Label className="text-xs">To</Label>
              <Input
                value={to}
                onChange={(e) => setTo(e.target.value)}
                className="text-sm bg-white dark:bg-slate-900"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Subject</Label>
              <Input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="text-sm bg-white dark:bg-slate-900"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Body</Label>
              <Textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={6}
                className="text-sm bg-white dark:bg-slate-900 resize-none"
              />
            </div>
          </>
        ) : (
          <div className="bg-white dark:bg-slate-900 rounded-lg border p-3 space-y-2">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="font-medium">To:</span>
              <span>{to}</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="font-medium">Subject:</span>
              <span>{subject}</span>
            </div>
            <div className="border-t pt-2 mt-2">
              <p className="text-sm text-foreground whitespace-pre-line leading-relaxed">
                {body}
              </p>
            </div>
          </div>
        )}

        <Button
          size="sm"
          className="bg-blue-600 hover:bg-blue-700 w-full"
          disabled={sendEmail.isPending}
          onClick={() => {
            sendEmail.mutate(
              { invoiceId, actionId: action.id, to, subject, body },
              {
                onSuccess: () => {
                  setSent(true)
                  toast.success("Email sent successfully")
                  onSent?.()
                },
                onError: (err) => toast.error(String(err)),
              }
            )
          }}
        >
          {sendEmail.isPending ? (
            <Loader2 className="size-3.5 mr-1.5 animate-spin" />
          ) : (
            <Send className="size-3.5 mr-1.5" />
          )}
          Send Email
        </Button>
      </CardContent>
    </Card>
  )
}
