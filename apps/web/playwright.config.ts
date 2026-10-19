import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  use: { baseURL: "http://127.0.0.1:3800", trace: "retain-on-failure" },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" },
    },
  ],
  webServer: [
    {
      command: "node tests/mock-api.mjs",
      url: "http://127.0.0.1:3801/health",
      reuseExistingServer: false,
    },
    {
      command: "pnpm start --port 3800",
      url: "http://127.0.0.1:3800/universities?year=2024",
      reuseExistingServer: false,
      timeout: 60000,
      env: {
        API_INTERNAL_URL: "http://127.0.0.1:3801",
        NEXT_TELEMETRY_DISABLED: "1",
      },
    },
  ],
});
