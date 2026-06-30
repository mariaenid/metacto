import { expect, test } from "@playwright/test";

test.describe("Auth page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/auth");
  });

  test("renders login tab by default", async ({ page }) => {
    await expect(page.getByText("Sign In")).toBeVisible();
  });

  test("switching to register tab shows display name field", async ({ page }) => {
    await page.getByText("register").click();
    await expect(page.getByText("Display name")).toBeVisible();
  });

  test("shows error on empty login submit", async ({ page }) => {
    await page.getByText("Sign In").click();
    await expect(page.getByText("Email and password are required.")).toBeVisible();
  });

  test("shows error on short password during registration", async ({ page }) => {
    await page.getByText("register").click();
    await page.getByPlaceholder("you@example.com").fill("test@example.com");
    await page.getByPlaceholder("Your name").fill("Test User");
    await page.getByPlaceholder("••••••••").fill("short");
    await page.getByText("Create Account").click();
    await expect(page.getByText("Password must be at least 8 characters.")).toBeVisible();
  });

  test("back link navigates to the previous page", async ({ page }) => {
    // Navigate from home → auth so back() resolves.
    await page.goto("/");
    await page.goto("/auth");
    await page.getByText("← Back").click();
    await expect(page).not.toHaveURL("/auth");
  });
});

test.describe("Submit page auth guard", () => {
  test("anonymous user navigates to /auth when clicking submit on feed", async ({
    page,
  }) => {
    await page.goto("/");
    await page.getByText("+ Submit").click();
    // SubmitScreen shows the form; without auth, hitting submit should redirect.
    await page.getByText("Submit Request").click();
    await expect(page).toHaveURL("/auth");
  });
});
