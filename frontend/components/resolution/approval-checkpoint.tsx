"use client"

import * as React from "react"
import {
  Bot,
  CheckCircle2,
  Loader2,
  MessageSquare,
  Send,
  Shield,
} from "lucide-react"
import { toast } from "sonner"

import { useApproveAndContinue, useRedirectAction } from "@/hooks/use-exceptions"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { friendlyActionType } from "./compact-step"
import type { AutomationAction } from "@/lib/types"

export function ApprovalCheckpoint({
  action,
  exceptionId,
  onComplete,
}: {
  action: AutomationAction
  exceptionId: string
  onComplete: () => void
}) {
  const [showRedirect, setShowRedirect] = React.useState(false)
  const [instructions, setInstructions] = React.useState("")
  const approveAndContinue = useApproveAndContinue()
  const redirectAction = useRedirectAction()

  const params = (action.params_json || {}) as { vendor_name?: string; subject?: string; body_template?: string }
  const hasEmailDraft = params.subject || params.body_template
  const result = action.result_json as { body?: string } | undefined

  return (
    <div className="space-y-3">
      <Card className="border-amber-300 bg-amber-50/50">
        <CardContent className="py-4 space-y-3">
          <div className="flex items-center gap-2">
            <div className="size-6 rounded bg-amber-400 flex items-center justify-center rotate-45">
              <Shield className="size-3.5 text-white -rotate-45" />
            </div>
            <div>
              <p className="text-sm font-medium">Approval Required</p>
              <p className="text-xs text-muted-foreground">{friendlyActionType(action.action_type)}</p>
            </div>
          </div>

          {action.expected_result && (
            <p className="text-sm text-foreground leading-relaxed">{action.expected_result}</p>
          )}

          {hasEmailDraft && (
            <div className="bg-white rounded-lg border p-3 space-y-2">
              <div className="flex items-center gap-2">
                <MessageSquare className="size-3.5 text-slate-400" />
                <span className="text-xs font-medium">Email Draft</span>
              </div>
              {params.vendor_name && (
                <p className="text-xs text-muted-foreground">To: {params.vendor_name}</p>
              )}
              {params.subject && (
                <p className="text-sm font-medium">{params.subject}</p>
              )}
              {result?.body && (
                <p className="text-xs text-muted-foreground leading-relaxed whitespace-pre-line line-clamp-6">{result.body}</p>
              )}
            </div>
          )}

          {!showRedirect ? (
            <div className="flex items-center gap-2 pt-1">
              <Button
                size="sm"
                onClick={() => {
                  approveAndContinue.mutate(
                    { exceptionId, actionId: action.id },
                    {
                      onSuccess: () => {
                        toast.success("Approved — continuing execution")
                        onComplete()
                      },
                      onError: (err) => toast.error(String(err)),
                    }
                  )
                }}
                disabled={approveAndContinue.isPending}
                className="bg-green-600 hover:bg-green-700"
              >
                {approveAndContinue.isPending ? (
                  <Loader2 className="size-3 mr-1.5 animate-spin" />
                ) : (
                  <CheckCircle2 className="size-3 mr-1.5" />
                )}
                Approve
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowRedirect(true)}
              >
                <Bot className="size-3 mr-1.5" />
                Tell Claude what to do instead
              </Button>
            </div>
          ) : (
            <div className="space-y-2 pt-1">
              <textarea
                className="w-full text-sm border rounded-lg p-2.5 min-h-[80px] resize-none focus:outline-none focus:ring-2 focus:ring-violet-300"
                placeholder="Tell Claude what you'd like to do differently..."
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                autoFocus
              />
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  onClick={() => {
                    if (!instructions.trim()) return
                    redirectAction.mutate(
                      { exceptionId, actionId: action.id, instructions },
                      {
                        onSuccess: () => {
                          toast.success("Claude is updating the approach...")
                          setShowRedirect(false)
                          setInstructions("")
                          onComplete()
                        },
                        onError: (err) => toast.error(String(err)),
                      }
                    )
                  }}
                  disabled={redirectAction.isPending || !instructions.trim()}
                  className="bg-violet-600 hover:bg-violet-700"
                >
                  {redirectAction.isPending ? (
                    <Loader2 className="size-3 mr-1.5 animate-spin" />
                  ) : (
                    <Send className="size-3 mr-1.5" />
                  )}
                  Send to Claude
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setShowRedirect(false)}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
