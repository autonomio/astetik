const fs = require('node:fs');
const path = require('node:path');
const {test, expect} = require('@playwright/test');

const html = fs.readFileSync(path.resolve(__dirname, '../../scripts/studio.html'), 'utf8');
const metadata = {
  version: 'test', source: 'import.csv', note: '', rows: 2, key: [], units: {}, descriptions: {},
  numeric: ['measurement', 'time'], groups: {group: ['shared', 'first'], other_group: ['shared', 'second']},
  palette: ['#123456', '#234567', '#345678'], legend_locations: ['best', 'outside top'],
  defaults: {hist: {}, line: {}, regs: {}, bar: {}, box: {}, violin: {}},
  manifest: {
    colors: {primary: '#123456', ink: '#111111', muted: '#555555', line: '#CCCCCC'},
    paper: {aspect: 1.5, dpi: 300, min_fontsize: 7},
    typography: {fontsize: 9, labelsize: 9, titlesize: 10, ticksize: 8, legendsize: 8},
    axes: {linewidth: 0.5, grid: false, spines: ['left', 'bottom'], tick_direction: 'out', tick_length: 3},
  },
};

test.beforeEach(async ({page}) => {
  await page.route('**/studio', (route) => route.fulfill({contentType: 'text/html', body: html}));
  await page.route('**/api/meta', (route) => route.fulfill({json: metadata}));
  await page.route('**/api/render', (route) => route.fulfill({json: {
    svg: '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>',
    size_mm: [89, 61], checks: [], observations: {used: 2}, bins: 1, milliseconds: 1,
  }}));
  await page.goto('/studio');
  await expect(page.locator('#figure')).toHaveAttribute('src', /^blob:/);
});

for (const type of ['Line', 'Bar']) {
  test(`${type} settles the interval before drawing its selector`, async ({page}) => {
    await page.getByRole('button', {name: type, exact: true}).click();
    await page.locator('[data-key$="/estimator"]').selectOption('median');
    await expect(page.locator('[data-key$="/errorbar"]')).toHaveValue('iqr');
    expect((await page.evaluate(() => build())).spec.options.errorbar).toBe('iqr');
    await page.locator('[data-key$="/estimator"]').selectOption('mean');
    await expect(page.locator('[data-key$="/errorbar"]')).toHaveValue('ci');
  });
}

test('grid hue columns share one colour control and manifest binding per label', async ({page}) => {
  await page.evaluate(() => {
    state.type = 'grid';
    state.grid.panels = [{type: 'hist', variable: ''}, {type: 'line', variable: ''}];
    state.types.hist.hue = 'group';
    state.types.line.hue = 'other_group';
    draw();
  });
  const row = page.locator('.row').filter({has: page.locator('label', {hasText: /^shared$/})});
  await expect(row).toHaveCount(1);
  await row.locator('input').fill('#abcdef');
  const call = await page.evaluate(() => build());
  expect(call.spec.panels.map((panel) => panel.hue)).toEqual(['group', 'other_group']);
  expect(call.manifest.categories).toEqual({shared: '#ABCDEF', first: '#234567', second: '#345678'});
});

test('imported units are editable, included only when used, and retained in saved state', async ({page}) => {
  await page.locator('[data-key="Units/measurement"]').fill('mg');
  await page.locator('[data-key="Units/time"]').fill('s');
  const call = await page.evaluate(() => build());
  expect(call.spec.paper).toBe('single');
  expect(call.spec.units).toEqual({measurement: 'mg'});
  await page.evaluate(() => { state = restore(JSON.parse(JSON.stringify(state))); draw(); });
  await expect(page.locator('[data-key="Units/time"]')).toHaveValue('s');
  await page.locator('[data-key="Units/measurement"]').fill('');
  expect((await page.evaluate(() => build())).spec.units).toBeUndefined();
});

test('SVG preview replacements and consumed downloads release their object URLs', async ({page}) => {
  const previous = await page.locator('#figure').getAttribute('src');
  await page.evaluate(() => render());
  const current = await page.locator('#figure').getAttribute('src');
  expect(current).not.toBe(previous);
  expect(await page.evaluate(async (url) => fetch(url).then(() => false, () => true), previous)).toBe(true);
  expect(await page.evaluate(async (url) => (await fetch(url)).ok, current)).toBe(true);
  await page.evaluate(() => {
    const revoke = URL.revokeObjectURL;
    window.revoked = [];
    URL.revokeObjectURL = (url) => { window.revoked.push(url); revoke.call(URL, url); };
  });
  const pending = page.waitForEvent('download');
  await page.getByRole('button', {name: 'SVG', exact: true}).click();
  const download = await pending;
  expect(await download.failure()).toBeNull();
  const content = [];
  for await (const chunk of await download.createReadStream()) content.push(chunk);
  expect(Buffer.concat(content).toString()).toContain('<svg');
  await expect.poll(() => page.evaluate(() => window.revoked)).toContain(download.url());
  expect(await page.evaluate(async (url) => fetch(url).then(() => false, () => true), download.url())).toBe(true);
});

test('prototype-named categories accept defaults and custom colours', async ({page}) => {
  await page.evaluate(() => {
    meta.groups.group = ['constructor', '__proto__'];
    state.types.hist.hue = 'group';
    draw();
  });
  let categories = JSON.parse(await page.evaluate(() => JSON.stringify(build().manifest.categories)));
  expect(categories).toEqual({constructor: '#123456', ['__proto__']: '#234567'});
  const row = page.locator('.row').filter({has: page.locator('label', {hasText: /^__proto__$/})});
  await row.locator('input').fill('#abcdef');
  categories = JSON.parse(await page.evaluate(() => JSON.stringify(build().manifest.categories)));
  expect(categories).toEqual({constructor: '#123456', ['__proto__']: '#ABCDEF'});
});

test('legacy saved links preserve unambiguous category colours', async ({page}) => {
  await page.evaluate(() => {
    const saved = JSON.parse(JSON.stringify(state));
    saved.types.hist.hue = 'group';
    delete saved.page.category_format;
    saved.page.categories = {'group/shared': '#AABBCC', 'group/first': '#DDEEFF'};
    state = restore(saved); draw();
  });
  expect((await page.evaluate(() => build())).manifest.categories).toEqual({shared: '#AABBCC', first: '#DDEEFF'});
});

test('legacy links report conflicting shared colours and allow a choice', async ({page}) => {
  await page.evaluate(() => {
    const saved = JSON.parse(JSON.stringify(state));
    saved.type = 'grid';
    saved.grid.panels = [{type: 'hist', variable: ''}, {type: 'line', variable: ''}];
    saved.types.hist.hue = 'group'; saved.types.line.hue = 'other_group';
    delete saved.page.category_format;
    saved.page.categories = {'group/shared': '#AABBCC', 'other_group/shared': '#DDEEFF'};
    state = restore(saved); draw();
  });
  await expect(page.getByText(/saved link.*different colours.*shared/i)).toBeVisible();
  await expect(page.getByText(/#AABBCC, #DDEEFF/)).toBeVisible();
  await page.evaluate(() => { state = restore(JSON.parse(JSON.stringify(state))); draw(); });
  await expect(page.getByText(/#AABBCC, #DDEEFF/)).toBeVisible();
  const row = page.locator('.row').filter({has: page.locator('label', {hasText: /^shared$/})});
  await row.locator('input').fill('#abcdef');
  expect((await page.evaluate(() => build())).manifest.categories.shared).toBe('#ABCDEF');
  await expect(page.getByText(/saved link.*different colours.*shared/i)).toHaveCount(0);
});

test('legacy names containing slashes migrate without losing other bindings', async ({page}) => {
  await page.evaluate(() => {
    meta.groups.group = ['first', 'group/first'];
    const saved = JSON.parse(JSON.stringify(state));
    delete saved.page.category_format;
    saved.types.hist.hue = 'group';
    saved.page.categories = {'group/first': '#AABBCC', 'group/group/first': '#DDEEFF'};
    state = restore(saved); draw();
  });
  expect((await page.evaluate(() => build())).manifest.categories).toEqual({first: '#AABBCC', 'group/first': '#DDEEFF'});
  await page.evaluate(() => { state = restore(JSON.parse(JSON.stringify(state))); draw(); });
  expect((await page.evaluate(() => build())).manifest.categories).toEqual({first: '#AABBCC', 'group/first': '#DDEEFF'});
});
