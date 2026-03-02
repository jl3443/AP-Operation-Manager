import type { ApiError } from "./types"

const BASE_URL = "/api/v1"

class ApiClientError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = "ApiClientError"
    this.status = status
    this.detail = detail
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = "An unexpected error occurred"
    try {
      const errorData: ApiError = await response.json()
      detail = errorData.detail || detail
    } catch {
      detail = response.statusText || detail
    }
    throw new ApiClientError(response.status, detail)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

function getHeaders(): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  }

  // Add auth token if available
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token")
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
  }

  return headers
}

export async function apiGet<T>(
  path: string,
  params?: Record<string, string | number | boolean | undefined>,
): Promise<T> {
  const url = new URL(`${BASE_URL}${path}`, window.location.origin)

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value))
      }
    })
  }

  const response = await fetch(url.toString(), {
    method: "GET",
    headers: getHeaders(),
  })

  return handleResponse<T>(response)
}

export async function apiPost<T>(
  path: string,
  body?: unknown,
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: getHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  })

  return handleResponse<T>(response)
}

export async function apiPatch<T>(
  path: string,
  body?: unknown,
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: "PATCH",
    headers: getHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  })

  return handleResponse<T>(response)
}

export async function apiDelete<T = void>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: "DELETE",
    headers: getHeaders(),
  })

  return handleResponse<T>(response)
}

export async function apiUpload<T>(
  path: string,
  formData: FormData,
): Promise<T> {
  const headers: HeadersInit = {}

  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token")
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: formData,
  })

  return handleResponse<T>(response)
}

export { ApiClientError }
