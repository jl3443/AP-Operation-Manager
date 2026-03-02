import { test, expect } from "@playwright/test"

test.describe("Dashboard", () => {
  test("displays KPI cards with real data", async ({ page }) => {
    await page.goto("/dashboard")
    await expect(page.getByText("Total Invoices")).toBeVisible()
    await expect(page.getByText("Pending Approval")).toBeVisible()
    await expect(page.getByText("Open Exceptions")).toBeVisible()
    await expect(page.getByText("Match Rate")).toBeVisible()
  })

  test("displays charts", async ({ page }) => {
    await page.goto("/dashboard")
    await expect(page.getByText("Invoice Processing Funnel")).toBeVisible()
    await expect(page.getByText("Invoice Volume Trend")).toBeVisible()
    await expect(page.getByText("Top Vendors by Volume")).toBeVisible()
  })

  test("displays recent invoices table", async ({ page }) => {
    await page.goto("/dashboard")
    await expect(page.getByText("Recent Invoices")).toBeVisible()
    // Seed data has invoices starting with INV-
    await expect(page.getByText(/INV-/)).toBeVisible()
  })

  test("navigates to invoices via View All", async ({ page }) => {
    await page.goto("/dashboard")
    await page.getByRole("link", { name: "View All" }).click()
    await page.waitForURL("/invoices")
  })
})
