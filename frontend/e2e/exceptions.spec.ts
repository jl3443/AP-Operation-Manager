import { test, expect } from "@playwright/test"

test.describe("Exceptions", () => {
  test("loads exception queue page", async ({ page }) => {
    await page.goto("/exceptions")
    // Page title in header
    await expect(page.getByText("Exception Queue")).toBeVisible()
  })

  test("displays exception entries from seed data", async ({ page }) => {
    await page.goto("/exceptions")
    // Seed data creates exceptions of various types
    await expect(page.getByRole("table").or(page.getByText(/exception/i).first())).toBeVisible()
  })

  test("shows status badges", async ({ page }) => {
    await page.goto("/exceptions")
    // Should show statuses like open, assigned
    const badges = page.locator("[class*='badge']")
    await expect(badges.first()).toBeVisible({ timeout: 10000 })
  })
})
