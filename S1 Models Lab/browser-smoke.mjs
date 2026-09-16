import { createServer } from 'node:http';
import { createServer as createTcpServer } from 'node:net';
import { readFile, mkdtemp, rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { extname, join, normalize, resolve, sep } from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';

const root = process.cwd();
const types = new Map([
  ['.html','text/html; charset=utf-8'], ['.mjs','text/javascript; charset=utf-8'],
  ['.js','text/javascript; charset=utf-8'], ['.css','text/css; charset=utf-8'], ['.json','application/json; charset=utf-8']
]);

function browserBinary() {
  const candidates = [process.env.CHROME_BIN, 'google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser'].filter(Boolean);
  for (const candidate of candidates) {
    if (candidate.includes(sep) && existsSync(candidate)) return candidate;
    const found = spawnSync('which', [candidate], { encoding: 'utf8' });
    if (found.status === 0 && found.stdout.trim()) return found.stdout.trim();
  }
  throw new Error('no Chrome/Chromium binary found for browser smoke');
}

function staticServer() {
  return createServer(async (req, res) => {
    try {
      const url = new URL(req.url, 'http://127.0.0.1');
      const pathname = decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname);
      const relative = normalize(pathname).replace(/^[/\\]+/, '');
      const file = resolve(root, relative);
      if (file !== root && !file.startsWith(root + sep)) throw new Error('path escape');
      const body = await readFile(file);
      res.writeHead(200, { 'content-type': types.get(extname(file)) ?? 'application/octet-stream', 'cache-control': 'no-store' });
      res.end(body);
    } catch {
      res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
      res.end('not found');
    }
  });
}

async function reserveTcpPort() {
  const probe = createTcpServer();
  await new Promise((resolveListen, rejectListen) => {
    probe.once('error', rejectListen);
    probe.listen(0, '127.0.0.1', resolveListen);
  });
  const address = probe.address();
  const port = address?.port;
  await new Promise(resolveClose => probe.close(resolveClose));
  if (!Number.isInteger(port) || port <= 0) throw new Error('failed to reserve Chrome DevTools port');
  return port;
}

async function connectCdp(port) {
  let target;
  for (let i = 0; i < 80; i++) {
    try {
      const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      target = targets.find(item => item.type === 'page');
      if (target?.webSocketDebuggerUrl) break;
    } catch {}
    await delay(100);
  }
  if (!target?.webSocketDebuggerUrl) throw new Error('Chrome DevTools page target not available');

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolveOpen, rejectOpen) => {
    ws.onopen = resolveOpen;
    ws.onerror = rejectOpen;
  });

  let nextId = 0;
  const pending = new Map();
  const exceptions = [];
  ws.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const { resolveCall, rejectCall } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) rejectCall(new Error(JSON.stringify(message.error)));
      else resolveCall(message.result);
      return;
    }
    if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params?.exceptionDetails?.text ?? 'runtime exception');
  };

  const send = (method, params = {}) => {
    const id = ++nextId;
    ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolveCall, rejectCall) => pending.set(id, { resolveCall, rejectCall }));
  };
  return { ws, send, exceptions };
}

async function evalValue(send, expression) {
  const response = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (response.exceptionDetails) throw new Error(response.exceptionDetails.exception?.description ?? response.exceptionDetails.text ?? 'browser evaluation failed');
  return response.result?.value;
}

async function waitFor(send, expression, label) {
  for (let i = 0; i < 80; i++) {
    if (await evalValue(send, expression)) return;
    await delay(100);
  }
  throw new Error(`timed out waiting for ${label}`);
}

function requireMatch(value, pattern, label) {
  if (!pattern.test(String(value))) throw new Error(`${label} failed: ${JSON.stringify(value)}`);
}

const server = staticServer();
const profile = await mkdtemp(join(tmpdir(), 's1-browser-smoke-'));
let chrome;
let ws;
try {
  await new Promise((resolveListen, rejectListen) => {
    server.once('error', rejectListen);
    server.listen(0, '127.0.0.1', resolveListen);
  });
  const address = server.address();
  const appUrl = `http://127.0.0.1:${address.port}/`;
  const browser = browserBinary();
  const debugPort = await reserveTcpPort();
  chrome = spawn(browser, [
    '--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
    '--remote-debugging-address=127.0.0.1', `--remote-debugging-port=${debugPort}`,
    `--user-data-dir=${profile}`, 'about:blank'
  ], { stdio: ['ignore', 'ignore', 'pipe'] });
  let browserStderr = '';
  chrome.stderr.on('data', chunk => { browserStderr += chunk.toString(); });

  let cdp;
  try {
    cdp = await connectCdp(debugPort);
  } catch (error) {
    if (chrome.exitCode !== null) throw new Error(`Chrome exited before DevTools became ready: ${browserStderr || error.message}`);
    throw new Error(`${error.message}; Chrome stderr: ${browserStderr || '(empty)'}`);
  }
  ws = cdp.ws;
  const { send, exceptions } = cdp;
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Page.navigate', { url: appUrl });
  await waitFor(send, `document.readyState === 'complete' && document.getElementById('inspection')?.textContent.includes('Moves: 0')`, 'S1 app initialization');

  const result = await evalValue(send, `(() => {
    const inspection = document.getElementById('inspection');
    const status = document.getElementById('status');
    const initial = inspection.textContent;
    document.getElementById('xw-plus').click();
    const afterMove = inspection.textContent;
    document.getElementById('save').click();
    const saveStatus = status.textContent;
    const savedCount = document.getElementById('saved-events').options.length;
    document.getElementById('replay').click();
    const replayStatus = status.textContent;
    const shell = document.getElementById('shell');
    shell.value = 'tesseract-boundary';
    shell.dispatchEvent(new Event('change', { bubbles: true }));
    const afterShell = inspection.textContent;
    const shellStatus = status.textContent;
    const yaw = document.getElementById('yaw');
    yaw.value = '0.2';
    yaw.dispatchEvent(new Event('input', { bubbles: true }));
    const afterObserver = inspection.textContent;
    document.getElementById('reframe').click();
    const reframeStatus = status.textContent;
    window.confirm = () => true;
    document.getElementById('clear').click();
    const clearStatus = status.textContent;
    return { initial, afterMove, saveStatus, savedCount, replayStatus, afterShell, shellStatus, afterObserver, reframeStatus, clearStatus };
  })()`);

  requireMatch(result.initial, /Moves: 0/, 'initial render');
  requireMatch(result.afterMove, /Moves: 1[\s\S]*Latest move: xw \+1°[\s\S]*Live equals mirror: false/, 'one-degree move');
  requireMatch(result.saveStatus, /^Saved .+ as (new-branch|variation|repeat)\.$/, 'save');
  if (result.savedCount < 1) throw new Error(`saved event selector was empty: ${result.savedCount}`);
  requireMatch(result.replayStatus, /^Replayed .+ exactly\.$/, 'replay');
  requireMatch(result.afterShell, /Shell: tesseract-boundary[\s\S]*Moves: 1/, 'shell reframe');
  requireMatch(result.shellStatus, /trajectory was preserved/, 'shell reframe status');
  requireMatch(result.afterObserver, /Observer: yaw=0\.2,/, 'observer update');
  requireMatch(result.reframeStatus, /^Reframed /, 'reframe');
  requireMatch(result.clearStatus, /^Local S1 history cleared\.$/, 'clear');
  if (exceptions.length) throw new Error(`browser runtime exception(s): ${exceptions.join(' | ')}`);

  process.stdout.write(JSON.stringify({ browser, appUrl, debugPort, checks: ['boot','move','save','replay','shell-reframe','observer','reframe','clear'] }, null, 2) + '\n');
} finally {
  try { ws?.close(); } catch {}
  if (chrome && chrome.exitCode === null) {
    const exited = new Promise(resolveExit => chrome.once('exit', resolveExit));
    chrome.kill('SIGTERM');
    await Promise.race([exited, delay(2000)]);
    if (chrome.exitCode === null) {
      chrome.kill('SIGKILL');
      await Promise.race([exited, delay(1000)]);
    }
  }
  await new Promise(resolveClose => server.close(resolveClose));
  await rm(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 });
}
