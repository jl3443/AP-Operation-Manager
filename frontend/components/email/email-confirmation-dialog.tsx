"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Loader2, Mail } from "lucide-react";

interface EmailPreview {
  to: string;
  subject: string;
  body: string;
  invoice_id: string;
  credit_amount?: number;
  action_id?: string;
}

interface EmailConfirmationDialogProps {
  open: boolean;
  preview: EmailPreview | null;
  isLoading?: boolean;
  onConfirm: (to: string, subject: string, body: string) => Promise<void>;
  onCancel: () => void;
}

export function EmailConfirmationDialog({
  open,
  preview,
  isLoading = false,
  onConfirm,
  onCancel,
}: EmailConfirmationDialogProps) {
  const [to, setTo] = useState(preview?.to || "");
  const [isSending, setIsSending] = useState(false);

  // Update recipient when preview changes
  useEffect(() => {
    if (preview && open) {
      setTo(preview.to);
    }
  }, [preview, open]);

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      onCancel();
    }
  };

  const handleSendEmail = async () => {
    if (!to.trim()) {
      toast.error("Please enter a recipient email address");
      return;
    }

    // Basic email validation
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(to)) {
      toast.error("Please enter a valid email address");
      return;
    }

    setIsSending(true);
    try {
      await onConfirm(to, preview?.subject || "", preview?.body || "");
      toast.success("Email sent successfully");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to send email");
    } finally {
      setIsSending(false);
    }
  };

  if (!preview) return null;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="size-5" />
            Email Preview
          </DialogTitle>
          <DialogDescription>
            Review and confirm the email before sending to {preview?.to}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 min-h-0">
          <div className="space-y-4 pr-4">
            {/* Recipient */}
            <div className="space-y-2">
              <Label htmlFor="to-email">To:</Label>
              <Input
                id="to-email"
                type="email"
                placeholder="recipient@example.com"
                value={to}
                onChange={(e) => setTo(e.target.value)}
                disabled={isSending}
              />
            </div>

            <Separator />

            {/* Subject */}
            <div className="space-y-2">
              <Label className="font-semibold">Subject:</Label>
              <div className="bg-slate-50 dark:bg-slate-900 rounded p-3 text-sm">
                {preview.subject}
              </div>
            </div>

            <Separator />

            {/* Body */}
            <div className="space-y-2">
              <Label className="font-semibold">Message:</Label>
              <div className="bg-slate-50 dark:bg-slate-900 rounded p-4 text-sm leading-relaxed whitespace-pre-wrap max-h-64 overflow-y-auto">
                {preview.body}
              </div>
            </div>

            {/* Invoice Details */}
            {preview.invoice_id && (
              <>
                <Separator />
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <Label className="text-xs font-semibold text-slate-500">Invoice ID</Label>
                    <p>{preview.invoice_id}</p>
                  </div>
                  {preview.credit_amount && (
                    <div>
                      <Label className="text-xs font-semibold text-slate-500">Credit Amount</Label>
                      <p>${preview.credit_amount.toLocaleString()}</p>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </ScrollArea>

        <DialogFooter className="mt-6">
          <Button
            variant="outline"
            onClick={onCancel}
            disabled={isSending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSendEmail}
            disabled={isSending || isLoading}
            className="gap-2"
          >
            {isSending ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Mail className="size-4" />
                Send Email
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
