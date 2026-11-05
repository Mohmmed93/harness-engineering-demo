# Four-day implementation plan

## Day 1: repeatable application environment

React dashboard, deterministic fixtures, reset control, explicit save-failure simulation, type checking/build, browser acceptance checks, CI evidence. Keep a passing baseline. For a repair demonstration, introduce a documented filter regression on a separate demo branch; do not knowingly break main.

## Day 2: task-to-PR worker

Implement a server-side ClickUp poller for List 901521438487. Read credentials from environment. Persist task ID, observed revision, job state, checkout path, attempt count, commit and PR URL in SQLite. Only eligible tasks in this list are accepted. States: queued, reproducing, implementing, verifying, ready_for_review, needs_input, failed. One worker initially. Atomic claiming and unique task/revision keys prevent duplicate execution.

Use an existing coding-agent CLI after confirming available authentication and noninteractive invocation. Give each job an isolated checkout, a task contract, a maximum runtime and attempt count. Ticket text is untrusted data, not permission to change policy or reveal secrets. Worker retains integration credentials; coding process receives only required access. Never fabricate successful execution if the agent isn't configured.

Require a failing reproduction before a bug repair, then a passing regression and full verification. Independently owned acceptance checks cannot be weakened by the repair. Create a PR with issue link, cause, scope, commands/results, and evidence. Human merges; no automatic production deployment.

## Day 3: deployment feedback

Select GitHub Pages/Actions hosting and configure the repository environment. Trigger checks only after successful staging deployment. Correlate URL, deployment ID and commit. Deduplicate incidents by environment + check/failure signature; update existing open incident on repeated failures. Distinguish app regressions from network/test infrastructure errors before dispatching repair. Do not close a ticket solely because a PR was merged; require verification on the deployed fix.

## Day 4: evaluation and rehearsal

Run a fixed task set from clean snapshots. Record verification success, human interventions, attempts, elapsed time and cost when available. Improve one concrete harness weakness and rerun the original and an unseen related task. Keep model/settings and checks constant. Add scheduled checks only after deduplication works; reuse the deployment check pipeline. Document blocked runs as results, not successes.

## Definition of complete demo

A real ClickUp task produces a real verified GitHub PR, a human merges it, the staging deployment is checked, and one seeded deployment failure creates exactly one repair incident. All evidence identifies the commit tested. Manual simulation remains clearly labelled until each integration is working.
