# Signal — Harness engineering demo

A small React support dashboard used to practise evidence-based agent repairs. All customers and tickets are synthetic. This is a local-first scaffold, not yet an autonomous worker.

## Run

Requires Node 20+.

```sh
npm ci
npx playwright install chromium
npm run dev
```

If Chrome is already installed, you can run `PLAYWRIGHT_CHANNEL=chrome npm test` without downloading Chromium.

Open the URL printed by Vite. Data is held in memory: reload or **Reset demo** restores fixtures. **Simulate save failure** provides a deterministic failure path; this version has no backend or actual API latency.

## Verify

```sh
npm run verify
```

Build runs TypeScript checks. Playwright covers combined filters, save failure/recovery, note isolation/reset, and empty results. Failure traces and screenshots are retained in ignored artifact directories. CI uploads these artifacts. Tests are Chromium-only initially.

For an existing deployment:

```sh
SMOKE_BASE_URL=https://example.com/harness-engineering-demo/ npm test
```

The URL must include its trailing slash and any repository subpath. This runs browser checks against the deployed app, not the local server. Passing checks only establish coverage of these journeys.

## Integrations and next milestone

- Repository: https://github.com/Mohmmed93/harness-engineering-demo
- ClickUp List: `901521438487`
- Copy `.env.example` to `.env` when implementing the worker. Never put a ClickUp token in frontend variables or commit it.
- ClickUp read-only intake and the local repair worker are implemented. See [worker guide](docs/worker.md). Read-only ClickUp intake has been verified against the demo List.
- The worker runs one queued task only when explicitly invoked. PR publication and schedules are not automated.
- GitHub Actions includes verification and Pages deployment with automatic deployed-URL smoke checks. Enable the Pages Actions source and merge the workflow to activate it; see [deployment guide](docs/deployment.md). Deployed smoke failures create/update ClickUp incidents once the incident-reporting workflow is merged and the CLICKUP_TOKEN Actions secret is configured; see [results and incident reporting](docs/incidents.md).

See [implementation plan](docs/plan.md) and [example task](docs/example-task.md).
