# Release, Deployment Validation, and Rollback Plan

## Release checklist
1. Confirm the latest change is committed to Git.
2. Push the branch and open a pull request.
3. Wait for the `Customer Support RAG CI` workflow to pass.
4. Review the changed files and test results before merging.
5. Deploy through the chosen hosting provider's documented process.
6. Set the GitHub repository secret `DEPLOY_HEALTH_URL` to the deployed API's `/health` URL.
7. In GitHub, open **Actions → Validate Deployed RAG API → Run workflow**.
8. Confirm the job reports `DEPLOYMENT VALIDATION PASSED`.
9. Manually test `/docs`, `/query`, `/feedback`, and the Streamlit UI.

## Rollback triggers
- The health check fails or returns a non-200 response.
- `/query` repeatedly returns server errors.
- The UI cannot reach the API.
- A critical regression is observed after deployment.

## Rollback procedure
1. Stop promoting the current release; record the failed commit and error.
2. Use the hosting provider's **rollback/previous release** feature if available.
3. Otherwise redeploy the last known-good Git commit/tag using that provider's documented deployment process.
4. Re-run the `Validate Deployed RAG API` workflow.
5. Manually verify `/health`, `/docs`, one safe test query, feedback submission, and the Streamlit UI.
6. Keep logs and screenshots for the incident; fix the issue on a branch and let CI pass before trying again.

## Git-only recovery (for local source, not a production deploy)
- Inspect changes: `git status` and `git log --oneline -5`.
- To undo an unpushed local commit: `git reset --hard <last-known-good-commit>` (destructive; only if you understand that uncommitted changes will be lost).
- For a commit already shared with others, prefer `git revert <bad-commit>` and push the new revert commit. This preserves history.

**Important:** Git commands alone do not roll back a running remote service. The last step must use the hosting provider's deployment/release mechanism.

## Security reminders
- Never store credentials in source files or commit `.env`.
- Use repository/environment secrets for deployment settings.
- Restrict who can deploy and roll back production.
- Do not send customer personal information to logs or test fixtures.
- The demo API should be protected with authentication, rate limiting, and safe logging before public production use.
