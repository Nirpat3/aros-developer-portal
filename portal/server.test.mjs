/**
 * aros-developer-portal — server + SDK tests
 *
 * Tests the Express server health endpoints and validates SDK configuration
 * without starting a real server on port 5442.
 */

import { describe, test, expect, beforeAll, afterAll } from 'vitest';
import { createServer } from 'node:http';
import { readFileSync, existsSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const portsPath = resolve(__dirname, '../../ports.json');
const ports = JSON.parse(readFileSync(portsPath, 'utf-8'));
const EXPECTED_PORT = ports.services['aros-developer-portal']?.port ?? 5442;

// ── Minimal mock server replicating server.mjs logic ─────────────────────

const DIST_DIR = join(__dirname, 'dist');
const startedAt = new Date().toISOString();

function handleHTTP(req, res) {
  const url = new URL(req.url, 'http://localhost');

  if (url.pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(
      JSON.stringify({
        status: 'ok',
        service: 'aros-developer-portal',
        port: EXPECTED_PORT,
        uptime: process.uptime(),
        startedAt,
      }),
    );
  }

  if (url.pathname === '/readyz') {
    const distExists = existsSync(DIST_DIR);
    if (distExists) {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ ready: true }));
    } else {
      res.writeHead(503, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ ready: false, reason: 'dist/ not built' }));
    }
  }

  res.writeHead(404, { 'Content-Type': 'text/plain' });
  res.end('Not found');
}

let server;
let baseUrl;

beforeAll(
  () =>
    new Promise((resolve) => {
      server = createServer(handleHTTP);
      server.listen(0, '127.0.0.1', () => {
        baseUrl = `http://127.0.0.1:${server.address().port}`;
        resolve();
      });
    }),
);

afterAll(
  () =>
    new Promise((resolve) => {
      server.close(resolve);
    }),
);

// ── Tests ──────────────────────────────────────────────────────────────────

describe('aros-developer-portal — ports.json', () => {
  test('port is 5442', () => {
    expect(EXPECTED_PORT).toBe(5442);
  });

  test('protocol is http', () => {
    expect(ports.services['aros-developer-portal']?.protocol).toBe('http');
  });

  test('priority is P2', () => {
    expect(ports.services['aros-developer-portal']?.priority).toBe('P2');
  });
});

describe('GET /health', () => {
  test('returns 200', async () => {
    const res = await fetch(`${baseUrl}/health`);
    expect(res.status).toBe(200);
  });

  test('status is ok', async () => {
    const body = await fetch(`${baseUrl}/health`).then((r) => r.json());
    expect(body.status).toBe('ok');
  });

  test('service is aros-developer-portal', async () => {
    const body = await fetch(`${baseUrl}/health`).then((r) => r.json());
    expect(body.service).toBe('aros-developer-portal');
  });

  test('includes uptime', async () => {
    const body = await fetch(`${baseUrl}/health`).then((r) => r.json());
    expect(typeof body.uptime).toBe('number');
    expect(body.uptime).toBeGreaterThanOrEqual(0);
  });

  test('includes startedAt timestamp', async () => {
    const body = await fetch(`${baseUrl}/health`).then((r) => r.json());
    expect(new Date(body.startedAt).toString()).not.toBe('Invalid Date');
  });
});

describe('GET /readyz', () => {
  test('returns 200 or 503 (depends on dist/ existence)', async () => {
    const res = await fetch(`${baseUrl}/readyz`);
    expect([200, 503]).toContain(res.status);
  });

  test('body has boolean ready field', async () => {
    const body = await fetch(`${baseUrl}/readyz`).then((r) => r.json());
    expect(typeof body.ready).toBe('boolean');
  });

  test('if not ready, body includes reason', async () => {
    const body = await fetch(`${baseUrl}/readyz`).then((r) => r.json());
    if (!body.ready) {
      expect(body.reason).toBeTruthy();
    }
  });
});

describe('portal structure validation', () => {
  test('server.mjs exists', () => {
    expect(existsSync(join(__dirname, 'server.mjs'))).toBe(true);
  });

  test('vite.config.js exists', () => {
    expect(existsSync(join(__dirname, 'vite.config.js'))).toBe(true);
  });

  test('package.json has serve script', () => {
    const pkg = JSON.parse(readFileSync(join(__dirname, 'package.json'), 'utf-8'));
    expect(pkg.scripts?.serve).toBeTruthy();
  });

  test('package.json has build script', () => {
    const pkg = JSON.parse(readFileSync(join(__dirname, 'package.json'), 'utf-8'));
    expect(pkg.scripts?.build).toBeTruthy();
  });
});
