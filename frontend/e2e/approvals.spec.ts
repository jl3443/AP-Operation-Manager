import { test, expect } from "@playwright/test"

test.describe("Approvals", () => {
  test("loads approval center page", async ({ page }) => {
    await page.goto("/approvals")
    await expect(page.getByText("Approval Center")).toBeVisible()
  })

  test("displays approval queue content", async ({ page }) => {
    await page.goto("/approvals")
    // Admin user may or may not have pending approvals
    // Just verify the page structure loads
    await expect(
      page.getByText(/pending/i).or(page.getByText(/no.*approval/i)).first()
    ).toBeVisible({ timeout: 10000 })
  })
})
