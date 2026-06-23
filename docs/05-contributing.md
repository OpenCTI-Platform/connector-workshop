# Module 5 - Contributing and Wrap-up

**Time:** 15:25 - 15:55
**Goal:** know how to get a connector merged and what "done" means.

## Contribution workflow

Connectors live in the [OpenCTI connectors repo](https://github.com/OpenCTI-Platform/connectors). The flow:

1. **Fork and branch.** Create a feature branch off the default branch. Use a descriptive name (e.g. `feature/acme-feed-connector`).
2. **Develop.** Build your connector in the directory layout matching its type and existing connectors.
3. **Format and lint.** `isort`, `black`, `flake8` all pass.
4. **Commit.** Write clear commit messages. Follow the project's commit convention (conventional-commit style prefixes like `feat:`, `fix:`, `docs:` where used). Keep commits logical and reviewable.
5. **Open a PR.** Target the correct branch, fill in the PR template, describe what the connector does and how you tested it.
6. **Respond to review.** Maintainers will check structure, config, and STIX correctness. Address comments and keep the branch up to date.

## Minimum release criteria

Before a connector is considered ready:

- [ ] Follows the standard directory and file layout for its type
- [ ] Configuration via `config.yml.sample` + environment variables, no secrets committed
- [ ] Passes `isort`, `black`, `flake8`
- [ ] Builds and runs as a container (`Dockerfile`, `docker-compose.yml`)
- [ ] Uses deterministic STIX IDs and proper bundle construction
- [ ] Handles errors without crashing the run loop; surfaces failures on the work
- [ ] Persists state where applicable
- [ ] Has a complete `README.md`

## README standards

A connector README should let an operator deploy it without reading the code. Include:

- **What it does** and which connector type it is.
- **Requirements** (platform version, source/service prerequisites, API keys).
- **Configuration table:** every parameter, its environment variable, whether it's required, and the default.
- **Deployment** instructions (Docker Compose snippet).
- **Behavior notes:** what it imports/enriches, scheduling, and any rate limits.
- Known **limitations** or caveats (e.g. "does not support STIX 2.1", "requires a paid account").

## Key takeaways recap

- A connector produces well-formed STIX and hands it to the queue; it does not write to the DB or wait on ingestion.
- Pick the right type: EXTERNAL_IMPORT pulls on a schedule, INTERNAL_ENRICHMENT reacts to entities or any of the types we have seen together in the previous modules.
- Use the helper for config, logging, work, state, and sending bundles.
- Deterministic STIX IDs give you deduplication for free; state keeps you incremental.
- Format, lint, handle errors specifically, and never commit secrets.
- Read existing connectors, match their patterns, don't reinvent.
- Debug top-down: connector logs, then RabbitMQ, then worker logs.

## Useful links

See [resources.md](resources.md).

---

Back to [README](../README.md)
