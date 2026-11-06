# Automatic ClickUp intake

The runner polls the demo List, investigates eligible tasks, asks questions on the individual task, and publishes verified repairs as GitHub PRs. A human reviews and merges. Hosting is not provisioned by this change.

## Selection and limits

Edit `harness/autopilot-policy.json` to configure selection. Defaults:

- Task type named **Bug** (a ClickUp task type, not a tag), sprint points **0.5–2**, priority **Normal or Low**.
- Status **to do**; High/Urgent, missing metadata, and incidents marked `HARNESS_INCIDENT_TRIAGE` are held.
- One task at a time, poll every 60 seconds, at most two investigations per rolling 24 hours and three per task.
- Investigation timeout 180 seconds; repair-agent timeout 600 seconds. These are execution limits, not monetary spending caps.

Create a Bug task type in the ClickUp workspace if absent. Assign the task's type, points, priority and status, and describe reproduction steps and expected behavior. The runner resolves the type ID from ClickUp; it does not infer Bug from the title.

## Run

Requires Python 3.9+, Node 20+, Codex CLI on PATH, configured Codex authentication, GitHub credentials with repository push/PR access, and Chromium installed for Playwright. Existing Chrome can be selected with `PLAYWRIGHT_CHANNEL=chrome`. Save `CLICKUP_TOKEN` in the ignored `.env` file.

```sh
# Read ClickUp and explain selection; no AI calls, comments or publication.
python3 harness/autopilot.py tick

# Process at most one eligible task.
PLAYWRIGHT_CHANNEL=chrome python3 harness/autopilot.py tick --execute

# Keep polling on this host until stopped.
PLAYWRIGHT_CHANNEL=chrome python3 harness/autopilot.py serve --execute

python3 harness/autopilot.py status
```

The host must remain awake and connected. This change does not install a service, provision a cloud host, or configure API-key authentication. A cloud deployment needs separate authentication and persistent storage setup; LangChain is not required.

## Questions, repair and publication

The investigator reads a checkout of fetched `origin/main`. It returns a concrete repair plan, up to three clarification questions, or an out-of-scope decision. Questions are posted on the task. A human reply or task edit permits another investigation within the attempt limits. The runner ignores its own marked comments when comparing task revisions.

A ready task enters the existing repair worker in an isolated checkout. Changes are restricted to `src/`; the controller runs the original `npm run verify`. Before repair and publication, the runner checks that task eligibility and contents have not changed. A changed task is held for a fresh investigation.

Verified patches are committed and pushed to a deterministic task branch, then opened as PRs. The PR link is commented on the task. Publication can resume after an API failure without rerunning the model. Existing closed PRs or mismatched branch commits require operator review. Open PRs block further attempts for that task. CI and human review still apply; passing the existing tests is not proof that every requested behavior is correct.

## Evidence and recovery

Evidence stays on the runner host in ignored `.runs/autopilot/`:

- `autopilot.sqlite3`: attempt state, task revision, result and PR link.
- `attempt-N/task.json`, `base.txt`: exact input and source revision.
- `attempt-N/investigation.json` and `investigation.jsonl`: structured decision and agent event trace.
- `attempt-N/repair/`: patch, agent events/summary, verification log and isolated checkout. Browser reports/traces are inside that checkout when produced.
- `attempt-N/publication.json` and `publish-*.log`: publication commit and Git output.

Do not commit these artifacts; they contain task content. Preserve this directory on a hosted runner or restart deduplication and budgets will be lost. GitHub Actions artifacts remain separate from these local artifacts.

Ctrl-C or `touch .runs/autopilot/STOP` stops polling after the current attempt finishes. Remove the STOP file deliberately before restarting. Interrupted or failed attempts are held. Inspect their evidence, then explicitly authorize a retry:

```sh
python3 harness/autopilot.py retry --attempt 1
```

A retry preserves evidence and still counts against task/daily limits. It runs on the next executable tick. The runner and manual worker share a process lock; do not run multiple hosts against the same List. This is a single-host demo, not a distributed queue. Task instructions are untrusted; the demo's sandbox and file gates are not a substitute for production isolation.

If the agent sandbox blocks server/browser execution, the repair agent may use a deterministic source finding and must disclose the runtime limitation. The controller still runs browser verification before publication. An empty repair is held for operator review; it is not automatically treated as a request for more task details.
