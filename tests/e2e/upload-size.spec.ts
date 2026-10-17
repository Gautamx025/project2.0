import { test, expect } from "@playwright/test";

test("large camera-style photo is reduced below the cloud request limit", async ({ page }) => {
  await page.goto("/create");
  const encoded = await page.evaluate(() => {
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = 1600;
    const context = canvas.getContext("2d")!;
    const pixels = context.createImageData(1600, 1600);
    let seed = 2417;
    for (let index = 0; index < pixels.data.length; index += 4) {
      for (let channel = 0; channel < 3; channel++) {
        seed ^= seed << 13;
        seed ^= seed >>> 17;
        seed ^= seed << 5;
        pixels.data[index + channel] = seed & 255;
      }
      pixels.data[index + 3] = 255;
    }
    context.putImageData(pixels, 0, 0);
    return canvas.toDataURL("image/png").split(",")[1];
  });
  const original = Buffer.from(encoded, "base64");
  expect(original.length).toBeGreaterThan(4_500_000);
  expect(original.length).toBeLessThan(10 * 1024 * 1024);
  // Independent control: the exact original fails the enforced transport limit.
  const oversized = await page.request.post("/api/jobs", { multipart: {
    files: { name:"camera-photo.png", mimeType:"image/png", buffer:original },
  } });
  expect(oversized.status()).toBe(413);
  await page.getByTestId("photo-input").setInputFiles({ name: "camera-photo.png", mimeType: "image/png", buffer: original });
  const upload = page.waitForResponse((response) => response.request().method() === "POST" && response.url().endsWith("/api/jobs"));
  await page.getByRole("button", { name: "Develop this listing" }).click();
  expect((await upload).status()).toBe(202);
  await expect(page.getByRole("region", { name: "Review and edit listing" })).toBeVisible();
  for (let index = 0; index < 6; index++) await expect(page.getByTestId("stage-"+index)).toHaveClass(/completed/);
});
