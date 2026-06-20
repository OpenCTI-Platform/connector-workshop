# Module 3 - Best Practices and Code Quality

**Time:** 13:30 - 14:35 (lecture ~35 min, mini lab ~30 min)
**Goal:** write connectors that reviewers will merge and operators can trust.

## Logging and error handling

Use the helper's logger, not `print`. It produces structured output the platform and operators can consume:

```python
self.helper.connector_logger.info("Starting run", {"feed": feed_url})
self.helper.connector_logger.error("Fetch failed", {"error": str(err)})
```

Error handling principles:

- **Fail loud, fail specific.** Catch the narrowest exception you can handle; let unexpected ones surface. A bare `except:` that swallows everything hides real bugs.
- **A failed run should not crash the connector.** For self-triggered connectors, catch per-run errors, log them, mark the work as failed, and let the next interval try again.
- **Mark work appropriately.** Use `to_processed(work_id, message, in_error=True)` so failures are visible in the UI rather than silent.
- **Don't retry blindly.** Distinguish transient (network, rate limit) from permanent (bad credentials, malformed source) and only retry the former.

## Code style: black, flake8, isort

The connector ecosystem standardizes on these. Run them before every commit:

```bash
isort .          # import ordering
black .          # formatting
flake8 .         # linting
```

Don't argue with the formatter. `black` is opinionated on purpose; consistent formatting removes a whole category of review comments. Configure all three in `pyproject.toml`/`setup.cfg` so everyone uses the same rules.

## State management and idempotency

Covered in Module 2, reinforced here: a well-behaved connector can be stopped and restarted without re-importing everything or losing its place. Persist your cursor/timestamp in state, and make your runs idempotent by relying on deterministic STIX IDs.

## Security hygiene: tokens and secrets

- **Never hardcode tokens.** Read them from environment variables or config that is injected at runtime.
- **Never commit secrets.** `config.yml` with real values stays out of git; commit a `config.yml.sample` with placeholders. Add the real file to `.gitignore`.
- **Never log secrets.** Be careful that error messages and debug logs don't echo the token or full request headers.
- **Least privilege.** The connector's platform user should have only the rights it needs.

## Read existing connectors, don't reinvent the wheel

The [OpenCTI connectors repo](https://github.com/OpenCTI-Platform/connectors) is the single best learning resource. Before building something custom:

- Find a connector of the same type and read its structure, you'll see the conventions for layout, config, and the run loop.
- Reuse the established patterns for state, work, and bundle construction rather than inventing your own.
- Match the file/module layout other connectors use so reviewers and operators find things where they expect.

## Mini lab: apply formatting and fix a bad error handler

Open [`labs/module3-mini-lab`](../labs/module3-mini-lab). You'll find a small file that:

1. Is not formatted (wrong import order, inconsistent style).
2. Contains a deliberately bad error handler (swallows everything, logs nothing useful, crashes the loop).

Your tasks:

- Run `isort`, `black`, and `flake8` and make them pass.
- Rewrite the error handler so failures are caught at the right granularity, logged with context, surfaced on the work, and non-fatal to the run loop.

A reference fix is in the same folder, try it yourself first.

---

Next: [Module 4 - Testing and Debugging](04-testing-debugging.md)
