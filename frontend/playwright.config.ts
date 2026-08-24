import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "../backend/tests/e2e",
  timeout: 30_000,
  use: { baseURL: process.env.APP_URL ?? "http://localhost:3000" },
});
