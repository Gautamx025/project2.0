import { test, expect } from "@playwright/test";
test("invalid input is rejected and resetting an in-flight upload discards its late response", async ({
  page,
}) => {
  await page.goto("/create");
  await page.getByTestId("photo-input").setInputFiles({
    name: "not-an-image.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("not an image"),
  });
  await expect(page.locator('main [role="alert"]')).toContainText(
    "Use JPG, PNG or WebP",
  );
  await page.getByRole("button", { name: "Dismiss" }).click();
  await page.route("**/api/jobs/sample", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 350));
    await route.continue();
  });
  const response = page.waitForResponse((result) =>
    result.url().endsWith("/api/jobs/sample"),
  );
  await page.getByRole("button", { name: "Develop this listing" }).click();
  await page.getByRole("button", { name: "Cancel & reset" }).click();
  const created = await (await response).json();
  await expect
    .poll(async () => {
      const job = await (
        await page.request.get("/api/jobs/" + created.id)
      ).json();
      return job.status;
    })
    .toBe("ready");
  await expect(
    page.getByRole("button", { name: "Develop this listing" }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Review and edit listing" }),
  ).toHaveCount(0);
});
test("a completed stage can be retried from the UI without reusing an approval", async ({
  page,
}) => {
  await page.goto("/create");
  await page.getByRole("button", { name: "Develop this listing" }).click();
  await expect(page.getByLabel("Product title", { exact: true })).toHaveValue(
    "Steel water bottle",
  );
  await page
    .getByTestId("stage-4")
    .getByRole("button", { name: "Retry stage" })
    .click();
  await expect(page.getByLabel("Product title", { exact: true })).toHaveValue(
    "Steel water bottle",
  );
  await expect(
    page.getByRole("checkbox", { name: /I reviewed the photo/ }),
  ).not.toBeChecked();
  await expect(page.getByTestId("stage-4")).toHaveClass(/completed/);
});
test("ledger network failure has an actionable recovery state", async ({
  page,
}) => {
  await page.route("**/api/jobs", (route) =>
    route.fulfill({
      status: 503,
      json: { detail: "The ledger is temporarily unavailable." },
    }),
  );
  await page.goto("/history");
  await expect(page.locator('main [role="alert"]')).toContainText(
    "temporarily unavailable",
  );
  await page.unroute("**/api/jobs");
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.locator('main [role="alert"]')).toHaveCount(0);
});
