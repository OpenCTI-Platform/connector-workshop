# Module 1 - Foundations and Ecosystem

**Time:** 09:00 - 09:45
**Goal:** shared mental model of how OpenCTI ingests data and where connectors fit.

## Architecture refresher

OpenCTI is a graph-based threat intelligence platform. 

Architecture overview: [Link to architecture diagram](https://docs.opencti.io/latest/deployment/overview/)

The pieces you care about as a connector developer:

- **Platform (GraphQL API):** the brain. Stores entities and relationships, exposes a GraphQL API, and validates incoming data. Connectors talk to it through this API (via `pycti`).
- **Workers:** stateless processes that consume STIX bundles from the message queue and write them into the platform. They handle deduplication, retries, and the heavy lifting of ingestion. You scale throughput by adding workers, not by making your connector write faster.
- **RabbitMQ:** the message bus. Connectors push STIX bundles here; workers pull from here. This decoupling is what makes ingestion resilient, your connector can finish and disconnect while workers are still draining the queue.
- **Connectors:** the integration layer. They bring data in, enrich it, export it, or stream it. This is what you are building today.
  

```
[ Data source ] --> [ Connector ] --push STIX--> [ RabbitMQ ] --> [ Workers ] --> [ Platform / DB ]
```

The key takeaway: **a connector's job is to produce well-formed STIX and hand it off.** It does not write to the database directly, and it does not wait for ingestion to complete.

## What is a Connector?

Connectors are standalone Python applications that interact with OpenCTI through the platform's API and messaging infrastructure. They extend OpenCTI's capabilities by:

- Importing threat intelligence from external sources
- Enriching existing data with additional context
- Streaming events to external platforms in real-time
- Processing files for import/export operations

## Connector types and when to use which

| Type | Trigger | What it does | Use when |
|------|---------|--------------|----------|
| `EXTERNAL_IMPORT` | Self-triggered (interval) | Pulls data from an outside source and imports it on a schedule | You want to ingest a feed, API, or report source periodically(Threat feeds, OSINT sources, vendor APIs) |
| `INTERNAL_ENRICHMENT` | Platform-triggered (on an entity) | Takes an existing entity and adds context to it | You want to enrich observables/entities with data from a service (IP/domain reputation, vulnerability enrichment, entity analysis) |
| `INTERNAL_IMPORT_FILE` | Platform-triggered (on file upload) | Parses an uploaded file into STIX | You want users to drop a file and get entities |
| `INTERNAL_EXPORT_FILE` | Platform-triggered (on export) | Serializes platform data into a file format | You want to export entities to a custom format |
| `STREAM` | Live stream | Reacts to a live stream of platform events | You want to forward changes to an external system in near real-time (SIEM integration, ticketing systems, real-time synchronization) |

When you build a connector, you choose one of these types depending on your use case. Each type has its own lifecycle and interaction pattern with the platform.

Today's lab covers one of the most common starting points: **EXTERNAL_IMPORT** (pull a feed) and the second most used connector type, **INTERNAL_ENRICHMENT** (enrich an entity), won't be covered in detail, but you will have the key concepts to build a connector for it.

## STIX 2.1 primer

STIX 2.1 (Structured Threat Information Expression) is the data model OpenCTI speaks. Three concepts to internalize:

**Entities (SDOs / SCOs).** The nouns. Domain objects (SDOs) like `intrusion-set`, `malware`, `report`, `indicator`; and cyber observables (SCOs) like `ipv4-addr`, `domain-name`, `file`. Each has a deterministic ID derived from its defining properties, this is how OpenCTI deduplicates.

**Relationships (SROs).** The verbs connecting entities, like `uses`, `indicates`, `targets`, `related-to`. Modeling relationships as first-class objects is what makes the graph valuable. Prefer expressing connections as SROs over flattening them into properties.

**Bundles.** The envelope. A `bundle` is a flat collection of objects you send together. A bundle should be internally consistent: if an object references another (a marking definition, an author identity, a relationship target), the referenced object should be present or already known to the platform.

> Why build STIX objects instead of calling the GraphQL API directly? Native data-model alignment, deterministic IDs (free deduplication), resilience through the worker/RabbitMQ pipeline, batch throughput, first-class relationships, early validation, and API stability. Build STIX.

## Dev environment pre-check

By now everyone should have completed [00-prerequisites.md](00-prerequisites.md). Quick room check:

- Platform loads and you can log in?
- API token in hand?
- `pycti` installed and the version query returned?

If anyone is blocked, pair them with a neighbor who is set up, the labs are doable in pairs.

---

Next: [Module 2 - Building a Connector](02-building-a-connector.md)
