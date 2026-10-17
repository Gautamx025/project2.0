import { test, expect } from "@playwright/test";
import path from "node:path";
import { capture } from "./capture";

test("upload → six measured stages → review/edit → explicitly approved demo draft", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/create");
  await page
    .getByTestId("photo-input")
    .setInputFiles(
      path.join(process.cwd(), "frontend/public/samples/bottle.jpg"),
    );
  await expect(page.getByAltText("Selected product photo 1")).toBeVisible();
  const created = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/jobs") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Develop this listing" }).click();
  await expect(page.getByRole("timer")).toBeVisible();
  await capture(page, "processing.png");
  const job = await (await created).json();
  await expect(
    page.getByRole("region", { name: "Review and edit listing" }),
  ).toBeVisible();
  for (let index = 0; index < 6; index++)
    await expect(page.getByTestId("stage-" + index)).toHaveClass(/completed/);
  expect((await page.request.get("/api/jobs/" + job.id)).status()).toBe(200);
  const slider = page.getByRole("slider", {
    name: "Before and after comparison",
  });
  await slider.focus();
  await slider.press("ArrowRight");
  await expect(slider).toHaveValue("51");
  await page
    .getByLabel("Product title", { exact: true })
    .fill("Steel bottle — reviewed by the merchant");
  await page.getByLabel("Your final price").fill("875.50");
  await expect(
    page.getByRole("button", { name: "Approve & create store draft" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Save reviewed draft" }).click();
  await expect(
    page.getByRole("button", { name: "Save reviewed draft" }),
  ).toBeDisabled();
  await page.getByText("Inspect store JSON payload").click();
  await expect(page.getByTestId("store-payload")).toContainText(
    "Steel bottle — reviewed by the merchant",
  );
  await expect(page.getByTestId("store-payload")).toContainText("875.50");
  await expect(
    page.locator(".product-preview").getByText("₹875.50", { exact: true }),
  ).toBeVisible();
  await capture(page, "review.png");
  await page.getByRole("checkbox", { name: /I reviewed the photo/ }).check();
  await page
    .getByRole("button", { name: "Approve & create store draft" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Filed in your local ledger." }),
  ).toBeVisible();
  const persisted = await (
    await page.request.get("/api/jobs/" + job.id)
  ).json();
  expect(persisted.result.copy.title).toBe(
    "Steel bottle — reviewed by the merchant",
  );
  expect(persisted.result.final_price).toBe(875.5);
  expect(persisted.store_result.demo).toBe(true);
  expect(persisted.store_result.status).toBe("draft");
  expect(errors).toEqual([]);
});

test("mobile upload layout and multilingual review remain usable at 390px", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/create");
  await capture(page, "mobile.png");
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await page.getByRole("button", { name: "Develop this listing" }).click();
  await expect(page.getByLabel("Product title", { exact: true })).toHaveValue(
    "Steel water bottle",
  );
  await page
    .getByLabel("Product title", { exact: true })
    .fill("My bilingual bottle");
  await page.getByRole("button", { name: "हिन्दी", exact: true }).click();
  await expect(page.getByLabel("Product title", { exact: true })).toHaveValue(
    "स्टील की पानी की बोतल",
  );
  await page
    .getByLabel("Product title", { exact: true })
    .fill("मेरी पानी की बोतल");
  await page.getByRole("button", { name: "मराठी", exact: true }).click();
  await expect(page.getByLabel("Product title", { exact: true })).toHaveValue(
    "स्टीलची पाण्याची बाटली",
  );
  await page.getByRole("button", { name: "Save reviewed draft" }).click();
  await expect(
    page.getByRole("button", { name: "Save reviewed draft" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "English", exact: true }).click();
  await expect(page.getByLabel("Product title", { exact: true })).toHaveValue(
    "My bilingual bottle",
  );
  await page.getByRole("button", { name: "हिन्दी", exact: true }).click();
  await expect(page.getByLabel("Product title", { exact: true })).toHaveValue(
    "मेरी पानी की बोतल",
  );
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
});
