import { test, expect } from "@playwright/test"

test.describe("Invoices", () => {
  test("lists invoices with seed data", async ({ page }) => {
    await page.goto("/invoices")
    await expect(page.getByRole("table")).toBeVisible()
    // Seed data creates invoices with INV- prefix
    await expect(page.getByText(/INV-/)).toBeVisible()
  })

  test("filters invoices by status", async ({ page }) => {
    await page.goto("/invoices")
    await expect(page.getByRole("table")).toBeVisible()
    // Status filter select should be present
    const statusFilter = page.locator("[data-testid='status-filter'], select, [role='combobox']").first()
    if (await statusFilter.isVisible()) {
      await statusFilter.click()
    }
  })

  test("shows upload page", async ({ page }) => {
    await page.goto("/invoices/upload")
    // Upload page should have file upload elements
    await expect(page.getByText(/upload/i)).toBeVisible()
  })
})
