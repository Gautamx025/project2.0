import { test, expect } from "@playwright/test";
import { capture } from "./capture";
test("editorial landing, projected claims, inline architecture and mobile composition", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "Good product.",
  );
  await expect(
    page.getByText("PROJECTED FIGURES / NOT MEASURED RESULTS", { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".how-steps>li")).toHaveCount(6);
  await expect(
    page.getByRole("heading", {
      name: "Faster, cheaper, better-looking catalogs without a studio or a copywriter.",
    }),
  ).toBeVisible();
  await capture(page, "landing.png");
  await page.setViewportSize({ width: 390, height: 844 });
  await capture(page, "landing-mobile.png");
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await page.goto("/under-the-hood");
  await expect(page.locator(".architecture-scroll>svg")).toBeVisible();
  await expect(page.locator(".tool-ledger>article")).toHaveCount(9);
  await expect(
    page.getByRole("heading", { name: "A path from one shop to many." }),
  ).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await capture(page, "architecture-mobile.png");
  expect(errors).toEqual([]);
});
