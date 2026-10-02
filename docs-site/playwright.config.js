const {defineConfig} = require('@playwright/test');
const productDocs = require('./product-docs.json');
const port = Number(process.env.DOCS_PORT ?? 3100);
if (!Number.isInteger(port) || port < 1024 || port > 65535) {
  throw new Error('DOCS_PORT must be an integer between 1024 and 65535');
}

module.exports = defineConfig({
  testDir: './tests',
  testMatch: '**/*.spec.js',
  outputDir: './test-results',
  reporter: [['list']],
  workers: 2,
  use: {
    baseURL: `http://127.0.0.1:${port}${productDocs.basePath}`,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: `npm exec -- docusaurus serve --dir build --host 127.0.0.1 --port ${port} --no-open`,
    url: `http://127.0.0.1:${port}${productDocs.basePath}`,
    reuseExistingServer: false,
    timeout: 60000,
  },
});
