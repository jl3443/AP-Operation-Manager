import { useMutation } from "@tanstack/react-query"
import { apiUpload } from "@/lib/api"

interface ImportResult {
  message: string
  created: number
  errors: number
  error_details?: string[]
}

function buildFormData(file: File): FormData {
  const fd = new FormData()
  fd.append("file", file)
  return fd
}

export function useImportPurchaseOrders() {
  return useMutation({
    mutationFn: (file: File) =>
      apiUpload<ImportResult>("/import/purchase-orders", buildFormData(file)),
  })
}

export function useImportGoodsReceipts() {
  return useMutation({
    mutationFn: (file: File) =>
      apiUpload<ImportResult>("/import/goods-receipts", buildFormData(file)),
  })
}

export function useImportVendors() {
  return useMutation({
    mutationFn: (file: File) =>
      apiUpload<ImportResult>("/import/vendors", buildFormData(file)),
  })
}
