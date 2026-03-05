import { useState } from "react";
import { apiPostDirect } from "@/lib/api";

interface EmailPreview {
  to: string;
  subject: string;
  body: string;
  invoice_id: string;
  credit_amount?: number;
  action_id?: string;
  preview: boolean;
}

interface EmailParams {
  to_email?: string;
  credit_amount?: number;
  action_id?: string;
}

/**
 * Hook for handling email preview and send workflow.
 * Manages the flow: preview fetch → dialog display → confirmation send
 */
export function useEmail(invoiceId: string) {
  const [preview, setPreview] = useState<EmailPreview | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [isLoadingConfirm, setIsLoadingConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch email preview for a credit approval email
   */
  const fetchCreditApprovalPreview = async (params: EmailParams = {}) => {
    setIsLoadingPreview(true);
    setError(null);
    try {
      const response = await apiPostDirect(
        `/invoices/${invoiceId}/approve-credit-preview`,
        params
      );
      setPreview(response as EmailPreview);
      return response as EmailPreview;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load email preview";
      setError(message);
      throw err;
    } finally {
      setIsLoadingPreview(false);
    }
  };

  /**
   * Send the credit approval email after user confirmation
   */
  const sendCreditApprovalEmail = async (
    to: string,
    subject: string,
    body: string,
    actionId?: string,
    creditAmount?: number
  ) => {
    setIsLoadingConfirm(true);
    setError(null);
    try {
      const response = await apiPostDirect(
        `/invoices/${invoiceId}/approve-credit-confirm`,
        {
          to,
          subject,
          body,
          action_id: actionId,
          credit_amount: creditAmount,
        }
      );
      setPreview(null);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to send email";
      setError(message);
      throw err;
    } finally {
      setIsLoadingConfirm(false);
    }
  };

  /**
   * Fetch PO request email preview
   */
  const fetchPORequestPreview = async (params: EmailParams = {}) => {
    setIsLoadingPreview(true);
    setError(null);
    try {
      const response = await apiPostDirect(
        `/invoices/${invoiceId}/request-po-preview`,
        params
      );
      setPreview(response as EmailPreview);
      return response as EmailPreview;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load email preview";
      setError(message);
      throw err;
    } finally {
      setIsLoadingPreview(false);
    }
  };

  /**
   * Send the PO request email
   */
  const sendPORequestEmail = async (
    to: string,
    subject: string,
    body: string,
    actionId?: string
  ) => {
    setIsLoadingConfirm(true);
    setError(null);
    try {
      const response = await apiPostDirect(
        `/invoices/${invoiceId}/request-po-confirm`,
        {
          to,
          subject,
          body,
          action_id: actionId,
        }
      );
      setPreview(null);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to send email";
      setError(message);
      throw err;
    } finally {
      setIsLoadingConfirm(false);
    }
  };

  const closePreview = () => {
    setPreview(null);
    setError(null);
  };

  return {
    preview,
    isLoadingPreview,
    isLoadingConfirm,
    error,
    fetchCreditApprovalPreview,
    sendCreditApprovalEmail,
    fetchPORequestPreview,
    sendPORequestEmail,
    closePreview,
  };
}
