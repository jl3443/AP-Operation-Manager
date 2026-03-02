import { test, expect } from "@playwright/test"

test.describe("Audit Trail", () => {
  test("loads audit trail page", async ({ page }) => {
    await page.goto("/audit")
    await expect(page.getByText("Audit Trail")).toBeVisible()
  })

  test("displays audit log entries", async ({ page }) => {
    await page.goto("/audit")
    // Seed data creates 18 audit log entries
    await expect(page.getByRole("table")).toBeVisible()
  })

  test("has pagination controls", async ({ page }) => {
    await page.goto("/audit")
    // Pagination buttons
    await expect(page.getByRole("button", { name: /next/i }).or(
      page.getByText(/page/i)
    )).toBeVisible({ timeout: 10000 })
  })

  test("has filter controls", async ({ page }) => {
    await page.goto("/audit")
    // Should have filter inputs/selects
    await expect(page.getByPlaceholder(/search/i).or(
      page.locator("select, [role='combobox']").first()
    )).toBeVisible({ timeout: 10000 })
  })
})
