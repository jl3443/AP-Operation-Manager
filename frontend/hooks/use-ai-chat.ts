"use client"

import { useMutation } from "@tanstack/react-query"
import { apiPost } from "@/lib/api"
import type { AIChatResponse } from "@/lib/types"

interface ChatPayload {
  message: string
  conversation_id?: string
}

export function useAIChat() {
  return useMutation({
    mutationFn: (payload: ChatPayload) =>
      apiPost<AIChatResponse>("/ai/chat", payload),
  })
}
