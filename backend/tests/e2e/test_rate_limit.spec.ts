// Playwright E2E: rate limit. 3 creates succeed, 4th returns 429.
import { test, expect, request } from '@playwright/test';

test('fourth ticket creation within window is rate limited', async ({ playwright }) => {
  const api = await request.newContext({ baseURL: process.env.API_URL });
  const body = {
    name: 'Load Test', email: 'load@example.com', subject: 'hi there',
    description: 'testing rate limits', captcha_token: 'dev-bypass',
  };
  const codes: number[] = [];
  for (let i = 0; i < 4; i++) {
    const r = await api.post('/api/v1/support/tickets', { data: body });
    codes.push(r.status());
  }
  expect(codes.slice(0, 3)).toEqual([201, 201, 201]);
  expect(codes[3]).toBe(429);
});
