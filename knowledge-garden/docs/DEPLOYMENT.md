# Knowledge Garden deployment

September 14, 2026

The repository root now contains `server.ts`, a deliberately thin production entry point for the existing Knowledge Garden Node server. It does not replace or duplicate the Garden request logic. It imports `knowledge-garden/server.mjs`, constructs the same validated/compiled read-only server, and listens on the host-provided `PORT`.

## Vercel path

Vercel announced zero-configuration deployment for root `server.ts` Node servers in June 2026. Connecting this repository to a Vercel project should therefore use the repository root, not a rewritten serverless API tree.

The adapter admits hostnames from Vercel's runtime system variables:

- `VERCEL_URL`
- `VERCEL_BRANCH_URL`
- `VERCEL_PROJECT_PRODUCTION_URL`

An operator can add comma-separated additional hostnames with `GARDEN_ALLOWED_HOSTS` when a deployment requires another explicit host. The adapter does not enable a wildcard host.

## Preserved boundaries

- The existing Garden compiler and plan validation remain unchanged.
- API methods remain GET/HEAD only.
- Imported working sets remain data and never gain execution authority.
- The mutable adjective/AOP layer remains sidecar-only with preserved semantics.
- Local development still uses `cd knowledge-garden && npm start`.
- Deployment does not upgrade browser or assistive-technology acceptance evidence.

## Verification before production

Run from the repository checkout:

```text
cd knowledge-garden
npm test
npm run build
node server.mjs --check-catalog
```

Then exercise the deployed `/api/health`, `/api/catalog`, root page, search, hierarchy, checkpoint/restore UI, and keyboard/screen-reader behavior. Production availability is a deployment fact, not evidence of accessibility acceptance or scientific validation.
