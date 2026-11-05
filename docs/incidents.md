# Deployment incidents and evidence

## Where results are saved

Open GitHub → repository → Actions → **Deploy and verify Pages** → a run. At the bottom of its Summary, download an artifact:

- `pre-deployment-evidence`: Playwright HTML report and any failure traces/screenshots from checks before deployment. Repository-default retention (currently 90 days).
- `deployed-smoke-evidence`: live-site HTML report, failure traces/screenshots, `deployment-evidence.json`, and `playwright-results.json`. Retained for 7 days.
- `github-pages`: the built site package, normally retained for 1 day. It is not a test report.

A passing check normally has no failure screenshot or trace because Playwright retains those only on failure. After downloading and unzipping an artifact, run `npx playwright show-report /absolute/path/to/playwright-report` for the report, or `npx playwright show-trace /absolute/path/to/trace.zip` for an individual trace. Logs remain on each workflow job's page. Artifacts eventually expire; download evidence you need for the company presentation.

Local worker evidence is separate: `.runs/job-N/` holds prompt, agent output, base commit, verification log, patch, and review notes. Local Playwright output lives in `playwright-report/` and `test-results/`. These ignored folders are not Git commits or automatically uploaded.

## Automated failure reporting

After a failed deployed smoke job, a separate job downloads its evidence and calls `harness/incidents.py --send`. It receives the `CLICKUP_TOKEN` repository secret only for that step; the browser tests and application build do not receive it. Tasks are created only in demo List 901521438487. A missing token or unreadable artifact fails the reporting job visibly; the original smoke failure remains visible too.

An incident includes site URL, tested commit, workflow link, failed test identities and bounded error messages. It never includes the token or uploads raw browser traces to ClickUp. This demo uses synthetic data; review/redact test messages before adapting to real customer data.

Fingerprint: site + failure classification + sorted test file/title set. The commit is excluded so repeated releases with the same failure update the same open incident. Each run ID/attempt is recorded once. Existing human notes are preserved. Closed incidents are excluded; recurrence creates a new task. Changed test names or a changed set of failing checks can create a different incident.

The Pages workflow's concurrency group serializes deployment, checking and reporting. Do not invoke multiple external reporters concurrently: ClickUp has no atomic uniqueness constraint for this fingerprint. A timed-out write is not blindly retried; inspect ClickUp and rerun, which searches existing tasks first. Concurrent manual writes or delayed API visibility can still require reconciliation. This is a demo-level deduplication design, not exactly-once delivery.

## Triage before repair

Even an assertion failure with a matching deployed commit is not necessarily a code bug. All generated incidents contain `HARNESS_INCIDENT_TRIAGE`; the local worker holds them in `needs_input`. Deployment-identity failures, missing reports and browser startup problems are classified as infrastructure/unknown.

For an actual confirmed application regression, add precise reproduction and expected behavior, remove the triage marker, explicitly retry its worker job, then poll to refresh the description before running. This release automates reporting, not repair dispatch, closure, rollback or schedules. Failures before deployment and runner failures that prevent artifact upload require reviewing Actions; they do not reliably produce ClickUp incidents yet.

## Reporting rehearsal

The first reporting rehearsal deliberately expected seven seeded tickets instead of six without changing the app. Its incident is prominently labelled **Reporting rehearsal** and uses a separate fingerprint namespace. Its linked successful deployment run is a deployment reference only; the intentional failure report and trace are local under `.runs/reporting-rehearsal/`. This proves the API integration and deduplication, not a production failure or the GitHub failure-job execution. The full failure job becomes active after merging this PR and must still be observed in Actions.

For local inspection without writes:

```sh
python3 harness/incidents.py --evidence evidence.json --report playwright-results.json
```

`--send` explicitly enables writes and requires `CLICKUP_TOKEN` in the process environment. The reporter does not automatically read `.env`.
