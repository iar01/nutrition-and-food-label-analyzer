import { expect, test, type Page } from '@playwright/test';

const PRODUCT = {
  code: '3017620422003',
  name: 'Test Spread',
  brand: 'Acme',
  quantity: '400 g',
  ingredients: 'sugar, palm oil, hazelnuts, skimmed milk powder, emulsifier (E322)',
  nutriscore: 'e',
  nova_group: 4,
  categories: ['en:spreads'],
  allergens: ['en:milk'],
  traces: [],
  additives: ['en:e322'],
  nutrition_per_100g: { energy_kcal: 540, fat_g: 30, sat_fat_g: 10, carbs_g: 57, sugars_g: 56, protein_g: 6, salt_g: 0.1 },
  off_url: 'https://world.openfoodfacts.org/product/3017620422003',
};

const ANALYSIS = {
  thread_id: 'thread-0001',
  product: PRODUCT,
  summary: 'Contains milk, which is on your allergen list.',
  tips: [],
  verdicts: {
    diets: {
      vegan: { status: 'not_suitable', reasons: ['The product data marks it as not suitable.'], evidence_ids: [] },
      gluten_free: { status: 'unknown', reasons: ['The product data does not settle this.'], evidence_ids: [] },
    },
    allergens: { milk: { status: 'contains', reasons: ['Declared allergen: milk.'], evidence_ids: [] } },
    nutrition: {
      sugars_g: { value: 56, level: 'high' },
      salt_g: { value: 0.1, level: 'low' },
      sat_fat_g: { value: 10, level: 'high' },
      fat_g: { value: 30, level: 'high' },
    },
    goals: {},
    overall: 'not_suitable',
  },
  ingredients: { summary: 'Mostly sugar and palm oil.', notable: [] },
  additives: { notes: [{ e_number: 'E322', explanation: 'An emulsifier.', relevant_to_user: null, evidence_id: 'kb:e322' }], missing: [] },
  alternatives: [],
  evidence: [{ id: 'product:3017620422003', kind: 'product', title: 'Test Spread (Open Food Facts)', text: 'Test', source_url: PRODUCT.off_url }],
  answer_markdown: '# Test Spread',
};

function sse(event: string, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

async function mockChat(page: Page, body: string, status = 200) {
  await page.route('**/api/v1/chat', (route) =>
    route.fulfill({
      status,
      headers: { 'content-type': 'text/event-stream', 'x-request-id': 'req-test-0001' },
      body,
    }),
  );
}

async function setProfile(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem(
      'labellens.profile.v1',
      JSON.stringify({ diets: ['vegan', 'gluten_free'], allergens: ['milk'], goals: [] }),
    );
  });
}

test.beforeEach(async ({ page }) => {
  // The product photo is not part of these tests.
  await page.route('**/api/v1/products/*/image', (route) => route.fulfill({ status: 404, body: '' }));
});

test('barcode flow shows the result with clear verdicts', async ({ page }) => {
  await setProfile(page);
  await mockChat(
    page,
    sse('step', { node: 'router', label: 'Understanding your request' }) +
      sse('final', ANALYSIS) +
      sse('done', { thread_id: 'thread-0001', status: 'complete' }),
  );

  await page.goto('/');
  await page.getByLabel('Barcode number').fill('3017620422003');
  await page.getByRole('button', { name: 'Check' }).click();

  await expect(page).toHaveURL(/\/check\?barcode=3017620422003/);
  await expect(page.getByRole('heading', { name: 'Test Spread' })).toBeVisible();
  await expect(page.getByText('Not suitable for your profile')).toBeVisible();
  await expect(page.getByText('Contains', { exact: true })).toBeVisible();
  // Unknown must be visible and clearly worded, not hidden or shown as suitable.
  await expect(page.getByText('Unknown: check the pack').first()).toBeVisible();
});

test('a mistyped barcode is rejected before any request is made', async ({ page }) => {
  let called = false;
  await page.route('**/api/v1/chat', (route) => {
    called = true;
    return route.abort();
  });
  await page.goto('/');
  await page.getByLabel('Barcode number').fill('3017620422004');
  await page.getByRole('button', { name: 'Check' }).click();
  await expect(page.locator('#barcode-error')).toContainText('does not look like a valid barcode');
  expect(called).toBe(false);
});

test('text search asks which product, then continues', async ({ page }) => {
  await setProfile(page);
  let calls = 0;
  await page.route('**/api/v1/chat', (route) => {
    calls += 1;
    const body =
      calls === 1
        ? sse('step', { node: 'find_candidates', label: 'Searching products' }) +
          sse('choose_product', {
            thread_id: 'thread-0001',
            question: 'Which product did you mean?',
            candidates: [
              { code: '3017620422003', name: 'Test Spread', brands: 'Acme' },
              { code: '4000000000006', name: 'Other Spread', brands: 'Other' },
            ],
          }) +
          sse('done', { thread_id: 'thread-0001', status: 'waiting_for_choice' })
        : sse('final', ANALYSIS) + sse('done', { thread_id: 'thread-0001', status: 'complete' });
    return route.fulfill({ status: 200, headers: { 'content-type': 'text/event-stream' }, body });
  });

  await page.goto('/check?q=spread');
  await expect(page.getByRole('dialog')).toContainText('Which product did you mean?');
  await page.getByRole('button', { name: /Test Spread/ }).click();
  await expect(page.getByRole('heading', { name: 'Test Spread' })).toBeVisible();
  expect(calls).toBe(2);
});

test('a server error shows a clear message and a retry button', async ({ page }) => {
  await page.route('**/api/v1/chat', (route) =>
    route.fulfill({
      status: 502,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'upstream_unreachable', message: 'x', request_id: 'req-502' }),
    }),
  );
  await page.goto('/check?barcode=3017620422003');
  await expect(page.locator('[role="alert"]:not(#__next-route-announcer__)')).toContainText('not reachable right now');
  await expect(page.getByRole('button', { name: 'Try again' })).toBeVisible();
});

test('a denied camera explains what to do and manual entry still works', async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'mediaDevices', {
      value: { getUserMedia: () => Promise.reject(new DOMException('denied', 'NotAllowedError')) },
    });
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Start camera' }).click();
  await expect(page.locator('[role="alert"]:not(#__next-route-announcer__)')).toContainText('Camera access was denied');
  await expect(page.getByLabel('Barcode number')).toBeVisible();
});

test('the profile is saved in the browser', async ({ page }) => {
  await page.goto('/profile');
  await page.getByRole('checkbox', { name: 'Milk' }).click();
  await page.reload();
  await expect(page.getByRole('checkbox', { name: 'Milk' })).toBeChecked();
});

