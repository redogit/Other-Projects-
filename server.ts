import { createServer } from './knowledge-garden/server.mjs';

const splitHosts = value => (value ?? '')
  .split(',')
  .map(value => value.trim())
  .filter(Boolean);

const allowedHosts = [
  process.env.VERCEL_URL,
  process.env.VERCEL_BRANCH_URL,
  process.env.VERCEL_PROJECT_PRODUCTION_URL,
  ...splitHosts(process.env.GARDEN_ALLOWED_HOSTS),
].filter(Boolean);

const rawPort = process.env.PORT ?? '3000';
if (!/^\d+$/.test(rawPort) || Number(rawPort) < 1 || Number(rawPort) > 65535) {
  throw new Error('PORT must be an integer from 1 to 65535.');
}

const server = createServer(undefined, { allowedHosts });
server.on('error', error => {
  console.error(`Knowledge Garden deployment server failed: ${error.message}`);
  process.exitCode = 1;
});
server.listen(Number(rawPort), '0.0.0.0', () => {
  console.log(`Knowledge Garden deployment server listening on port ${rawPort}.`);
});

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.once(signal, () => server.close());
}
