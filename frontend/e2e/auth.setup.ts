import { test as setup, expect } from "@playwright/test"
import path from "path"

const authFile = path.join(__dirname, ".auth", "user.json")

setup("authenticate", async ({ page }) => {
  await page.goto("/login")
  await page.getByLabel("Email").fill("admin@apops.dev")
  await page.getByLabel("Password").fill("admin123")
  await page.getByRole("button", { name: "Sign In" }).click()

  // Wait for redirect to dashboard and data to load
  await page.waitForURL("/dashboard")
  await expect(page.getByText("Total Invoices")).toBeVisible({ timeout: 15000 })

  // Save storage state (includes localStorage with access_token)
  await page.context().storageState({ path: authFile })
})
