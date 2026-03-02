import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost, apiPatch, apiDelete } from "@/lib/api"
import type { Vendor, PaginatedResponse } from "@/lib/types"

interface VendorListParams {
  page?: number
  page_size?: number
  search?: string
  status?: string
  risk_level?: string
}

export function useVendors(params: VendorListParams = {}) {
  return useQuery({
    queryKey: ["vendors", "list", params],
    queryFn: () =>
      apiGet<PaginatedResponse<Vendor>>("/vendors", {
        page: params.page ?? 1,
        page_size: params.page_size ?? 100,
        search: params.search,
        status: params.status,
        risk_level: params.risk_level,
      }),
  })
}

export function useVendor(id: string) {
  return useQuery({
    queryKey: ["vendors", "detail", id],
    queryFn: () => apiGet<Vendor>(`/vendors/${id}`),
    enabled: !!id,
  })
}

interface VendorCreatePayload {
  vendor_code: string
  name: string
  city?: string
  state?: string
  country?: string
  payment_terms_code?: string
  status?: string
  risk_level?: string
}

export function useCreateVendor() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: VendorCreatePayload) =>
      apiPost<Vendor>("/vendors", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vendors"] })
    },
  })
}

export function useUpdateVendor() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string } & Partial<VendorCreatePayload>) =>
      apiPatch<Vendor>(`/vendors/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vendors"] })
    },
  })
}

export function useDeleteVendor() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/vendors/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vendors"] })
    },
  })
}
