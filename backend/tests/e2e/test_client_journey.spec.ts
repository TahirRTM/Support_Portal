// Playwright E2E: client journey.
// Create Ticket -> Case Number -> Track -> OTP -> View -> Reply.
// Requires the full stack running (docker compose up) + Playwright installed.
import { test, expect } from '@playwright/test';

test('client can create and track a ticket', async ({ page }) => {
  await page.goto('/support/create');
  await page.getByLabel('Name').fill('Ada Lovelace');
  await page.getByLabel('Email').fill('ada@example.com');
  await page.getByLabel('Subject').fill('Cannot log in');
  await page.getByLabel('Description').fill('I am locked out of my account.');
  await page.getByRole('button', { name: /submit/i }).click();

  await expect(page.getByText('Support Request Received')).toBeVisible();
  const caseNumber = await page.getByTestId('case-number').innerText();
  expect(caseNumber).toMatch(/^SUP-\d{4}-[0-9A-Z]{10}$/);

  // Track: case + email -> OTP screen.
  await page.goto('/support/track');
  await page.getByLabel('Case Number').fill(caseNumber);
  await page.getByLabel('Email').fill('ada@example.com');
  await page.getByRole('button', { name: /request code/i }).click();
  await expect(page.getByText(/verification code/i)).toBeVisible();
});
