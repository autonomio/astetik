const path = require('node:path');
const productDocs = require('./product-docs.json');
const prismTheme = {
  plain: {color: 'var(--astetik-ink)', backgroundColor: 'var(--astetik-paper-2)'},
  styles: [
    {types: ['comment', 'prolog', 'doctype', 'cdata'], style: {color: 'var(--astetik-ink-mute)'}},
    {types: ['punctuation', 'operator'], style: {color: 'var(--astetik-ink-soft)'}},
    {types: ['keyword', 'selector', 'atrule'], style: {color: 'var(--astetik-accent)'}},
    {types: ['string', 'attr-value'], style: {color: 'var(--astetik-syntax-string)'}},
    {types: ['number', 'boolean', 'constant'], style: {color: 'var(--astetik-syntax-number)'}},
    {types: ['function', 'class-name', 'property', 'attr-name', 'tag'], style: {color: 'var(--astetik-ink-deep)'}},
  ],
};

function repositoryCoordinates(sourceRepoUrl) {
  const url = new URL(sourceRepoUrl);
  const [organizationName, projectName] = url.pathname.split('/').filter(Boolean);
  return {organizationName, projectName};
}

const baseUrl = productDocs.basePath;
const url = productDocs.siteUrl;
const {organizationName, projectName} = repositoryCoordinates(productDocs.sourceRepoUrl);
const faviconLetter = encodeURIComponent(productDocs.productName.slice(0, 1).toUpperCase());

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: productDocs.productName,
  tagline: productDocs.tagline,
  url,
  baseUrl,
  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },
  favicon: `data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>${faviconLetter}</text></svg>`,
  trailingSlash: false,
  organizationName,
  projectName,
  themes: [],
  plugins: [
    [
      require.resolve('@easyops-cn/docusaurus-search-local'),
      {
        docsRouteBasePath: '/',
        docsDir: '.generated/docs',
        indexDocs: true,
        indexBlog: false,
        hashed: true,
      },
    ],
  ],
  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          path: path.resolve(__dirname, '.generated/docs'),
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: `${productDocs.sourceRepoUrl}/edit/${productDocs.sourceBranch}/`,
        },
        blog: false,
        pages: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],
  staticDirectories: [path.resolve(__dirname, '.generated/static')],
  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: {respectPrefersColorScheme: true},
      metadata: [
        {name: 'description', content: productDocs.tagline},
        {property: 'og:type', content: 'website'},
        {property: 'og:site_name', content: productDocs.productName},
        {property: 'og:title', content: `${productDocs.productName} Docs`},
        {property: 'og:description', content: productDocs.tagline},
        {property: 'og:url', content: `${url}${baseUrl}`},
        {name: 'twitter:card', content: 'summary'},
        {name: 'twitter:title', content: `${productDocs.productName} Docs`},
        {name: 'twitter:description', content: productDocs.tagline},
      ],
      navbar: {
        title: productDocs.productName,
        items: [
          {to: '/', label: 'Home', position: 'left'},
          {to: '/overview', label: 'Overview', position: 'left'},
          {to: '/guides', label: 'Guides', position: 'left'},
          {to: '/reference', label: 'Reference', position: 'left'},
          {to: '/developer', label: 'Developer', position: 'left'},
          {to: '/packages', label: 'Packages', position: 'left'},
          {href: productDocs.sourceRepoUrl, label: 'GitHub', position: 'right'},
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {label: 'Overview', to: '/overview'},
              {label: 'Guides', to: '/guides'},
              {label: 'Reference', to: '/reference'},
              {label: 'Developer', to: '/developer'},
              {label: 'Packages', to: '/packages'},
            ],
          },
          {
            title: 'Product',
            items: [
              {label: 'Repository', href: productDocs.sourceRepoUrl},
              {label: 'Autonomio', href: 'https://github.com/autonomio'},
            ],
          },
        ],
        copyright: `Copyright ${new Date().getFullYear()} ${organizationName}.`,
      },
      prism: {
        theme: prismTheme,
        darkTheme: prismTheme,
      },
      docs: {
        sidebar: {
          hideable: true,
        },
      },
    }),
};

module.exports = config;
