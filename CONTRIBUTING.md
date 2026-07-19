# Contributing

## Workflow

1. Branch from `main` using `feature/<slug>`, `fix/<slug>`, or `sec/<slug>`
   (see [docs/governance/branching-strategy.md](docs/governance/branching-strategy.md)).
2. Install the pre-commit hooks once: `pip install pre-commit && pre-commit install`.
   They run GitLeaks, Bandit and hygiene checks locally — the same checks CI
   enforces, caught at the keyboard instead of in the pipeline.
3. Open a pull request against `main`. The PR template will ask for a
   security-impact statement; fill it honestly.
4. Every PR runs the full DevSecOps scan gauntlet (all blocking) plus an
   AI review pass ([actions/ai-code-review.yml](actions/ai-code-review.yml)).
   A human CODEOWNERS approval is always required — the AI review is
   advisory.
5. Squash-merge. `main` deploys via ArgoCD only; nothing applies manifests
   by hand (see [ADR-0001](docs/adr/0001-argocd-sole-applier.md)).

## Ground rules

- **Never weaken a gate.** No `|| true`, `soft_fail: true`, `exit-code: "0"`,
  or `continue-on-error` on a security step. If a finding is a false
  positive, suppress it in the tool's config file with a comment.
- **No secrets in code, env.sh files, or manifests.** Cloud auth is OIDC;
  runtime secrets come from the cloud secret manager via CSI.
- Architectural decisions get an ADR ([docs/adr/](docs/adr/)).
- Keep the ADMIN and USER apps in lockstep when touching shared modules
  (`security.py`, `security_middleware.py`, `token_store.py`, `telemetry.py`).

## Local development

```bash
cd dockerized/USER_FASTAPI
pip install -r requirements.txt
COOKIE_SECURE=0 python main.py          # http://localhost:50443 (no certs locally)
pytest
```

Set `REDIS_URL` to exercise distributed rate-limiting/revocation;
without it the app uses an in-process store.
