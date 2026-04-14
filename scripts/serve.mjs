import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, '..');

const basePort = Number(process.env.PORT || 5180 );

const mime = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.mjs', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.png', 'image/png'],
  ['.jpg', 'image/jpeg'],
  ['.jpeg', 'image/jpeg'],
  ['.webp', 'image/webp'],
  ['.gif', 'image/gif'],
  ['.svg', 'image/svg+xml; charset=utf-8']
]);

function safeResolve(urlPath) {
  const clean = urlPath.split('?')[0].split('#')[0];
  const decoded = decodeURIComponent(clean);
  const normalized = path.posix.normalize(decoded);
  const rel = normalized.replace(/^(\.\.(\/|\\|$))+/, '');
  const abs = path.resolve(root, rel.replace(/^\//, ''));
  if (!abs.startsWith(root)) return null;
  return abs;
}

const server = http.createServer(async (req, res) => {
  try {
    const reqUrl = req.url || '/';
    const urlPath = reqUrl === '/' ? '/scripts/index.html' : reqUrl;
    const abs = safeResolve(urlPath);
    if (!abs) {
      res.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Bad request');
      return;
    }

    let stat;
    try {
      stat = await fs.stat(abs);
    } catch {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Not found');
      return;
    }

    if (stat.isDirectory()) {
      // Serve directory index.html (avoid redirect loops in some clients)
      const indexAbs = path.join(abs, 'index.html');
      try {
        const indexBody = await fs.readFile(indexAbs);
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
        res.end(indexBody);
      } catch {
        const loc = reqUrl.endsWith('/') ? reqUrl : `${reqUrl}/`;
        res.writeHead(301, { Location: loc });
        res.end();
      }
      return;
    }

    const ext = path.extname(abs).toLowerCase();
    const type = mime.get(ext) || 'application/octet-stream';
    const body = await fs.readFile(abs);
    res.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'no-store' });
    res.end(body);
  } catch (e) {
    res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end(`Server error: ${e?.message || String(e)}`);
  }
});

function listenWithFallback(port, triesLeft = 20) {
  server.once('error', (err) => {
    if (err?.code === 'EADDRINUSE' && triesLeft > 0) {
      listenWithFallback(port + 1, triesLeft - 1);
      return;
    }
    throw err;
  });

  server.listen(port, () => {
    console.log(`Online-PT running at http://localhost:${port}/`);
    console.log(`Open: http://localhost:${port}/scripts/`);
  });
}

listenWithFallback(basePort);

