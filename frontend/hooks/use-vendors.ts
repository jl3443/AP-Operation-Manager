import { useQuery } from "@tanstack/react-query"
import { apiGet } from "@/lib/api"
import type { Vendor, PaginatedResponse } from "@/lib/types"

interface VendorListParams {
  page?: number
  page_size?: number
  search?: string
  status?: string
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
