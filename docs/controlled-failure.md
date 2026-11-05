# Controlled deployed failure exercise

This branch intentionally introduces an application bug in synthetic demo data. Do not use this change in a real product. It is not a fabricated test result or a disabled test.

## What changes

Search normalization is mistakenly conditional on `window.location.pathname === '/'`. The root-hosted app trims whitespace correctly. At `/harness-engineering-demo/`, whitespace-only search returns zero tickets instead of all six. Other ticket behavior is unchanged.

## Why local CI can pass

The pre-deployment Playwright configuration exercises the root URL. GitHub Pages serves the same built app at a repository subpath. The existing whitespace regression test therefore passes before deployment and fails against the deployed site. The gap is deployment-shape coverage, not a bypass of an acceptance check.

## Expected sequence after human merge

1. Build and pre-deployment tests pass.
2. Pages deploys this intentionally faulty version.
3. Deployed smoke checks fail on the whitespace-only query.
4. The commit checks pass before and after the test, attributing evidence to this deployment.
5. `report_failure` creates one ClickUp smoke incident with a workflow link and assertion details.
6. The incident is held for triage. Confirm the reproduction, then run the repair worker and review its PR.
7. After merging the repair, deployment and smoke checks must pass before closing the incident.

Failure is expected during this exercise. A failed reporting job is a harness defect and must be investigated separately from the application regression. The exercise does not start unattended repair or automatically close a task.

## Restore and improve

The minimal restoration makes query normalization unconditional: `query.trim()`. If repair is blocked, revert this deliberate source change through a normal PR; no data migration is involved. The live synthetic app remains affected until the restoration deploys.

After restoration, add a pre-deployment browser check against a built artifact mounted at the Pages subpath. That should fail on this seed and pass on the fix, turning the discovered gap into durable harness coverage.

Local exercise evidence is saved in the ignored `.runs/subpath-exercise/` directory. GitHub evidence is in the deployment run's artifacts, as described in `docs/incidents.md`.
