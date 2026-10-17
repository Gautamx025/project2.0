import type { Page } from "@playwright/test";
import { mkdir, rename, unlink, writeFile } from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";

// Windows thumbnail/indexing services can briefly hold the previous image open.
// Capture once; retry only the atomic artifact replacement, never the app action.
export async function capture(page: Page, name: string) {
  const directory = path.join(process.cwd(), "docs/screenshots");
  await mkdir(directory, { recursive: true });
  const target = path.join(directory, name),
    temporary = target + "." + randomUUID() + ".tmp";
  const bytes = await page.screenshot({ fullPage: true });
  await writeFile(temporary, bytes);
  try {
    for (let attempt = 0; ; attempt++) {
      try {
        await rename(temporary, target);
        return;
      } catch (error) {
        if (attempt >= 7) throw error;
        await new Promise((resolve) =>
          setTimeout(resolve, 100 * (attempt + 1)),
        );
      }
    }
  } finally {
    await unlink(temporary).catch(() => {});
  }
}
