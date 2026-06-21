# Module 3 - Best Practices and Code Quality

**Time:** 13:30 - 14:35 (lecture ~35 min, mini lab ~30 min)
**Goal:** write connectors that reviewers will merge and operators can trust.

## Bundles vs API calls

In the module 2 lab, you built a connector that fetched data from an external source and sent it to the platform as a STIX bundle. This is the recommended pattern for most connectors: fetch, transform, and send a bundle.

The OpenCTI API client is accessible through `self.helper.api`, allowing direct queries against the platform. However, this approach is **not recommended** in most connector workflows.

Here is an example of using the API client to read an entity and list indicators:

```python
# Get entity by ID
entity = self.helper.api.stix_domain_object.read(id=entity_id)

# Search indicators
indicators = self.helper.api.indicator.list(
    filters=[{
        "key": "pattern_type",
        "values": ["stix"]
    }]
)
```

**Why it should be avoided:**

- **Performance impact.** Direct API calls add extra load on the OpenCTI platform, especially when listing large collections or making calls in loops.
- **Tight coupling.** Relying on specific API endpoints makes the connector more fragile to platform API changes.
- **Limited functionality.** The API client may not support all operations needed for complex processing, leading to workarounds that can be inefficient.

## Deterministic STIX IDs

We have talked about it in module 2 as well. When creating STIX objects, use deterministic IDs based on the object's content. This ensures that the same object will always have the same ID, preventing duplicates and making it easier to track entities across runs.

The `id` of the STIX object is generated using the `generate_id()` method from the `pycti` library. For details, check the [Data Deduplication Strategies on OpenCTI](https://github.com/OpenCTI-Platform/connectors/blob/master/docs/02-external-import-specifications.md#data-deduplication-strategies) section. It is important to use the `generate_id()` method to ensure that the `id` of the STIX object is unique and consistent across different runs of the connector and prevent duplicates.

## Logging Best Practices

### Using the Connector Logger

Always use `self.helper.connector_logger`:

```python
# Info level - general information
self.helper.connector_logger.info(
    "Starting data collection",
    {"source": "api.example.com"}
)

# Debug level - detailed information for debugging
self.helper.connector_logger.debug(
    "API response received",
    {"status_code": 200, "items": 42}
)

# Warning level - something unexpected but not fatal
self.helper.connector_logger.warning(
    "Rate limit approaching",
    {"remaining": 10, "reset_time": reset_time}
)

# Error level - errors that prevent processing
self.helper.connector_logger.error(
    "Failed to fetch data",
    {"error": str(e), "url": url}
)
```

### Log Levels

Set via `CONNECTOR_LOG_LEVEL` environment variable or `connector.log_level` in config:

- `debug` - Verbose output for development
- `info` - General operational messages (recommended)
- `warning` - Unexpected situations
- `error` - Errors that prevent operation

### Structured Logging

Always pass context as a dictionary:

```python
# Good - structured
self.helper.connector_logger.info(
    "Processing entity",
    {"entity_id": entity_id, "entity_type": entity_type}
)

# Bad - string concatenation
self.helper.connector_logger.info(
    f"Processing entity {entity_id} of type {entity_type}"
)
```

## Error handling

Error handling principles:

- **Fail loud, fail specific.** Catch the narrowest exception you can handle; let unexpected ones surface. A bare `except:` that swallows everything hides real bugs.
- **A failed run should not crash the connector.** For self-triggered connectors, catch per-run errors, log them, mark the work as failed, and let the next interval try again.
- **Mark work appropriately.** Use `to_processed(work_id, message, in_error=True)` so failures are visible in the UI rather than silent.
- **Don't retry blindly.** Distinguish transient (network, rate limit) from permanent (bad credentials, malformed source) and only retry the former.

### Exception Handling Pattern

```python
def process_message(self, data: dict) -> str:
    try:
        # Main processing logic
        result = self._process_data(data)
        return f"Successfully processed {result}"

    except KeyError as e:
        # Handle missing data
        self.helper.connector_logger.error(
            "Missing required field",
            {"error": str(e), "data": data}
        )
        return f"Failed: missing field {e}"

    except requests.exceptions.RequestException as e:
        # Handle API errors
        self.helper.connector_logger.error(
            "API request failed",
            {"error": str(e)}
        )
        return f"Failed: API error {e}"

    except Exception as e:
        # Catch-all for unexpected errors
        self.helper.connector_logger.error(
            "Unexpected error",
            {"error": str(e), "type": type(e).__name__}
        )
        raise  # Re-raise unexpected errors
```

### Traceback

Use custom exceptions for **clarity and control**; use `raise ... from ...` to **preserve the traceback** and maintain context.

## Retry strategy and API calls: retries, backoff, and rate limiting

External feeds fail in ways your connector doesn't control: the source has a brief outage, throttles you, or returns a 5xx. A production connector treats these as expected and retries them gracefully instead of dying on the first hiccup. Don't hand-roll retry loops with `time.sleep`, use a dedicated library so the behavior is correct and readable.

The OpenCTI **ServiceNow** external-import connector is a good reference. Its API client wraps every request with [`tenacity`](https://tenacity.readthedocs.io/) for retry-with-backoff and a leaky-bucket rate limiter, and lets `aiohttp` raise on HTTP error status so failures actually trigger the retry. Stripped to the essentials:

```python
from aiohttp import ClientSession
from tenacity import retry, stop_after_attempt, wait_exponential_jitter


async def _request_data(self, table_name, query_parameters):
    url = self._build_url(table_name, query_parameters)

    @retry(
        stop=stop_after_attempt(self.api_retry),           # cap the attempts
        wait=wait_exponential_jitter(                      # back off, with jitter
            initial=1, max=self.api_backoff, exp_base=2, jitter=1
        ),
    )
    async def _retry_wrapped():
        async with ClientSession(
            headers=self.headers,
            raise_for_status=True,   # 4xx/5xx become exceptions -> retried
            trust_env=True,          # honor proxy env vars
        ) as session:
            async with session.get(url=url) as response:
                return await response.json()

    async with self.rate_limiter:    # leaky bucket: stay under the source's limits
        return await _retry_wrapped()
```

What to take from this pattern:

- **Cap the attempts.** `stop_after_attempt(n)` means a persistently failing source eventually gives up and surfaces the error rather than retrying forever.
- **Exponential backoff with jitter.** Each retry waits longer (`exp_base=2`), up to a ceiling (`max`), and `jitter` randomizes the delay so many connectors don't retry in lockstep and hammer a recovering source (the "thundering herd").
- **`raise_for_status=True` is what makes retries fire.** If you silently accept a 500 response, `tenacity` never sees a failure and never retries. Let bad statuses raise.
- **Rate-limit on purpose.** The leaky-bucket limiter caps request rate so you respect the source's quota instead of getting throttled or banned. This complements retries: backoff handles failures, the limiter prevents them.
- **Make it configurable.** ServiceNow exposes `api_retry`, `api_backoff`, and the leaky-bucket rate/capacity as config. Operators tune resilience to their instance without code changes; never bake these as magic numbers.
- **Don't retry the un-retryable.** Scope retries to transient conditions. A `401` from a bad token or a malformed payload will fail identically every attempt, so wasting retries on it just delays a clear error.

So, when you create connector and need to connector to external sources, the interesting information is to know the limitation quota of the source, and to implement a retry strategy with backoff and rate limiting. This will make your connector more resilient and reliable in production.

## State management and idempotency

Covered in Module 2, reinforced here: a well-behaved connector can be stopped and restarted without re-importing everything or losing its place. Persist your cursor/timestamp in state, and make your runs idempotent by relying on deterministic STIX IDs.

Connectors can persist state between runs to track progress.

### Getting Current State

```python
current_state = self.helper.get_state()

if current_state is None:
    # First run
    current_state = {"last_run": None}
```

### Updating State

```python
from datetime import datetime, timezone

now = datetime.now(timezone.utc)
current_timestamp = int(now.timestamp())

# Update state
new_state = {
    "last_run": now.strftime("%Y-%m-%d %H:%M:%S"),
    "last_timestamp": current_timestamp,
    "items_processed": 42,
}

self.helper.set_state(new_state)
```

### State Use Cases

- **Last run timestamp** - For incremental imports
- **Cursor/pagination** - Resume from last position
- **Processing markers** - Track what's been processed
- **Rate limit tracking** - Monitor API usage

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

## Code style: black, flake8, isort

The connector ecosystem standardizes on these. Run them before every commit:

```bash
isort .          # import ordering
black .          # formatting
flake8 .         # linting
```

Don't argue with the formatter. `black` is opinionated on purpose; consistent formatting removes a whole category of review comments. Configure all three in `pyproject.toml`/`setup.cfg` so everyone uses the same rules.
In the resources file, you'll find a list of connectors that are good examples of the above principles.

## Mini lab: apply formatting and fix a bad error handler

- Go to your connectors' repo and run `isort`, `black`, and `flake8`. Fix any issues until they all pass.
- The formatter and linter should be run at the root of the connectors repository, not inside the connector folder.

```shell
# Check formatting and linting from root of connectors repo

# Run black check
black --check <path/to/folder>

# Run isort check
isort --profile black --skip-glob '*venv*' --check <path/to/folder>

# Run flake8 check
flake8 --exclude=venv* <path/to/folder>

```

Your tasks:

- Run `isort`, `black`, and `flake8` and make them pass.
- Rewrite the error handler so failures are caught at the right granularity, logged with context, surfaced on the work, and non-fatal to the run loop.

A reference fix is in the same folder, try it yourself first.

---

Next: [Module 4 - Testing and Debugging](04-testing-debugging.md)
