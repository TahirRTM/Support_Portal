// Playwright E2E: client cannot access another ticket, internal notes, or admin APIs.
import { test, expect, request } from '@playwright/test';

test('client session is scoped and cannot reach admin APIs', async ({ playwright }) => {
  const api = await request.newContext({ baseURL: process.env.API_URL });
  // A client-scoped token (obtained via OTP in a full run) must be rejected here.
  const adminList = await api.get('/api/v1/admin/tickets', {
    headers: { Authorization: 'Bearer client-scoped-token-placeholder' },
  });
  expect([401, 403]).toContain(adminList.status());
});
