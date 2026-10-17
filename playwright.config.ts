import { defineConfig } from "@playwright/test";
import path from "node:path";
const python =
  process.platform === "win32"
    ? ".venv\\Scripts\\python.exe"
    : ".venv/bin/python";
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60000,
  expect: { timeout: 15000 },
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    reducedMotion: "reduce",
  },
  webServer: [
    {
      command: `${python} -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`,
      url: "http://127.0.0.1:8000/api/health",
      reuseExistingServer: process.env.PLAYWRIGHT_REUSE_SERVER === "true",
      timeout: 60000,
      env: {
        DEMO_MODE: "true",
        REDIS_URL: "",
        DATA_DIR: path.join(process.cwd(), "data/e2e"),
        SETTINGS_ENV_FILE: path.join(process.cwd(), "data/e2e-config/.env"),
      },
    },
    {
      command:
        process.env.PLAYWRIGHT_PRODUCTION === "true"
          ? "npm start"
          : "npm run dev --workspace frontend",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: process.env.PLAYWRIGHT_REUSE_SERVER === "true",
      timeout: 120000,
    },
  ],
});
