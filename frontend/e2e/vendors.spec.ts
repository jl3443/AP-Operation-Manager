import { test, expect } from "@playwright/test"

test.describe("Vendors", () => {
  test("lists vendors with seed data", async ({ page }) => {
    await page.goto("/vendors")
    await expect(page.getByRole("table")).toBeVisible()
    // Seed data creates vendors like Acme Corp, TechParts Ltd
    await expect(page.getByText("Acme Corp")).toBeVisible()
  })

  test("shows vendor status badges", async ({ page }) => {
    await page.goto("/vendors")
    await expect(page.getByText(/active/i).first()).toBeVisible()
  })

  test("has Add Vendor button", async ({ page }) => {
    await page.goto("/vendors")
    await expect(page.getByRole("button", { name: /add vendor/i })).toBeVisible()
  })

  test("opens Add Vendor dialog", async ({ page }) => {
    await page.goto("/vendors")
    await page.getByRole("button", { name: /add vendor/i }).click()
    await expect(page.getByText(/vendor name/i)).toBeVisible()
  })
})
