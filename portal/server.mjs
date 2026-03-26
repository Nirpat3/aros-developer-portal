/**
 * aros-developer-portal — production server
 *
 * Serves the Vite-built SPA from dist/ with /health and /readyz endpoints.
 * Binds to 0.0.0.0 per platform standard.
 */

import express from 'express';
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Port: read from ports.json (single source of truth), env override allowed
function loadPort() {
  try {
    const portsPath = resolve(__dirname, '../../ports.json');
    const ports = JSON.parse(readFileSync(portsPath, 'utf-8'));
    return ports.services['aros-developer-portal']?.port ?? 5442;
  } catch {
    return 5442;
  }
}

const PORT = parseInt(process.env.PORT || loadPort(), 10);
const DIST_DIR = join(__dirname, 'dist');
const startedAt = new Date().toISOString();

const app = express();

// ── Health endpoints ────────────────────────────────────────
app.get('/health', (_req, res) => {
  res.json({
    status: 'ok',
    service: 'aros-developer-portal',
    port: PORT,
    uptime: process.uptime(),
    startedAt,
  });
});

app.get('/readyz', (_req, res) => {
  const distExists = existsSync(DIST_DIR);
  if (distExists) {
    res.json({ ready: true });
  } else {
    res.status(503).json({ ready: false, reason: 'dist/ not built' });
  }
});

// ── Static files ────────────────────────────────────────────
if (existsSync(DIST_DIR)) {
  app.use(express.static(DIST_DIR, { maxAge: '1d' }));

  // SPA fallback — serve index.html for all non-file routes
  app.get('*', (_req, res) => {
    res.sendFile(join(DIST_DIR, 'index.html'), (err) => {
      if (err && !res.headersSent) {
        res.status(500).send('Internal Server Error');
      }
    });
  });
} else {
  app.get('*', (_req, res) => {
    res.status(503).send('Build not found. Run: npm run build');
  });
}

// ── Error handling ──────────────────────────────────────────
app.use((err, _req, res, _next) => {
  console.error(`[aros-developer-portal] Express error: ${err.message}`);
  if (!res.headersSent) {
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

process.on('uncaughtException', (err) => {
  console.error(`[aros-developer-portal] Uncaught exception: ${err.message}`);
  if (err.code === 'EADDRINUSE') {
    console.error(`[aros-developer-portal] Port ${PORT} already in use — exiting`);
    process.exit(1);
  }
});

process.on('unhandledRejection', (reason) => {
  console.error(`[aros-developer-portal] Unhandled rejection:`, reason);
});

process.on('SIGTERM', () => {
  console.log('[aros-developer-portal] SIGTERM received — shutting down');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('[aros-developer-portal] SIGINT received — shutting down');
  process.exit(0);
});

// ── Start ───────────────────────────────────────────────────
app.listen(PORT, '0.0.0.0', () => {
  console.log(`[aros-developer-portal] listening on 0.0.0.0:${PORT}`);
});
