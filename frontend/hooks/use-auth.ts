import { useQuery } from "@tanstack/react-query"
import { apiGet } from "@/lib/api"
import type { User } from "@/lib/types"

export function useCurrentUser() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => apiGet<User>("/auth/me"),
    enabled: typeof window !== "undefined" && !!localStorage.getItem("access_token"),
    retry: false,
  })
}
