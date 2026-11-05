# Deployment and smoke verification

The `Deploy and verify Pages` workflow runs on pushes to main or manual dispatch from main. It verifies the application, builds one artifact, stamps it with the full commit SHA, deploys it to the `github-pages` environment, then runs browser tests against the URL returned by GitHub.

## One-time repository setup

In repository Settings → Pages, select **GitHub Actions** as the build/deployment source. Keep the `github-pages` environment limited to main. Merge the deployment PR; the workflow then runs automatically. No ClickUp token is required in GitHub for this milestone.

## Evidence and limitations

`deployment.json` identifies the artifact's commit. The smoke job checks it before and after exercising the deployed app. A missing or different SHA fails the job. It waits with bounded retries for Pages propagation. Workflow concurrency keeps our deployment and smoke steps together; changes made outside this workflow can still interfere and require investigation.

The workflow run contains build evidence and deployed browser reports/traces. A successful Pages deployment is not the same as a successful smoke job: check all three jobs. Failed deployed smoke checks create or update a ClickUp incident when the CLICKUP_TOKEN Actions secret is configured. They do not automatically roll back or dispatch a repair. See [incident reporting](incidents.md). Do not close a task on merge alone.

The deployed app contains only synthetic data held in browser memory. Smoke tests are safe to repeat against this demo; that does not imply they are safe for a future app backed by production data. The tests cover five selected journeys, not the entire application.

The manual `Deployment smoke check` workflow remains available for arbitrary demo URLs. It does not bind its results to a commit and is intended for exploratory checks. Use the deployment workflow for commit-correlated release evidence.

Pre-deployment verification now includes `npm run test:subpath`, which mounts the built artifact at the real Pages path and reuses the unchanged browser tests. This check failed on the deliberate path-dependent search seed before repair. Its reports are under `playwright-report/subpath/` and `test-results/subpath/`.
