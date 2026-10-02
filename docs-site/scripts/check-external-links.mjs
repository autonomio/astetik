import dns from 'node:dns/promises';
import fs from 'node:fs/promises';
import http from 'node:http';
import https from 'node:https';
import net from 'node:net';
import path from 'node:path';
import timers from 'node:timers/promises';
import {fileURLToPath} from 'node:url';

import {resolveRepositoryFile} from './repository-paths.mjs';

const scriptPath = fileURLToPath(import.meta.url);
const repoRoot = path.resolve(path.dirname(scriptPath), '..', '..');
const docsMap = JSON.parse(
  await fs.readFile(path.resolve(repoRoot, 'docs-site', 'docs-map.json'), 'utf8')
);

function stripInlineCode(line) {
  let output = '';
  let index = 0;
  while (index < line.length) {
    const opening = line.indexOf('`', index);
    if (opening === -1) {
      return output + line.slice(index);
    }
    output += line.slice(index, opening);
    let markerEnd = opening;
    while (line[markerEnd] === '`') {
      markerEnd += 1;
    }
    const marker = line.slice(opening, markerEnd);
    const closing = line.indexOf(marker, markerEnd);
    if (closing === -1) {
      return output;
    }
    index = closing + marker.length;
  }
  return output;
}

export function stripMarkdownCode(text) {
  let fence = null;
  return text.split('\n').map((line) => {
    const match = line.match(/^\s*(`{3,}|~{3,})/);
    if (match) {
      const marker = match[1];
      if (fence === null) {
        fence = marker;
      } else if (marker[0] === fence[0] && marker.length >= fence.length) {
        fence = null;
      }
      return '';
    }
    return fence === null ? stripInlineCode(line) : '';
  }).join('\n');
}

export function extractExternalLinks(text) {
  const links = new Set();
  const prose = stripMarkdownCode(text);
  const patterns = [
    /\[[^\]]*]\((https?:\/\/[^)\s]+)\)/g,
    /(?:href|src)=["'](https?:\/\/[^"']+)["']/g,
  ];
  for (const pattern of patterns) {
    for (const match of prose.matchAll(pattern)) {
      links.add(match[1]);
    }
  }
  return links;
}

function isPrivateIpv4(address) {
  const [first, second, third] = address.split('.').map(Number);
  return (
    first === 0
    || first === 10
    || first === 127
    || (first === 100 && second >= 64 && second <= 127)
    || (first === 169 && second === 254)
    || (first === 172 && second >= 16 && second <= 31)
    || (first === 192 && second === 0 && [0, 2].includes(third))
    || (first === 192 && second === 168)
    || (first === 198 && (second === 18 || second === 19))
    || address.startsWith('198.51.100.')
    || address.startsWith('203.0.113.')
    || first >= 224
  );
}

export function isPublicAddress(address) {
  const normalized = address.toLowerCase();
  if (net.isIP(normalized) === 4) {
    return !isPrivateIpv4(normalized);
  }
  if (net.isIP(normalized) !== 6) {
    return false;
  }
  if (normalized.startsWith('::ffff:')) {
    return isPublicAddress(normalized.slice('::ffff:'.length));
  }
  return !(
    normalized === '::'
    || normalized === '::1'
    || normalized.startsWith('fc')
    || normalized.startsWith('fd')
    || /^fe[89ab]/.test(normalized)
    || normalized.startsWith('ff')
    || normalized.startsWith('2001:db8:')
  );
}

function displayUrl(url) {
  const parsed = new URL(url);
  return `${parsed.protocol}//${parsed.host}${parsed.pathname}`;
}

function reportResponse(url, method, response) {
  const status = response.statusCode;
  if (method === 'HEAD' && status >= 200 && status < 300) {
    return;
  }
  const fields = [
    ['request-id', response.headers['x-github-request-id'] ?? response.headers['x-request-id']],
    ['retry-after', response.headers['retry-after']],
  ].filter(([, value]) => value !== undefined)
    .map(([name, value]) => ` ${name}=${JSON.stringify(String(value).slice(0, 160))}`)
    .join('');
  process.stderr.write(`External link ${method} ${displayUrl(url)} returned ${status}${fields}\n`);
}

export async function assertPublicUrl(url) {
  const parsed = new URL(url);
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error(`${displayUrl(url)} must use HTTP or HTTPS`);
  }
  if (parsed.username || parsed.password) {
    throw new Error(`${displayUrl(url)} must not contain credentials`);
  }
  const hostname = parsed.hostname.replace(/^\[|\]$/g, '').toLowerCase();
  if (hostname === 'localhost' || hostname.endsWith('.localhost')) {
    throw new Error(`${displayUrl(url)} resolves to a non-public destination`);
  }
  const family = net.isIP(hostname);
  const addresses = family
    ? [{address: hostname, family}]
    : await dns.lookup(hostname, {all: true});
  if (
    addresses.length === 0
    || addresses.some(({address}) => !isPublicAddress(address))
  ) {
    throw new Error(`${displayUrl(url)} resolves to a non-public destination`);
  }
  return {addresses, parsed};
}

function pinnedLookup(addresses) {
  return (_hostname, options, callback) => {
    if (options.all) {
      callback(null, addresses);
      return;
    }
    const [{address, family}] = addresses;
    callback(null, address, family);
  };
}

async function requestOnce(url, method) {
  const {addresses, parsed} = await assertPublicUrl(url);
  const transport = parsed.protocol === 'https:' ? https : http;
  return new Promise((resolve, reject) => {
    const outgoing = transport.request(
      parsed,
      {
        headers: {'user-agent': 'astetik-docs-link-check/1.0'},
        lookup: pinnedLookup(addresses),
        method,
        signal: AbortSignal.timeout(15000),
      },
      (response) => {
        reportResponse(url, method, response);
        resolve(response);
      }
    );
    outgoing.on('error', reject);
    outgoing.end();
  });
}

async function request(url, method) {
  let currentUrl = url;
  for (let redirectCount = 0; redirectCount <= 5; redirectCount += 1) {
    const response = await requestOnce(currentUrl, method);
    if (![301, 302, 303, 307, 308].includes(response.statusCode)) {
      return response;
    }
    const location = response.headers.location;
    response.resume();
    if (!location) {
      throw new Error(`${displayUrl(currentUrl)} redirected without a location`);
    }
    currentUrl = new URL(location, currentUrl).href;
  }
  throw new Error(`${displayUrl(url)} exceeded five redirects`);
}

// Statuses that mean "not now" rather than "this link is wrong". Retrying the
// second class -- 404 and its neighbours -- would turn a real broken link into
// a slow real broken link, which is the opposite of what this check is for.
export const RETRYABLE_STATUS = new Set([408, 425, 429, 500, 502, 503, 504]);
// Bounded on purpose: an unbounded retry converts a dead host into a hung
// required check, which is worse than a red one.
export const MAX_ATTEMPTS = 3;
const RETRY_BASE_MS = 500;

async function attemptLink(url) {
  const response = await request(url, 'HEAD');
  if (response.statusCode === 405 || RETRYABLE_STATUS.has(response.statusCode)) {
    response.resume();
    const getResponse = await request(url, 'GET');
    getResponse.resume();
    return getResponse.statusCode;
  }
  response.resume();
  return response.statusCode;
}

export async function checkLink(url, attempt = async (u) => attemptLink(u), sleep = timers.setTimeout) {
  let lastStatus = null;
  for (let tries = 1; tries <= MAX_ATTEMPTS; tries += 1) {
    let status;
    try {
      status = await attempt(url);
    } catch (error) {
      // A network-level failure -- DNS, reset, the 15s timeout -- is the same
      // class as a 5xx: the host, not the link.
      if (tries === MAX_ATTEMPTS) {
        throw error;
      }
      await sleep(RETRY_BASE_MS * tries);
      continue;
    }
    if (status >= 200 && status < 300) {
      return;
    }
    lastStatus = status;
    if (!RETRYABLE_STATUS.has(status) || tries === MAX_ATTEMPTS) {
      break;
    }
    await sleep(RETRY_BASE_MS * tries);
  }
  throw new Error(`${displayUrl(url)} returned ${lastStatus}`);
}

async function main() {
  const links = new Set();
  for (const document of docsMap.documents) {
    const sourcePath = resolveRepositoryFile(repoRoot, document.source);
    const text = await fs.readFile(sourcePath, 'utf8');
    for (const url of extractExternalLinks(text)) {
      links.add(url);
    }
  }
  for (const url of [...links].sort()) {
    await checkLink(url);
  }
  process.stdout.write(`External links healthy: ${links.size}\n`);
}

if (process.argv[1] === scriptPath) {
  await main();
}
