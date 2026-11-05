import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { dirname, resolve, sep, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const dist = resolve(root, 'dist');
const prefix = '/harness-engineering-demo/';
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml' };
// Serve only the built artifact, mounted exactly as it is on GitHub Pages.
const server = createServer(async (request, response) => {
  try {
    const path = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    if (!path.startsWith(prefix)) { response.writeHead(404).end(); return; }
    const file = resolve(dist, path.slice(prefix.length) || 'index.html');
    if (!file.startsWith(dist + sep)) { response.writeHead(403).end(); return; }
    const body = await readFile(file);
    response.writeHead(200, { 'Content-Type': types[extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    response.end(body);
  } catch { response.writeHead(404).end(); }
});
await new Promise((resolve, reject) => {
  server.once('error', reject);
  server.listen(0, '127.0.0.1', resolve);
});
const url = `http://127.0.0.1:${server.address().port}${prefix}`;
console.log(`Testing the built artifact at ${url}`);
try {
  const child = spawn(process.execPath, [resolve(root, 'node_modules/@playwright/test/cli.js'), 'test', '--config', 'playwright.subpath.config.ts'], {
    cwd: root, stdio: 'inherit', env: { ...process.env, SMOKE_BASE_URL: url },
  });
  const code = await new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('exit', code => resolve(code ?? 1));
  });
  process.exitCode = code;
} finally {
  server.closeAllConnections();
  await new Promise(resolve => server.close(resolve));
}
