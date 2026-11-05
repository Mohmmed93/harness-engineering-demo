# Local task worker

This milestone implements ClickUp read-only intake, a persistent SQLite queue, dry runs, and a bounded Codex execution path that produces a local verified patch. It does not yet publish PRs, post ClickUp comments, deploy, or run on a schedule. Read-only ClickUp intake is verified. Real agent execution remains unvalidated until a suitable task is available.

## Credentials

Create `.env` in the repository root and set `CLICKUP_TOKEN`. This file is ignored. Do not paste credentials into a ticket or chat. The parser supports simple KEY=value entries only, without shell expansion. List ID is deliberately fixed to 901521438487 in the worker for this demo.

The installed `codex` CLI must be logged in. The controller filters integration tokens out of child process environments. This is not full credential isolation: a local agent still uses your account/home directory and its sandbox can have read access outside the checkout. Use synthetic demo data only. A dedicated container/account with restricted mounts is needed before handling company tickets or adversarial inputs.

## Try without external services

```sh
python3 harness/worker.py import --fixture fixtures/tasks.json
python3 harness/worker.py run --dry-run
python3 harness/worker.py status
python3 -m unittest discover -s harness_tests -v
```

Dry runs produce prompts, not repair claims. Repeat imports do not duplicate jobs. The fixture describes behavior that currently passes, so an actual run should report no reproducible issue instead of inventing changes.

## Read the ClickUp List

```sh
python3 harness/worker.py poll
python3 harness/worker.py status
```

Poll is a single read-only import, not a daemon. It reads open tasks from the dedicated List with pagination and a 15-second timeout per request. Existing tasks are included on the first import. One job per task ID is intentional: status/comment changes cannot re-trigger a repair. Tasks without descriptions are held as `needs_input`. Review imported tasks before running. After editing a held ClickUp task, explicitly retry it, then poll to refresh its payload before running.

## Run one job

Commit the baseline first; the working tree must be clean. Dependencies and a browser must be installed on this host. On this Mac, Chrome can be selected explicitly:

```sh
PLAYWRIGHT_CHANNEL=chrome python3 harness/worker.py run
```

Each job clones the committed baseline into `.runs/job-N/checkout`, installs locked dependencies without lifecycle scripts, invokes Codex with the workspace-write sandbox and no user configuration/rules, and applies a 600-second agent timeout. No sandbox bypass is used. A subprocess environment allowlist strips ClickUp/GitHub tokens. The controller rejects changes outside `src/`, runs the original verification command, and saves a patch and review report. Tests and configuration cannot be modified as part of this repair scope.

A passing run means the existing checks passed. Reproduction claims and coverage still need human review; there is no independent before/after reproduction gate yet. New-feature tasks needing changed tests/configuration are outside this first worker's scope. No-change outcomes are `needs_input`.

Artifacts contain task text and agent logs and remain ignored. Inspect them before sharing. They are not automatically uploaded. A file lock allows one worker command at a time. A timeout terminates the child process group. If the controller itself is killed, inspect/stop orphaned processes before recovery.

```sh
python3 harness/worker.py recover
python3 harness/worker.py retry --job 1
```

Recovery holds interrupted jobs for review. Explicit retry preserves previous evidence by archiving the job directory. There are no automatic retries or infinite repair loops. Queue state is local and should not be deleted while a worker is active.

## Next integration boundary

After a real read-only ClickUp import and controlled agent run, add authenticated GitHub publication with idempotent branch/PR lookup, then ClickUp result comments. Bind acceptance evidence to the tested base and patch. Add deployment/scheduled triggers only after that flow works. No automatic merge is planned.

References: https://developer.clickup.com/reference/gettasks and https://learn.chatgpt.com/docs/non-interactive-mode

## Verified first task and harness lesson

The first live task produced a one-line query-trimming repair. An independent browser check failed against the baseline on whitespace-only input, then passed against the repaired checkout along with the four existing checks. The originally suggested ` report ` query happened to match the fixture already; whitespace-only input was the confirmed failure.

The initial test configuration could reuse a running development server. The worker now supplies HARNESS_VERIFY=1 and TEST_PORT=4176; Playwright refuses server reuse and Vite uses strictPort. A port conflict fails verification instead of silently testing another checkout. The independent first-run checks used a dedicated server on port 4175.
