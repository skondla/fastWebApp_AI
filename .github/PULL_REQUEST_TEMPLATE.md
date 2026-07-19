## What & why

<!-- One or two sentences: what changes, and the problem it solves. -->

## Type of change

- [ ] Feature
- [ ] Bug fix
- [ ] Security fix
- [ ] Infrastructure / pipeline
- [ ] Docs / governance

## Security impact statement (required)

<!-- Answer even if "none". Reviewers gate on this section. -->

- Does this change auth, session, or token handling? How?
- Does it touch a CI security gate, signing, or admission policy?
- Does it add a dependency, external endpoint, or new secret?
- Does it change what data is logged or retained?

## Checklist

- [ ] Pre-commit hooks pass locally (`pre-commit run -a`)
- [ ] No security gate weakened (`|| true`, `soft_fail`, `exit-code: "0"`)
- [ ] ADMIN and USER apps kept in lockstep for shared modules
- [ ] ADR added/updated for architectural decisions
- [ ] CHANGELOG.md updated
