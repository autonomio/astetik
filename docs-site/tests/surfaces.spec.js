const {test, expect} = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
const docsMap = require('../docs-map.json');
const productDocs = require('../product-docs.json');

function documentIn(section) {
  const document = docsMap.documents.find((candidate) => candidate.dest.startsWith(`${section}/`));
  if (!document) throw new Error(`route map lacks a representative ${section} document`);
  return document;
}

const roles = [
  {role: 'home', document: docsMap.documents.find((document) => document.slug === '/')},
  {role: 'category', slug: docsMap.sections[0].slug},
  {role: 'guide', document: documentIn('guides')},
  {role: 'reference', document: documentIn('reference')},
  {role: 'developer', document: documentIn('developer')},
  {role: 'package', document: documentIn('packages')},
];
const viewports = [
  {name: 'desktop', width: 1440, height: 900},
  {name: 'mobile', width: 390, height: 844},
];

for (const role of roles) {
  for (const viewport of viewports) {
    for (const theme of ['light', 'dark']) {
      test(`${role.role} / ${viewport.name} / ${theme}`, async ({page}, testInfo) => {
        const errors = [];
        page.on('pageerror', (error) => errors.push(error.message));
        page.on('console', (message) => {
          if (message.type() === 'error') errors.push(message.text());
        });
        await page.setViewportSize({width: viewport.width, height: viewport.height});
        const slug = role.document?.slug ?? role.slug;
        await page.goto(`${slug.replace(/^\//, '')}?docusaurus-theme=${theme}`);
        await expect(page.locator('main h1')).toBeVisible();
        await page.evaluate(() => document.fonts.ready);
        const surface = await page.evaluate(() => ({
          theme: document.documentElement.dataset.theme,
          font: getComputedStyle(document.body).fontFamily,
          localFontLoaded: [...document.fonts].some((font) => font.family.replaceAll("'", '') === 'Finlandica' && font.status === 'loaded'),
          paper: getComputedStyle(document.documentElement).getPropertyValue('--astetik-paper').trim().toUpperCase(),
          overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        }));
        expect(surface.theme).toBe(theme);
        expect(surface.font).toContain('Finlandica');
        expect(surface.localFontLoaded).toBe(true);
        expect(surface.paper).toBe(theme === 'light' ? '#F7F7F2' : '#252D33');
        expect(surface.overflow).toBeLessThanOrEqual(1);
        if (role.document) {
          await expect(page.getByRole('link', {name: 'Edit this page'})).toHaveAttribute(
            'href',
            `${productDocs.sourceRepoUrl}/edit/${productDocs.sourceBranch}/${role.document.source}`
          );
        }
        await page.screenshot({path: testInfo.outputPath('surface.png'), fullPage: true});
        const accessibility = await new AxeBuilder({page}).withTags(['wcag2a', 'wcag2aa']).analyze();
        expect(accessibility.violations).toEqual([]);
        expect(errors).toEqual([]);
      });
    }
  }
}
