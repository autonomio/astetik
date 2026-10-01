const fs = require('node:fs');
const path = require('node:path');
const {test, expect} = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
const docsMap = require('../docs-map.json');
const productDocs = require('../product-docs.json');

const contractDocument = docsMap.documents.find(
  (document) => document.source === 'docs/Developer/Documentation-System.md'
);
const contractSource = fs.readFileSync(
  path.resolve(__dirname, '..', '..', contractDocument.source),
  'utf8'
);
const contractTitle = contractSource.match(/^# (.+)$/m)[1];
const contractRoute = contractDocument.slug.replace(/^\//, '');

test('desktop documentation surface matches the shared contract', async ({page}) => {
  await page.goto(`${contractRoute}?docusaurus-theme=light`);
  await expect(page.locator('h1')).toHaveText(contractTitle);
  await expect(page.locator('.navbar__link')).toHaveText([
    'Home',
    'Overview',
    'Guides',
    'Reference',
    'Developer',
    'Packages',
    'GitHub',
  ]);
  await expect(page.locator('a', {hasText: 'Edit this page'})).toHaveAttribute(
    'href',
    `${productDocs.sourceRepoUrl}/edit/${productDocs.sourceBranch}/${contractDocument.source}`
  );
  const geometry = await page.locator('.theme-doc-markdown').evaluate((element) => ({
    width: element.getBoundingClientRect().width,
    font: getComputedStyle(element).fontFamily,
    size: getComputedStyle(element).fontSize,
    navbar: document.querySelector('.navbar').getBoundingClientRect().height,
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  }));
  expect(geometry.width).toBeLessThanOrEqual(680);
  expect(geometry.font).toContain('Finlandica');
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.fonts.check('17px Finlandica'))).toBe(true);
  expect(geometry.size).toBe('17px');
  expect(geometry.navbar).toBeGreaterThanOrEqual(55);
  expect(geometry.navbar).toBeLessThanOrEqual(57);
  expect(geometry.overflow).toBeLessThanOrEqual(1);
  const accessibility = await new AxeBuilder({page}).withTags(['wcag2a', 'wcag2aa']).analyze();
  expect(accessibility.violations).toEqual([]);
});

test('search and mobile behavior remain functional', async ({page}) => {
  await page.goto('?docusaurus-theme=light');
  await page.locator('input[aria-label="Search"]').fill(contractTitle);
  await expect(page.locator('[role="listbox"]')).toBeVisible();
  await expect(page.locator('[role="listbox"]')).toContainText(contractTitle);

  await page.setViewportSize({width: 390, height: 844});
  await page.goto(`${contractRoute}?docusaurus-theme=dark`);
  await expect(page.locator('.navbar__toggle')).toBeVisible();
  await expect(page.locator('.theme-doc-sidebar-container')).toBeHidden();
  const mobile = await page.evaluate(() => ({
    theme: document.documentElement.dataset.theme,
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  }));
  expect(mobile.theme).toBe('dark');
  expect(mobile.overflow).toBeLessThanOrEqual(1);
  await page.locator('.navbar__toggle').click();
  await expect(page.locator('.navbar-sidebar')).toBeVisible();
  const drawerAccessibility = await new AxeBuilder({page}).withTags(['wcag2a', 'wcag2aa']).analyze();
  expect(drawerAccessibility.violations).toEqual([]);
  await page.getByRole('button', {name: 'Close navigation bar', exact: true}).click();
  await page.getByRole('button', {name: 'On this page', exact: true}).click();
  await expect(page.locator('[class*="tocCollapsibleContent"] ul')).toBeVisible();
  const table = page.locator('.theme-doc-markdown table[tabindex="0"]').first();
  await expect(table).toBeVisible();
  await table.focus();
  await expect(table).toBeFocused();
  const beforeScroll = await table.evaluate((element) => element.scrollLeft);
  await page.keyboard.press('ArrowRight');
  await expect.poll(() => table.evaluate((element) => element.scrollLeft)).toBeGreaterThan(beforeScroll);
  const accessibility = await new AxeBuilder({page}).withTags(['wcag2a', 'wcag2aa']).analyze();
  expect(accessibility.violations).toEqual([]);
});

test('keyboard access reaches content and local search results', async ({page}) => {
  await page.goto('?docusaurus-theme=light');
  await expect(page.getByRole('button', {name: /Switch between dark and light mode/}).first()).toBeEnabled();
  await page.keyboard.press('Tab');
  const skip = page.getByRole('link', {name: 'Skip to main content'});
  await expect(skip).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('main')).toBeFocused();
  const search = page.locator('input[aria-label="Search"]');
  await search.focus();
  await page.keyboard.type(contractTitle);
  await expect(page.locator('[role="listbox"]')).toBeVisible();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await expect(page.locator('h1')).toHaveText(contractTitle);
});


test('sidebar and light/dark/system controls remain usable', async ({page}) => {
  await page.goto(`${contractRoute}?docusaurus-theme=light`);
  expect(await page.locator('.menu__list-item--collapsed').count()).toBeGreaterThanOrEqual(4);
  await page.getByRole('button', {name: 'Collapse sidebar', exact: true}).click();
  await page.getByRole('button', {name: 'Expand sidebar', exact: true}).click();
  const theme = page.getByRole('button', {name: /Switch between dark and light mode/}).first();
  await expect(theme).toHaveAttribute('title', 'light mode');
  await theme.click();
  await expect(theme).toHaveAttribute('title', 'dark mode');
  await theme.click();
  await expect(theme).toHaveAttribute('title', 'system mode');
});
