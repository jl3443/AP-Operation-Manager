"use client"

import * as React from "react"
import { usePathname, useRouter } from "next/navigation"
import { Bell, Search, Moon, Sun } from "lucide-react"
import { AIAssistantPanel } from "@/components/ai-assistant-panel"
import { useTheme } from "next-themes"
import { useQueryClient } from "@tanstack/react-query"

import { useCurrentUser } from "@/hooks/use-auth"
import { SidebarNav } from "@/components/sidebar-nav"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"

const pageTitles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/analytics": "Analytics",
  "/invoices": "Invoices",
  "/exceptions": "Exception Queue",
  "/approvals": "Approval Center",
  "/vendors": "Vendor Management",
  "/import": "Data Import",
  "/audit": "Audit Trail",
  "/compliance": "Compliance & Insights",
  "/settings": "Settings",
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const router = useRouter()
  const queryClient = useQueryClient()
  const { theme, setTheme } = useTheme()
  const { data: user, isError: userError } = useCurrentUser()

  // Redirect to login if no token
  React.useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      router.push("/login")
    }
  }, [router])

  // Redirect on auth error (expired/invalid token)
  React.useEffect(() => {
    if (userError) {
      localStorage.removeItem("access_token")
      router.push("/login")
    }
  }, [userError, router])

  const userInitials = user?.name
    ? user.name.split(" ").map((n) => n[0]).join("").toUpperCase()
    : "??"
  const userDisplayName = user?.name
    ? user.name.split(" ").map((n, i) => (i === 0 ? n : n[0] + ".")).join(" ")
    : "User"

  function handleSignOut() {
    localStorage.removeItem("access_token")
    queryClient.clear()
    router.push("/login")
  }

  // Find the matching page title
  const pageTitle = Object.entries(pageTitles).find(([path]) =>
    pathname.startsWith(path),
  )?.[1] || "Dashboard"

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <SidebarNav />

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header Bar */}
        <header className="flex items-center justify-between h-14 border-b bg-card px-4 gap-4 shrink-0">
          <h2 className="text-lg font-semibold shrink-0">{pageTitle}</h2>

          {/* Search Bar */}
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
              <Input
                placeholder="Search invoices, vendors, POs..."
                className="pl-9 h-8 bg-secondary/50"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              <Sun className="size-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute size-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              <span className="sr-only">Toggle theme</span>
            </Button>

            {/* AI Assistant */}
            <AIAssistantPanel />

            {/* Notifications */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon-sm" className="relative">
                  <Bell className="size-4" />
                  <span className="absolute -top-0.5 -right-0.5 flex size-4 items-center justify-center rounded-full bg-destructive text-[10px] font-bold text-destructive-foreground">
                    3
                  </span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-80">
                <DropdownMenuLabel>Notifications</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="flex flex-col items-start gap-1 py-2">
                  <span className="text-sm font-medium">
                    Invoice #INV-2024-0892 needs approval
                  </span>
                  <span className="text-xs text-muted-foreground">
                    2 minutes ago
                  </span>
                </DropdownMenuItem>
                <DropdownMenuItem className="flex flex-col items-start gap-1 py-2">
                  <span className="text-sm font-medium">
                    Price mismatch on PO-45231
                  </span>
                  <span className="text-xs text-muted-foreground">
                    15 minutes ago
                  </span>
                </DropdownMenuItem>
                <DropdownMenuItem className="flex flex-col items-start gap-1 py-2">
                  <span className="text-sm font-medium">
                    Batch import completed: 45 POs
                  </span>
                  <span className="text-xs text-muted-foreground">
                    1 hour ago
                  </span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="gap-2 px-2 h-8">
                  <Avatar className="size-6">
                    <AvatarFallback className="text-xs bg-primary text-primary-foreground">
                      {userInitials}
                    </AvatarFallback>
                  </Avatar>
                  <span className="text-sm font-medium hidden sm:inline">
                    {userDisplayName}
                  </span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuLabel className="flex flex-col">
                  <span>{user?.name ?? "User"}</span>
                  <span className="text-xs text-muted-foreground font-normal">
                    {user?.email ?? ""}
                  </span>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>Profile</DropdownMenuItem>
                <DropdownMenuItem>Preferences</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-destructive" onClick={handleSignOut}>
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Main scrollable content */}
        <ScrollArea className="flex-1 overflow-hidden">
          <main className="p-6">{children}</main>
        </ScrollArea>
      </div>
    </div>
  )
}
