import assert from 'node:assert/strict';
import dns from 'node:dns/promises';
import {EventEmitter} from 'node:events';
import http from 'node:http';
import https from 'node:https';
import test from 'node:test';
import timers from 'node:timers/promises';

import {
  checkLink,
  MAX_ATTEMPTS,
  RETRYABLE_STATUS,
} from '../scripts/check-external-links.mjs';

// The link check runs inside the required documentation gate and makes live
// requests to third-party hosts. Without a retry, one rate-limit response
// reddens a required check for a reason the author cannot influence -- and a
// gate that fails for reasons unrelated to the PR is one people learn to
// re-run rather than read.
//
// The attempt function is injected so these cases never touch the network:
// a test that depended on a real host would have the flakiness it is meant to
// fix.

function responder(statuses) {
  const remaining = [...statuses];
  const calls = {count: 0};
  const attempt = async () => {
    calls.count += 1;
    const next = remaining.shift();
    if (next instanceof Error) {
      throw next;
    }
    return next;
  };
  return {attempt, calls};
}

const noSleep = async () => {};

test('retries a rate-limited response and then succeeds', async () => {
  const {attempt, calls} = responder([429, 200]);
  await checkLink('https://example.test/a', attempt, noSleep);
  assert.equal(calls.count, 2, 'a 429 must be retried, not reported');
});

test('retries a server error and then succeeds', async () => {
  const {attempt, calls} = responder([503, 200]);
  await checkLink('https://example.test/b', attempt, noSleep);
  assert.equal(calls.count, 2);
});

test('retries a network-level failure', async () => {
  const {attempt, calls} = responder([new Error('ECONNRESET'), 200]);
  await checkLink('https://example.test/c', attempt, noSleep);
  assert.equal(calls.count, 2, 'a reset is the host, not the link');
});

test('does not retry a genuine broken link', async () => {
  const {attempt, calls} = responder([404, 200]);
  await assert.rejects(
    () => checkLink('https://example.test/gone', attempt, noSleep),
    /returned 404/,
  );
  assert.equal(
    calls.count,
    1,
    'retrying a 404 would turn a real broken link into a slow real broken link',
  );
});

test('gives up after the attempt ceiling', async () => {
  const {attempt, calls} = responder([429, 429, 429, 200]);
  await assert.rejects(
    () => checkLink('https://example.test/busy', attempt, noSleep),
    /returned 429/,
  );
  assert.equal(
    calls.count,
    MAX_ATTEMPTS,
    'an unbounded retry turns a dead host into a hung required check',
  );
});

test('a first-attempt success makes no further request', async () => {
  const {attempt, calls} = responder([200, 500]);
  await checkLink('https://example.test/ok', attempt, noSleep);
  assert.equal(calls.count, 1);
});

test('the retryable set covers only transient statuses', () => {
  for (const status of [408, 425, 429, 500, 502, 503, 504]) {
    assert.ok(RETRYABLE_STATUS.has(status), `${status} should be retryable`);
  }
  for (const status of [400, 401, 403, 404, 410, 451]) {
    assert.ok(
      !RETRYABLE_STATUS.has(status),
      `${status} names a wrong link, so retrying it hides the finding`,
    );
  }
});


function safeTransport(context, replies) {
  const remaining = [...replies];
  const calls = [];
  const diagnostics = [];
  const delays = [];
  const publicAddresses = [{address: '93.184.216.34', family: 4}];
  context.mock.method(dns, 'lookup', async () => publicAddresses);
  context.mock.method(process.stderr, 'write', (chunk) => {
    diagnostics.push(String(chunk));
    return true;
  });
  context.mock.method(timers, 'setTimeout', async (milliseconds) => {
    delays.push(milliseconds);
  });
  const privateRequest = context.mock.method(http, 'request', () => {
    assert.fail('A private redirect must be rejected before any HTTP connection');
  });
  context.mock.method(https, 'request', (url, options, callback) => {
    assert.deepEqual(options.headers, {'user-agent': 'astetik-docs-link-check/1.0'});
    options.lookup(url.hostname, {all: true}, (error, addresses) => {
      assert.equal(error, null);
      assert.deepEqual(addresses, publicAddresses);
    });
    options.lookup(url.hostname, {}, (error, address, family) => {
      assert.equal(error, null);
      assert.equal(address, publicAddresses[0].address);
      assert.equal(family, publicAddresses[0].family);
    });
    const reply = remaining.shift();
    assert.ok(reply, 'Unexpected additional HTTP request');
    const call = {url: url.href, method: options.method, resumed: 0};
    calls.push(call);
    const outgoing = new EventEmitter();
    outgoing.end = () => {
      queueMicrotask(() => callback({
        statusCode: reply.status,
        headers: reply.headers ?? {},
        resume() {
          call.resumed += 1;
        },
      }));
    };
    return outgoing;
  });
  return {calls, diagnostics, delays, privateRequest};
}

test('verifies a transient HEAD failure with safe GET', async (context) => {
  const transport = safeTransport(context, [{status: 503}, {status: 200}]);
  await checkLink('https://example.test/document');
  assert.deepEqual(transport.calls.map(({method}) => method), ['HEAD', 'GET']);
  assert.deepEqual(transport.calls.map(({resumed}) => resumed), [1, 1]);
  assert.deepEqual(transport.delays, []);
});

test('bounds HEAD and GET failures with real default delays', async (context) => {
  const transport = safeTransport(context, Array.from({length: MAX_ATTEMPTS * 2}, () => ({status: 503})));
  await assert.rejects(() => checkLink('https://example.test/unavailable'), /returned 503/);
  assert.deepEqual(transport.calls.map(({method}) => method), ['HEAD', 'GET', 'HEAD', 'GET', 'HEAD', 'GET']);
  assert.ok(transport.calls.every(({resumed}) => resumed === 1));
  assert.deepEqual(transport.delays, [500, 1000]);
});

test('rejects HEAD404 without GET or retry', async (context) => {
  const transport = safeTransport(context, [{status: 404}]);
  await assert.rejects(() => checkLink('https://example.test/missing'), /returned 404/);
  assert.deepEqual(transport.calls.map(({method}) => method), ['HEAD']);
  assert.equal(transport.calls[0].resumed, 1);
  assert.deepEqual(transport.delays, []);
});

test('rejects an unsafe GET redirect before any private connection', async (context) => {
  const replies = Array.from({length: MAX_ATTEMPTS}, () => [
    {status: 503}, {status: 302, headers: {location: 'http://127.0.0.1/private'}},
  ]).flat();
  const transport = safeTransport(context, replies);
  await assert.rejects(() => checkLink('https://example.test/redirect'), /non-public destination/);
  assert.equal(transport.privateRequest.mock.callCount(), 0);
  assert.deepEqual(transport.calls.map(({method}) => method), ['HEAD', 'GET', 'HEAD', 'GET', 'HEAD', 'GET']);
  assert.ok(transport.calls.every(({resumed}) => resumed === 1));
});

test('retains safe response diagnostics without URL secrets', async (context) => {
  const transport = safeTransport(context, [
    {status: 503, headers: {'x-github-request-id': 'ABC:123', 'retry-after': '60', 'set-cookie': 'unrelated-secret'}},
    {status: 200, headers: {'x-request-id': 'GET-123'}},
  ]);
  await checkLink('https://example.test/document?token=query-secret');
  assert.equal(transport.calls[1].url, 'https://example.test/document?token=query-secret');
  assert.match(transport.diagnostics[0], /HEAD https:\/\/example.test\/document returned 503 request-id="ABC:123" retry-after="60"/);
  assert.match(transport.diagnostics[1], /GET https:\/\/example.test\/document returned 200 request-id="GET-123"/);
  assert.doesNotMatch(transport.diagnostics.join(''), /query-secret|unrelated-secret/);
  await assert.rejects(
    () => checkLink('https://operator:credential-secret@example.test/document?token=query-secret'),
    (error) => {
      assert.match(error.message, /must not contain credentials/);
      assert.doesNotMatch(error.message, /operator|credential-secret|query-secret/);
      return true;
    },
  );
});

test('preserves safe GET verification for unsupported HEAD', async (context) => {
  const transport = safeTransport(context, [{status: 405}, {status: 200}]);
  await checkLink('https://example.test/head-unsupported');
  assert.deepEqual(transport.calls.map(({method}) => method), ['HEAD', 'GET']);
  assert.deepEqual(transport.delays, []);
});

test('rejects a definitive GET failure after a transient HEAD', async (context) => {
  const transport = safeTransport(context, [{status: 503}, {status: 404}]);
  await assert.rejects(() => checkLink('https://example.test/get-missing'), /returned 404/);
  assert.deepEqual(transport.calls.map(({method}) => method), ['HEAD', 'GET']);
  assert.deepEqual(transport.delays, []);
});
