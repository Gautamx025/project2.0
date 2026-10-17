import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
test("WCAG AA automated checks cover the landing, studio, settings and supporting desks", async ({
  page,
}) => {
  for (const route of [
    "/",
    "/create",
    "/settings",
    "/bulk",
    "/history",
    "/impact",
    "/under-the-hood",
  ]) {
    await page.goto(route);
    await expect(page.locator(".loading-state")).toHaveCount(0);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    const report = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(report.violations, route + " accessibility violations").toEqual([]);
  }
  await page.goto("/create");
  await page.getByRole("button", { name: "Develop this listing" }).click();
  await expect(
    page.getByRole("region", { name: "Review and edit listing" }),
  ).toBeVisible();
  const review = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(review.violations, "Review accessibility violations").toEqual([]);
});
test("sample pipeline needs no third-party network at runtime", async ({
  page,
}) => {
  const blocked: string[] = [];
  await page.route("**/*", (route) => {
    const hostname = new URL(route.request().url()).hostname;
    if (["127.0.0.1", "localhost"].includes(hostname)) return route.continue();
    blocked.push(route.request().url());
    return route.abort();
  });
  await page.goto("/create");
  await page
    .getByRole("button", { name: /Digital watch.*ACCESSORIES/ })
    .click();
  await page.getByRole("button", { name: "Develop this listing" }).click();
  await expect(page.getByLabel("Product title", { exact: true })).toHaveValue(
    "Everyday digital watch",
  );
  expect(blocked).toEqual([]);
});
