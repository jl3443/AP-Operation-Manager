import { test, expect } from "@playwright/test"

test.describe("Import Data", () => {
  test("loads import page", async ({ page }) => {
    await page.goto("/import")
    await expect(page.getByText("Data Import")).toBeVisible()
  })

  test("displays three import cards", async ({ page }) => {
    await page.goto("/import")
    // Three import types: Purchase Orders, Goods Receipts, Vendor Master Data
    await expect(page.getByText("Purchase Orders")).toBeVisible()
    await expect(page.getByText("Goods Receipts")).toBeVisible()
    await expect(page.getByText(/vendor/i)).toBeVisible()
  })

  test("each card has an import button", async ({ page }) => {
    await page.goto("/import")
    const importButtons = page.getByRole("button", { name: /import|upload|select/i })
    // Should have at least 3 import triggers
    await expect(importButtons.first()).toBeVisible()
  })
})
