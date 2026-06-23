# Module 2 - Deep Dive: Building a Connector

**Time:** 10:40 - 12:30 (lecture ~30 min, lab ~80 min)
**Goal:** understand the connector lifecycle, then build a minimal working connector.

## OpenCTIConnectorHelper

`OpenCTIConnectorHelper` (from `pycti`) is the object that wires your connector to the platform and the message queue. It reads configuration, registers the connector, gives you a logger, and exposes the methods you use to initiate work and send bundles.

You construct it from a config dictionary (typically loaded from `config.yml` and environment variables):

```python
from pycti import OpenCTIConnectorHelper

helper = OpenCTIConnectorHelper(config)
```

The helper handles registration with the platform automatically. What you write is the logic in between.

## Self-triggered vs. platform-triggered

This distinction drives the entire shape of your code.

**Self-triggered (EXTERNAL_IMPORT).** Your connector runs a loop. On each iteration it decides whether enough time has passed (based on its interval and stored state), and if so, it does a run: fetch from the source, build STIX, send it. You drive the schedule.

```python
def run(self):
    self.helper.schedule_iso(
        message_callback=self.process,
        duration_period="PT24H",  # ISO-8601 duration
    )
```

**Platform-triggered (INTERNAL_ENRICHMENT).** Your connector listens. The platform invokes it with a message when a user (or a rule) requests enrichment of a specific entity. You react to that message.

```python
def run(self):
    self.helper.listen(message_callback=self.process_message)
```

In both cases the callback is where your real work happens.

## Work initiation, state, and avoiding duplicates

**Work initiation.** Before sending data, open a "work" so the platform can track the ingestion as a unit and surface progress and errors in the UI:

```python
work_id = self.helper.api.work.initiate_work(
    self.helper.connect_id, "Fetching latest feed"
)
# ... send bundle(s) with this work_id ...
self.helper.api.work.to_processed(work_id, "Done")
```

**State management.** The helper persists a small JSON state for you. Use it to remember where you left off (last run timestamp, last seen cursor) so you only fetch new data:

```python
state = self.helper.get_state() or {}
last_run = state.get("last_run")
# ... do work ...
self.helper.set_state({"last_run": now})
```

**Avoiding duplicates.** Largely free if you do two things: rely on STIX deterministic IDs (don't invent random IDs for the same logical entity), and use state to avoid re-fetching the same window. The workers deduplicate on ID, so a stable ID for "the same thing" means re-sending it updates rather than duplicates.

## Constructing STIX 2.1 bundles and the callback deep dive

Inside your callback:

1. **Fetch / receive.** Pull from the source (import) or read the entity from the message (enrichment).
2. **Build STIX objects.** Use the `stix2` library to create SDOs/SCOs/SROs. Set deterministic IDs, attach the author identity and marking definitions.
3. **Bundle.** Collect objects into a list.
4. **Send.** Serialize and send via the helper:

```python
bundle = self.helper.stix2_create_bundle(stix_objects)
self.helper.send_stix2_bundle(bundle, work_id=work_id)
```

> **On `cleanup_inconsistent_bundle`:** it defaults to `False` because many connectors intentionally ship partial bundles. If you enable it, your bundle must include every referenced object: marking definitions, the author identity, and all base marking options. A `MISSING_REFERENCE_ERROR` usually means a malformed/incomplete bundle, or that the connector lacks rights to create foundational objects, check both.

For enrichment, the callback receives the entity to enrich. You read it, fetch context from your service, build the new objects and relationships, and send them back attached to that entity.

## Hands-on lab

Let's build a minimal working connector together.
We will implement without AI assistance to understand the full workflow and connector lifecycle. Of course, you can use AI to help you create new ones later, but you should understand the underlying concepts first.

### Before you start

Ensure you have completed the prerequisites and pre-check sign-off. You should have a working OpenCTI instance, an API token, and a cloned copy of this repo.

You must be aligned with connectors master branch. If you have a fork, make sure it is up to date:

```bash
# Update your fork and then update local master branch
git pull origin master
```

Create a new branch in your fork of the `connectors` repo. You will be committing your work there.

```bash
git checkout -b <your-branch-name>

# or
git switch -c <your-branch-name>
```

### Step 1: Open the connector repository

You should have cloned the `connectors` repo in the prerequisites. Open it in your code editor.

You will a have all of our connectors listed.

What interest you is the `templates` folder. Inside, you will find a connector template for each type. Open the `EXTERNAL_IMPORT` template.

#### File Descriptions

| File/Directory                       | Purpose                                                   |
| ------------------------------------ | --------------------------------------------------------- |
| `__metadata__/`                      | Contains metadata for connector catalog and documentation |
| `connector_manifest.json`            | Connector information, version, capabilities              |
| `src/connector/connector.py`         | Main connector logic and processing                       |
| `src/connector/converter_to_stix.py` | STIX object creation and conversion                       |
| `src/connector/settings.py`          | Configuration models with Pydantic validation             |
| `src/connector/utils.py`             | Utility functions and helpers                             |
| `src/template_client/api_client.py`        | External API client implementation                        |
| `src/main.py`                        | Entry point, initializes connector                        |
| `tests/`                             | Unit and integration tests                                |
| `config.yml.sample`                  | Sample configuration for users                            |
| `Dockerfile`                         | Container image definition                                |
| `docker-compose.yml`                 | Docker Compose service definition                         |

### Step 2: Create a new connector directory

The fastest way to start is using the provided script in the templates folder. It will copy the template and rename it for you.

```bash
cd templates
sh create_connector_dir.sh -t <TYPE> -n <NAME>
```

![Creating connector image](../docs/media/create-connector.png)

It will create a new directory in the `connectors` folder with the name you provided, and copy the template files into it (as it is `EXTERNAL_IMPORT` connector, you should find in the `external-import` folder). You can now open this new directory in your code editor.

![Connector directory structure](../docs/media/connector-created.png)

It can take few minutes to rename all the files and update the imports. Once done, you can start editing your connector.

If your connector has hyphens in its name, the script will convert them to underscores for the settings.

Please check the config.yml file created to ensure everything is correct.

### Step 4: Install dependencies

Go to your connector directory and install the dependencies in a virtual environment (using pip or uv):

```bash
# Create a virtual environment
python3 -m venv venv
source venv/Scripts/activate

# Check what environment you are using
which python

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Generate an API Token

If you are using your own OpenCTI instance, you can create a new Token and paste it in the `config.yml` file in `token` field.

If you are using the shared lab instance, on OpenCTI:

- Go to `Settings > Security > Users` and create a new user for your connector and register in `Workshop-Group`.

![Workshop group](../docs/media/workshop-group.png)

- Log out and connect with the new user to generate a token in `Profile > API Access`.
- Copy the token and paste it in the `config.yml` file.

If you are using the shared lab instance, you can also use the token provided for the prerequisites.

### Step 6: Register the connector in the platform

Go back to your connector directory and edit the `config.yml` file:

- Add your OpenCTI URL (the lab instance URL) and the API token you generated.
- Change the id of the connector to a unique value (e.g. `my-connector-custom`). It will create a unique queue for your connector in RabbitMQ.
- Change the name of the connector in the `config.yml` file to something unique (e.g. `my-connector-custom`).
- Change the scope `vulnerability,ip-addr,software`. The `scope` parameter in OpenCTI connectors defines **what the connector handles**. Its behavior depends on the connector type. **Scope never filters the bundle content.** It only controls **when/how the platform triggers the connector**.
- Change `duration_period` to a longer interval (e.g. `PT10M`) for testing purposes.

You can now run the connector and check that it registers in the platform. You should see it in the connectors list.

```bash
python3 src/main.py

#or using uv
uv run --active src/main.py
```

You will have a bunch of errors in the logs, but the connector should be registered and appear in the platform.

Let's check in the UI in `Data > Ingestion > Monitoring`.

### Step 7: Implement the connector settings

- Copy paste the `sample` folder in which you will find samples of API responses to use for testing. You will find Domains, IPs, and Vulnerabilities samples. You can use them to test your connector without calling the API.

Once done, let's explore `settings.py`.

<details>
<summary> DETAILS ON SETTINGS </summary>

This defines the configuration schema for an OpenCTI external import connector using the `connectors_sdk` and Pydantic.

**`ExternalImportConnectorConfig`** extends the SDK's base class for `EXTERNAL_IMPORT` connectors. It overrides two fields:

- `name` — the connector's display name, defaulting to `"WorkshopFeedConnectorConnector"`.
- `duration_period` — a `timedelta` controlling how long the connector waits between runs, defaulting to 1 hour. Pydantic parses ISO 8601 duration strings (e.g. `PT2H`) into a `timedelta` here.

**`WorkshopFeedConnectorConfig`** holds the settings specific to this connector's data source:

- `api_base_url` — typed as `HttpUrl`, so Pydantic validates it is a well-formed URL.
- `api_key` — the authentication secret (no default, so it is required).
- `tlp_level` — restricted by `Literal` to the allowed Traffic Light Protocol values, defaulting to `"clear"`. This sets the marking applied to imported entities.

**`ConnectorSettings`** is the top-level config object. It overrides the SDK's `BaseConnectorSettings` to wire in the two config classes above as nested sections:

- `connector` → the generic connector behavior.
- `workshop_feed_connector` → the feed-specific parameters.

Both use `default_factory`, meaning Pydantic instantiates each sub-model automatically, pulling values from the environment (the SDK typically maps `WORKSHOP_FEED_CONNECTOR_API_KEY`, `CONNECTOR_NAME`, etc.). Fields without defaults (like `api_key` and `api_base_url`) must be supplied, or validation fails at startup.

The overall pattern separates SDK-provided defaults from your connector's custom requirements, giving you type-checked, validated configuration loaded from environment variables.

The attributes defined must be written similiarly in the `config.yml` file. If you add a new attribute in the settings, you must add it in the `config.yml` file. As well in the docker-compose.yml file to build the docker image properly.
</details>
</br>

- Where is it instantiated? In `main.py` when the helper is created. The helper reads the config from the environment and validates it against this schema. You can add a debug breakpoint to inspect the object and see the values.

### Step 8: Update settings

- Let's change a configuration parameter in the `config.yml` file and see how it is reflected in the logs when we run the connector.
- Remove `api_base_url` and `api_key` from the `config.yml` file and run the connector. You should see a validation error in the logs.
- Remove from `settings.py` the `api_base_url` and `api_key` attributes and run the connector. You should see a validation error in the logs.

Errors are clear and tell you exactly what is wrong.

- Now remove it completely where it is used: `<template_client>/api_client.py`, `connector/connector.py`, and `docker-compose.yml`.

<details>
<summary> DETAILS ON `api_client.py` </summary>

```python
import requests
from pycti import OpenCTIConnectorHelper
from pydantic import HttpUrl


class WorkshopFeedConnectorClient:
    def __init__(self, helper: OpenCTIConnectorHelper):
        # REMOVED PARAMETERS ==============================
        """
        Initialize the client with necessary configuration.
        For log purpose, the connector's helper CAN be injected.
        Other arguments CAN be added (e.g. `api_key`) if necessary.

        Args:
            helper (OpenCTIConnectorHelper): The helper of the connector. Used for logs.

        =========REMOVED HERE=================

        """
        self.helper = helper

        # REMOVED HERE

    def _request_data(self, api_url: str, params=None):
        """
        Internal method to handle API requests
        :return: Response in JSON format
        """
        try:
            response = self.session.get(api_url, params=params)

            self.helper.connector_logger.info(
                "[API] HTTP Get Request to endpoint", {"url_path": api_url}
            )

            response.raise_for_status()
            return response

        except requests.RequestException as err:
            error_msg = "[API] Error while fetching data: "
            self.helper.connector_logger.error(
                error_msg, {"url_path": {api_url}, "error": {str(err)}}
            )
            return None

    def get_entities(self, params=None) -> dict:
        """
        If params is None, retrieve all CVEs in National Vulnerability Database
        :param params: Optional Params to filter what list to return
        :return: A list of dicts of the complete collection of CVE from NVD
        """
        try:
            # ===========================
            # === Add your code below ===
            # ===========================

            # response = self._request_data() # REMOVED HERE

            # return response.json()
            # ===========================
            # === Add your code above ===
            # ===========================

            raise NotImplementedError

        except Exception as err:
            self.helper.connector_logger.error(err)

```

</details>

<details>
<summary> DETAILS ON `connector.py` </summary>

```python
import sys
from datetime import datetime, timezone

from connector.converter_to_stix import ConverterToStix
from connector.settings import ConnectorSettings
from pycti import OpenCTIConnectorHelper
from workshop_feed_connector_client import WorkshopFeedConnectorClient


class WorkshopFeedConnectorConnector:
    """
    ...
    """

    def __init__(self, config: ConnectorSettings, helper: OpenCTIConnectorHelper):
        """
        ...
        """
        self.config = config
        self.helper = helper

        self.client = WorkshopFeedConnectorClient(
            self.helper,
            # REMOVED HERE =======================================
            # Pass any arguments necessary to the client
        )
        self.converter_to_stix = ConverterToStix(
            self.helper,
            tlp_level=self.config.workshop_feed_connector.tlp_level,
            # Pass any arguments necessary to the converter
        )

    [...]
```

</details>
</br>

- Run the connector, you shouldn't see validation errors in the logs. The connector should register in the platform.

> [!NOTE]
> You will still get an error on the logs because the `get_entities` method is not implemented yet. You will implement it in the next step.

- Let's add a new attribute in the settings. For example, add a new attribute `sample_file_path` in the `WorkshopFeedConnectorConfig` class. Add it in the `config.yml` file and in the `docker-compose.yml` file.

In config.yml:

```yaml
workshop_feed_connector:
  sample_file_path: '../samples' # Add it here
  tlp_level: 'clear' # available values: 'clear', 'white', 'green', 'amber', 'amber+strict', 'red' (default: 'clear')
```

In settings.py:

```python
class WorkshopFeedConnectorConfig(BaseConfigModel):
    """
    Define parameters and/or defaults for the configuration specific to the `WorkshopFeedConnectorConnector`.
    """
    sample_file_path: str = Field(description="File path to samples.")
    tlp_level: Literal[
        "clear",
        "white",
        "green",
        "amber",
        "amber+strict",
        "red",
    ] = Field(
        description="Default TLP level of the imported entities.",
        default="clear",
    )
```

In docker-compose.yml:

```yaml
      - WORKSHOP_CONNECTOR_SAMPLE_FILE_PATH=../samples # Add it here
```

- Add the same breakpoint in the `main.py` file and run the connector. You should see the new attribute in the settings object.

![Connector settings with new attribute](../docs/media/connector-settings.png)

- The tests in the template are already implemented to test the settings. You can run them and see that they do not pass.

To run tests, you can use the following commands:

```bash
# Install tests requirements
pip install -r tests/requirements.txt

# or using uv
uv pip install -r tests/test-requirements.txt

# Run tests in the folder
pytest -vv
```

We will update it in the module 4 to make them pass.

### Step 9: Implement the "client" to fetch data from the source

- We will use our brand new settings attribute `sample_file_path` to read the samples from the `samples` folder.

- Add in `__init__` of `WorkshopFeedConnectorClient` class the following code:

```python
    def __init__(self, helper: OpenCTIConnectorHelper, sample_file_path: str):
        """
        ...
        """
        self.helper = helper

        self.sample_file_path = sample_file_path
        self.domain_path = "/domains_sample.json"
        self.ip_addresses_path = "/ip_addresses_sample.json"
        self.vulnerabilities_path = "/vulnerabilities_sample.json"
```

- Let's basically implement a method to read the samples from the `samples` folder. Add the following code in the `WorkshopFeedConnectorClient` class:

```python
    def _from_json(self, sample_file_path: str) -> dict:
        with open(sample_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
```

- Update `_request_data` method and add for each entity type their own method
  
```python
    def _from_json(self, sample_file_path: str) -> dict:
        with open(sample_file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _request_data(self, sample_file_path: str):
        """
        Internal method to handle API requests
        :return: Response in JSON format
        """
        try:
            response = self._from_json(sample_file_path)
            return response

        except requests.RequestException as err:
            error_msg = "[API] Error while fetching data: "
            self.helper.connector_logger.error(
                error_msg, {"url_path": {sample_file_path}, "error": {str(err)}}
            )
            return None

    def get_domain_entities(self) -> dict:
        """
        If params is None, retrieve all CVEs in National Vulnerability Database
        :param params: Optional Params to filter what list to return
        :return: A list of dicts of the complete collection of CVE from NVD
        """
        try:
            # ===========================
            # === Add your code below ===
            # ===========================

            response = self._request_data(self.sample_file_path + self.domain_path)

            return response
            # ===========================
            # === Add your code above ===
            # ===========================

            # raise NotImplementedError

        except Exception as err:
            self.helper.connector_logger.error(err)

    def get_ip_entities(self) -> dict:
        """
        If params is None, retrieve all CVEs in National Vulnerability Database
        :param params: Optional Params to filter what list to return
        :return: A list of dicts of the complete collection of CVE from NVD
        """
        try:
            # ===========================
            # === Add your code below ===
            # ===========================

            response = self._request_data(
                self.sample_file_path + self.ip_addresses_path
            )

            return response
            # ===========================
            # === Add your code above ===
            # ===========================

            # raise NotImplementedError

        except Exception as err:
            self.helper.connector_logger.error(err)

    def get_vulnerability_entities(self) -> dict:
        """
        If params is None, retrieve all CVEs in National Vulnerability Database
        :param params: Optional Params to filter what list to return
        :return: A list of dicts of the complete collection of CVE from NVD
        """
        try:
            # ===========================
            # === Add your code below ===
            # ===========================

            response = self._request_data(
                self.sample_file_path + self.vulnerabilities_path
            )

            return response
            # ===========================
            # === Add your code above ===
            # ===========================

            # raise NotImplementedError

        except Exception as err:
            self.helper.connector_logger.error(err)
```

<details>
<summary> COMPLETE `api_client.py` CODE DETAILS </summary>

```python
import json

import requests
from pycti import OpenCTIConnectorHelper


class WorkshopConnectorClient:
    def __init__(self, helper: OpenCTIConnectorHelper, sample_file_path: str):
        """
        Initialize the client with necessary configuration.
        For log purpose, the connector's helper CAN be injected.
        Other arguments CAN be added (e.g. `api_key`) if necessary.

        Args:
            helper (OpenCTIConnectorHelper): The helper of the connector. Used for logs.
        """
        self.helper = helper

        self.sample_file_path = sample_file_path
        self.domain_path = "/domains_sample.json"
        self.ip_addresses_path = "/ip_addresses_sample.json"
        self.vulnerabilities_path = "/vulnerabilities_sample.json"

    def _from_json(self, sample_file_path: str) -> dict:
        with open(sample_file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _request_data(self, sample_file_path: str):
        """
        Internal method to handle API requests
        :return: Response in JSON format
        """
        try:
            response = self._from_json(sample_file_path)
            return response

        except requests.RequestException as err:
            error_msg = "[API] Error while fetching data: "
            self.helper.connector_logger.error(
                error_msg, {"url_path": {sample_file_path}, "error": {str(err)}}
            )
            return None

    def get_domain_entities(self) -> dict:
        """
        If params is None, retrieve all CVEs in National Vulnerability Database
        :param params: Optional Params to filter what list to return
        :return: A list of dicts of the complete collection of CVE from NVD
        """
        try:
            # ===========================
            # === Add your code below ===
            # ===========================

            response = self._request_data(self.sample_file_path + self.domain_path)

            return response
            # ===========================
            # === Add your code above ===
            # ===========================

            # raise NotImplementedError

        except Exception as err:
            self.helper.connector_logger.error(err)

    def get_ip_entities(self) -> dict:
        """
        If params is None, retrieve all CVEs in National Vulnerability Database
        :param params: Optional Params to filter what list to return
        :return: A list of dicts of the complete collection of CVE from NVD
        """
        try:
            # ===========================
            # === Add your code below ===
            # ===========================

            response = self._request_data(
                self.sample_file_path + self.ip_addresses_path
            )

            return response
            # ===========================
            # === Add your code above ===
            # ===========================

            # raise NotImplementedError

        except Exception as err:
            self.helper.connector_logger.error(err)

    def get_vulnerability_entities(self) -> dict:
        """
        If params is None, retrieve all CVEs in National Vulnerability Database
        :param params: Optional Params to filter what list to return
        :return: A list of dicts of the complete collection of CVE from NVD
        """
        try:
            # ===========================
            # === Add your code below ===
            # ===========================

            response = self._request_data(
                self.sample_file_path + self.vulnerabilities_path
            )

            return response
            # ===========================
            # === Add your code above ===
            # ===========================

            # raise NotImplementedError

        except Exception as err:
            self.helper.connector_logger.error(err)

```

</details>
</br>

- Remove unnecessary imports
- As `WorkshopFeedConnectorClient` is instantiated in the `WorkshopFeedConnectorConnector` class, you need to pass the `sample_file_path` attribute from the settings to the client. Update the `__init__` method of the `WorkshopFeedConnectorConnector` class in `connector.py`:

```python
    def __init__(self, config: ConnectorSettings, helper: OpenCTIConnectorHelper):
        """
        ...
        """
        self.config = config
        self.helper = helper

        self.client = WorkshopFeedConnectorClient(
            self.helper,
            self.config.workshop_feed_connector.sample_file_path,
            # Pass any arguments necessary to the client
        )
```

### Step 10: Collect intelligence at regular intervals

Before implementing the intelligence collection, let's check the `run` method in the `WorkshopFeedConnectorConnector` class. It is already implemented to run at regular intervals based on the `duration_period` attribute in the settings.

```python
    def run(self) -> None:
        self.helper.schedule_process(
            message_callback=self.process_message,
            duration_period=self.config.connector.duration_period.total_seconds(),
        )
```

This is an essential part of `EXTERNAL_IMPORT` connectors. And let's details a bit about [Auto backpressure, Scheduling and Execution flow](https://github.com/OpenCTI-Platform/connectors/blob/master/docs/02-external-import-specifications.md#auto-backpressure-scheduling-and-execution)

Implementing it helps to avoid overloading the platform with too many messages at once. The helper will automatically manage the scheduling and execution of the connector's processing logic, ensuring that it runs at the specified intervals without overwhelming the system. And for that, the connector can be in an `idle` state or `buffering` mode or let's say `pause` to let workers consume the messages in the queue.

When the connector is in a buffering state, it will wait until the platform is ready to accept new messages before proceeding with the next batch of data. This ensures that the connector operates efficiently.

The core behavior of an `EXTERNAL_IMPORT` connector is to fetch data from an external source at regular intervals, process it, and send it to the OpenCTI platform. The queue control and scheduling mechanism provided by the helper ensures that this process is smooth and does not overwhelm the platform. Think it like a controlled ETL (Extract, Transform, Load) process.

Let's get all entities needed before converting it into STIX data for OpenCTI.

- Remove the code between comments `# === Add your code below ===` and `# === Add your code above ===`
- Add the following code to fetch all entities from the samples folder:

```python
    # Get entities from external sources
    domain_entities = self.client.get_domain_entities()
    ip_entities = self.client.get_ip_entities()
    vulnerability_entities = self.client.get_vulnerability_entities()
```

- Let's add a breakpoint and run the connector. You should see all entities fetched from the samples folder.

Result
![Entities fetched from samples folder](../docs/media/entities-fetched.png)

- Continue, you will see that the connector won't crash anymore, but it will still not send any data to the platform. You will implement the conversion to STIX in the next step.

### Step 11: Transform intelligence

Now that you have fetched the entities from the samples folder, you need to convert them into STIX format before sending them to OpenCTI. This is done in the `ConverterToStix` class.

- Let's add a new method called `_transform_intelligence` in the `WorkshopFeedConnectorConnector` class. This method will take the fetched entities and convert them into STIX objects using the `ConverterToStix` class.

- First, add in `_collect_intelligence` method the following code to convert the fetched entities into STIX objects:

```python
        # Convert into STIX2 object and add it on a list
        stix_domain_entities = self._transform_intelligence(domain_entities["response"])
        stix_ip_entities = self._transform_intelligence(ip_entities["response"])
        stix_vulnerability_entities = self._transform_intelligence(
            vulnerability_entities["response"]
        )

```

- Create the `_transform_intelligence` method in the `WorkshopFeedConnectorConnector` class.

We want this method parse the entities and convert them into STIX objects. For each entity type, we will use the appropriate method from the `ConverterToStix` class to create the STIX objects.

<details>
<summary> COMPLETE `_transform_intelligence` CODE DETAILS </summary>

```python
    def _transform_intelligence(self, entities):
        stix_entities = []
        stix_relationships = []
        for entity in entities:
            if entity["type"] == "ip_address":
                stix_entities.append(self.converter_to_stix.create_obs(entity["id"]))

            if entity["type"] == "domain":
                stix_entities.append(self.converter_to_stix.create_obs(entity["id"]))

            if entity["type"] == "vulnerability":
                # Transform vulnerability
                vulnerability = {
                    "name": entity["attributes"]["name"],
                    "tags": entity["attributes"]["tags"],
                    "description": entity["attributes"]["description"],
                    "epss_score": entity["attributes"]["epss"]["score"],
                    "epss_percentile": entity["attributes"]["epss"]["percentile"],
                    "cvss_v3_vector_string": entity["attributes"]["cvss"]["cvssv3_x"][
                        "vector"
                    ],
                    "cvss_v3_base_score": entity["attributes"]["cvss"]["cvssv3_x"][
                        "base_score"
                    ],
                    "cvss_v4_vector_string": entity["attributes"]["cvss"]["cvssv4_0"][
                        "vector"
                    ],
                    "cvss_v4_base_score": entity["attributes"]["cvss"]["cvssv4_0"][
                        "base_score"
                    ],
                }
                stix_vulnerability = self.converter_to_stix.create_vulnerability(
                    vulnerability
                )
                stix_entities.append(stix_vulnerability)

                # Create and transform related CPEs
                affected_software = entity["attributes"]["cpes"]

                for software in affected_software:
                    software_details = {
                        "name": software["product"],
                        "cpe": software["uri"],
                        "vendor": software["vendor"],
                        "version": software["version"],
                    }
                    stix_software = self.converter_to_stix.create_software(
                        software_details
                    )

                    # Create relationship STIX object
                    software_has_vulnerability = (
                        self.converter_to_stix.create_relationship(
                            source=stix_software,
                            relationship_type="has",
                            target=stix_vulnerability,
                        )
                    )

                    stix_entities.append(stix_software)
                    stix_relationships.append(software_has_vulnerability)

        return stix_entities + stix_relationships

```

</details>
</br>

- In the response, we can find the type of the entity. For each type, we will call the appropriate method from the `ConverterToStix` class to create the STIX object.

>[!NOTE]
> Note that the response will vary depending on the data source you are using. You will need to adapt the code to match the structure of the response from your specific data source.

### Step 12: Deep dive into the STIX conversion

In the `converter_to_stix.py` file, you will find the methods to create STIX objects. You can use them to create STIX objects from the fetched entities.

You'll see here an example of how to implement it using `stix2` library.

Remember that we want to convert data into STIX format before sending it to OpenCTI as a bundle to be consumed by the platform.

We don't want to write by calling the OpenCTI API directly, but rather to create a STIX bundle and send it to OpenCTI. The platform will then process the bundle and create the appropriate entities and relationships in the platform and have a proper tracking of the number of entities expected to be created and the number of entities actually created.

- Go to `converter_to_stix.py` and implement the methods to create STIX objects for each entity type. You can use the `stix2` library to create the STIX objects and we can see later the `connectors_sdk` usage.

- When importing data, we want to specify where it comes from. Check the `create_author` method in the `ConverterToStix` class. It creates an `Identity` STIX object representing the source of the data. You can use it to create an author for your connector.

- We also want to specify the marking of the data. Check the `_create_tlp_marking` method in the `ConverterToStix` class. It creates a `MarkingDefinition` STIX object representing the TLP level of the data. You can use it to create a marking for data.

- What is also relevant is when we can create relationships between STIX objects. Check the `create_relationship` method in the `ConverterToStix` class. It creates a `Relationship` STIX object representing a relationship between two STIX objects. You can use it to create relationships between STIX objects.

- Our samples contain:
  - Domains
  - IPs
  - Vulnerabilities and related CPEs

- You can use the `create_obs` method to create STIX objects for Domains and IPs. We will create a `create_vulnerability` method to create STIX objects for Vulnerabilities. And create a `create_software` method to create STIX objects for CPEs. You can use the `create_relationship` method to create relationships between Vulnerabilities and CPEs.

- Copy paste the code below in the `converter_to_stix.py` file to implement the methods to create STIX objects for each entity type to get you started. You can modify it later, you get the idea of how to implement it then we can walk through it together.

<details>
<summary> COPY PASTE - COMPLETE `converter_to_stix.py` CODE DETAILS</summary>

```python
import ipaddress
from typing import Literal

import stix2
import validators

# from connectors_sdk.models import DomainName  # noqa: F401
# from connectors_sdk.models import IPV4Address  # noqa: F401
# from connectors_sdk.models import Relationship  # noqa: F401
# from connectors_sdk.models import Software  # noqa: F401
# from connectors_sdk.models import TLPMarking  # noqa: F401
from connectors_sdk.models import (
    OrganizationAuthor,
)

# from connectors_sdk.models import Vulnerability as SDKVulnerability  # noqa: F401
from pycti import (
    Identity,
    MarkingDefinition,
    OpenCTIConnectorHelper,
    StixCoreRelationship,
    Vulnerability,
)


class ConverterToStix:
    """
    Provides methods for converting various types of input data into STIX 2.1 objects.

    REQUIREMENTS:
        - `generate_id()` methods from `pycti` library MUST be used to generate the `id` of each entity (except observables),
        e.g. `pycti.Identity.generate_id(name="Source Name", identity_class="organization")` for a STIX Identity.
    """

    def __init__(
        self,
        helper: OpenCTIConnectorHelper,
        tlp_level: Literal["clear", "white", "green", "amber", "amber+strict", "red"],
    ):
        """
        Initialize the converter with necessary configuration.
        For log purpose, the connector's helper CAN be injected.
        Other arguments CAN be added (e.g. `tlp_level`) if necessary.

        Args:
            helper (OpenCTIConnectorHelper): The helper of the connector. Used for logs.
            tlp_level (str): The TLP level to add to the created STIX entities.
        """
        self.helper = helper

        self.author = self.create_author()
        self.tlp_marking = self._create_tlp_marking(level=tlp_level.lower())

    @staticmethod
    def create_author() -> dict | OrganizationAuthor:
        """
        Create Author
        :return: Author in Stix2 object
        """
        stix2_author = stix2.Identity(
            id=Identity.generate_id(name="WORKSHOP", identity_class="organization"),
            name="WORKSHOP",
            identity_class="organization",
            description="Workshop purpose.",
            external_references=[
                stix2.ExternalReference(
                    source_name="External Source",
                    url="CHANGEME",
                    description="DESCRIPTION",
                )
            ],
        )

        # Or using connectors-sdk
        # sdk_author = OrganizationAuthor(
        #     name="Workshop Author",
        #     description="Workshop purpose."
        # )
        # return sdk_author.to_stix2_object()

        return stix2_author

    @staticmethod
    def _create_tlp_marking(level):
        # Marking definition using Stix2 Python library
        mapping = {
            "white": stix2.TLP_WHITE,
            "clear": stix2.TLP_WHITE,
            "green": stix2.TLP_GREEN,
            "amber": stix2.TLP_AMBER,
            "amber+strict": stix2.MarkingDefinition(
                id=MarkingDefinition.generate_id("TLP", "TLP:AMBER+STRICT"),
                definition_type="statement",
                definition={"statement": "custom"},
                custom_properties={
                    "x_opencti_definition_type": "TLP",
                    "x_opencti_definition": "TLP:AMBER+STRICT",
                },
            ),
            "red": stix2.TLP_RED,
        }

        # Or using connectors-sdk
        # sdk_tlp_marking = TLPMarking(level=level)
        # return sdk_tlp_marking.to_stix2_object()

        return mapping[level]

    def create_relationship(
        self, source: str, relationship_type: str, target: str
    ) -> dict:
        """
        Creates Relationship object
        :param source: Source in string
        :param relationship_type: Relationship type in string
        :param target: Target in string
        :return: Relationship STIX2 object
        """
        relationship = stix2.Relationship(
            id=StixCoreRelationship.generate_id(
                relationship_type, source.id, target.id
            ),
            relationship_type=relationship_type,
            source_ref=source.id,
            target_ref=target.id,
            created_by_ref=self.author["id"],
        )

        # Or using connectors-sdk example
        # sdk_stix_relationship = Relationship(
        #     source=source,
        #     type=relationship_type,
        #     target=target
        # )
        # return sdk_stix_relationship.to_stix2_object()

        return relationship

    # ===========================#
    # Other Examples
    # ===========================#

    @staticmethod
    def _is_ipv6(value: str) -> bool:
        """
        Determine whether the provided IP string is IPv6
        :param value: Value in string
        :return: A boolean
        """
        try:
            ipaddress.IPv6Address(value)
            return True
        except ipaddress.AddressValueError:
            return False

    @staticmethod
    def _is_ipv4(value: str) -> bool:
        """
        Determine whether the provided IP string is IPv4
        :param value: Value in string
        :return: A boolean
        """
        try:
            ipaddress.IPv4Address(value)
            return True
        except ipaddress.AddressValueError:
            return False

    @staticmethod
    def _is_domain(value: str) -> bool:
        """
        Valid domain name regex including internationalized domain name
        :param value: Value in string
        :return: A boolean
        """
        is_valid_domain = validators.domain(value)

        if is_valid_domain:
            return True
        else:
            return False

    def create_obs(self, value: str) -> dict:
        """
        Create observable according to value given
        :param value: Value in string
        :return: Stix object for IPV4, IPV6 or Domain
        """
        if self._is_ipv6(value) is True:
            stix_ipv6_address = stix2.IPv6Address(
                value=value,
                custom_properties={
                    "x_opencti_created_by_ref": self.author["id"],
                },
            )
            return stix_ipv6_address
        elif self._is_ipv4(value) is True:
            stix_ipv4_address = stix2.IPv4Address(
                value=value,
                custom_properties={
                    "x_opencti_created_by_ref": self.author["id"],
                },
            )

            # Or using connectors-sdk example
            # sdk_stix_ipv4 = IPV4Address(value=value, author=self.author)
            # return sdk_stix_ipv4.to_stix2_object()

            return stix_ipv4_address
        elif self._is_domain(value) is True:
            stix_domain_name = stix2.DomainName(
                value=value,
                custom_properties={
                    "x_opencti_created_by_ref": self.author["id"],
                },
            )

            # Or using connectors-sdk example
            # sdk_stix_domain = DomainName(value=value, author=self.author)
            # return sdk_stix_domain.to_stix2_object()

            return stix_domain_name
        else:
            self.helper.connector_logger.error(
                "This observable value is not a valid IPv4 or IPv6 address nor DomainName: ",
                {"value": value},
            )

    def create_vulnerability(self, vulnerability: dict) -> dict:
        """
        Create a STIX 2.1 Vulnerability object from vulnerability data.
        :param vulnerability: Dictionary containing vulnerability data
        :return: A STIX 2.1 Vulnerability object.
        """
        stix_vulnerability = stix2.Vulnerability(
            id=Vulnerability.generate_id(name=vulnerability["name"]),
            name=vulnerability["name"],
            object_marking_refs=[self.tlp_marking],
            custom_properties={
                "x_opencti_created_by": self.author["id"],
                "x_opencti_labels": vulnerability["tags"],
                "x_opencti_description": vulnerability["description"],
                "x_opencti_epss_score": vulnerability["epss_score"],
                "x_opencti_epss_percentile": vulnerability["epss_percentile"],
                # Cvss v3 (default on OpenCTI)
                "x_opencti_cvss_vector_string": vulnerability["cvss_v3_vector_string"],
                "x_opencti_cvss_base_score": vulnerability["cvss_v3_base_score"],
                # CVSS v4
                "x_opencti_cvss_v4_vector_string": vulnerability[
                    "cvss_v4_vector_string"
                ],
                "x_opencti_cvss_v4_base_score": vulnerability["cvss_v4_base_score"],
            },
        )

        # Or using connectors-sdk example
        # sdk_stix_vulnerability = SDKVulnerability(
        #         name=vulnerability["name"],
        #         description=vulnerability["description"],
        #         author=self.author,
        #         markings=[self.tlp_marking],
        #         epss_score=vulnerability["epss_score"],
        #         epss_percentile=vulnerability["epss_percentile"],
        #         cvss_v3_vector_string=vulnerability["cvss_v3_vector_string"],
        #         cvss_v3_base_score=vulnerability["cvss_v3_base_score"],
        #         cvss_v4_vector_string=vulnerability["cvss_v4_vector_string"],
        #         cvss_v4_base_score=vulnerability["cvss_v4_base_score"],
        #     )
        # return sdk_stix_vulnerability.to_stix2_object()

        return stix_vulnerability

    def create_software(self, software: dict) -> dict:
        """
        Create a STIX 2.1 Software object from software data.
        :param software: Dictionary containing software data
        :return: A STIX 2.1 Software object.
        """
        stix_software = stix2.Software(
            name=software["name"],
            cpe=software["cpe"],
            vendor=software["vendor"],
            version=software["version"],
        )

        # Or using connectors-sdk example
        # sdk_stix_software = Software(
        #     name=software["name"],
        #     cpe=software["cpe"],
        #     vendor=software["vendor"],
        #     version=software["version"],)
        # return sdk_stix_software.to_stix2_object()

        return stix_software

```

</details>
</br>

- There is a IP and domain validator in the `ConverterToStix` class. It will help you to validate if the value is a valid IP or domain before creating the STIX object.
- Let's check a bit in details the Vulnerability and Software STIX objects. The `create_vulnerability` method takes a dictionary containing vulnerability data and creates a STIX 2.1 Vulnerability object. The `create_software` method takes a dictionary containing software data and creates a STIX 2.1 Software object.
- For example vulnerability STIX object has the following fields that we want to populate from the data source:
  - id
  - name
  - tlp marking
  - author
  - labels
  - description
  - epss_score
  - epss_percentile
  - cvss_v3_vector_string
  - cvss_v3_base_score
  - cvss_v4_vector_string
  - cvss_v4_base_score

- When creating a STIX object, there is an important point to note. The `id` of the STIX object is generated using the `generate_id()` method from the `pycti` library. For details, check the [Data Deduplication Strategies on OpenCTI](https://github.com/OpenCTI-Platform/connectors/blob/master/docs/02-external-import-specifications.md#data-deduplication-strategies) section. It is important to use the `generate_id()` method to ensure that the `id` of the STIX object is unique and consistent across different runs of the connector and prevent duplicates.

- What is useful by using the `connectors_sdk` is that each model available interface with the OpenCTI API and will help you to create the STIX objects with exact available fields in OpenCTI. To avoid forget the deterministic ID generation, the `connectors_sdk` will generate it for you when calling the `to_stix2_object()` method. You can check the `connectors_sdk` models for example for a Vulnerability in the [connectors_sdk/models](https://github.com/OpenCTI-Platform/connectors/blob/master/connectors-sdk/connectors_sdk/models/vulnerability.py).

- Once you have all of your converters ready, let's go back to transform the fetched entities into STIX objects in the `_transform_intelligence` method in the `WorkshopFeedConnectorConnector` class.
- You can see clearly now the usage of it for each entity type. As well as the creation of relationships between Vulnerabilities and CPEs.
- Now, we need to return the list of STIX objects from the `_transform_intelligence` method. We will then send this list to OpenCTI in the next step.
- Complete the STIX object list in `_collect_intelligence` method by adding the following code:

```python
        # Complete STIX objects list
        stix_objects.extend(
            stix_domain_entities + stix_ip_entities + stix_vulnerability_entities
        )
```

- Let's check what inside the `stix_objects` list. You can add a breakpoint and run the connector. You should see all STIX objects created from the fetched entities.
- The template already return the stix_objects list from the `_collect_intelligence` method.

### Step 13: Send the STIX bundle to OpenCTI

Final step, we need to send the STIX bundle to OpenCTI. The `send_stix_bundle` method in the `WorkshopFeedConnectorConnector` class is already implemented to send the STIX bundle to OpenCTI.

- The `pycti` provides a helper that helps you to create a STIX bundle and send it to OpenCTI. The `send_stix_bundle` method takes a list of STIX objects and sends them to OpenCTI as a bundle.

>[!WARNING]
> If you are using your own local OpenCTI instance, you might have an issue with the connector when sending bundle to OpenCTI with a pika error. This is because the connector is trying to push to a queue in RabbitMQ, but the user is not in the same environment as the RabbitMQ user. You can fix this by following the instructions in the README of `octi-labs`.
>
> You have to add in your `hosts` system file the following line:
>
>```txt
>127.0.0.1   rabbitmq
>```
>
> For Windows, the file is located in `C:\Windows\System32\drivers\etc\hosts`. For Linux, it is located in `/etc/hosts`.
>
> If you are using the SaaS OpenCTI instance, you have to add in your configuration `queue_protocol='api'` just for demo purposes.
>

If you are using **API mode**, it can _look_ faster because the connector sends **one HTTP request** and returns quickly. But the platform still needs to do the same work (split + process), so **end-to-end ingestion is usually not faster**, and it can even be slower under load.  
  
**What you gain**  

- Easier deployment: only OpenCTI API URL + token
- Works when RabbitMQ is not reachable (network, security, proxy constraints)

**What you lose (main trade-offs)**  

- **No retry / no delivery guarantee**: if the GraphQL call fails, data can be lost (AMQP retries and uses persistent messages)
- **No expectations / weaker progress tracking**: UI completion % is not reliable, the bundle is sent as a single unsplit payload
- **Timeout risk on large bundles**: one big payload through GraphQL can hit HTTP or gateway timeouts, the platform itself handles splitting/processing server-side
- **More platform-side bottleneck risk**: splitting and processing happens server-side, potentially synchronously

**Recommendation**  

- Use **AMQP** for production and high-volume connectors.
- Use **API** mainly for PoCs, dev/test, very small payloads, or when RabbitMQ cannot be exposed.

### Step 14: Final step - Data in OpenCTI

- Now, you can check the data in OpenCTI. You should see the new entities created in OpenCTI. You can also check the relationships between Vulnerabilities and CPEs.
- Let's check our ingestion first, no errors, data ingested well

![Healthy ingestion](../docs/media/ingestion-healthy.png)

- Go to `Arsenal > Vulnerabilities` and check the new vulnerabilities created in OpenCTI.
- Checked the relationships between Vulnerabilities and CPEs.
- You can pivot to the CPEs and check the relationships between CPEs and Vulnerabilities.
- Go now check the Domains and IPs created in OpenCTI. You should see the new domains and IPs created in OpenCTI in `Observations > Observables`.

> [!NOTE]
> As everyone is using the same sample data, you might see the same entities created in OpenCTI. You can modify the sample data to create new entities.

### Success criteria

- The connector registers and appears in the platform's connectors list.
- It runs without exceptions.
- New entities appear in the platform (import) or new context attaches to the target entity (enrichment).
- You can see the work and its status in the UI.

---

Next: [Module 3 - Best Practices and Code Quality](03-best-practices.md)
