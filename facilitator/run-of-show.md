# Facilitator Run-of-Show

One day, 10:00-16:00, ~20 attendees. Lunch at 12:30-13:30. Times are guides; the buffer at the end absorbs overruns.

## Agenda

**Module 1: Foundations & Ecosystem**
• Architecture refresher — platform, workers, RabbitMQ, connectors  
• Connector types table + when to use which  
• STIX 2.1 primer — entities, relationships, bundles  
• Dev environment pre-check (everyone should have done this before arriving)

**Module 2: Deep Dive — Building a Connector**
• OpenCTIConnectorHelper, self-triggered vs. platform-triggered  
• Work initiation, state management, deduplication strategy  
• Constructing STIX 2.1 bundles and connectors SDK  
• Hands-on lab — build a minimal EXTERNAL_IMPORT connector

**LUNCH — 11:30 (1 hour)**

**Module 3: Best Practices & Code Quality**
• Logging, error handling, code style (black, flake8, isort)  
• State management, security hygiene (tokens, secrets)  
• Reading existing connectors for patterns and guidelines — don't reinvent the wheel  
• Apply formatting + fix a bad error handler in sample code

**Module 4: Testing & Debugging**
• Local testing workflow, inspecting RabbitMQ, worker logs  
• Common mistakes and how to avoid them

**Module 5: Contributing & Wrap-up**  
• Contribution workflow — branch, commit, PR conventions  
• Minimum release criteria, README standards  
• Key takeaways recap + useful links

## At a glance

| Time | Module |
|------|--------|
| 10:00 - 10:40 | Module 1: Foundations and Ecosystem |
| 10:40 - 12:30 | Module 2: Deep Dive, Building a Connector (incl. hands-on lab) |
| 12:30 - 13:30 | Lunch |
| 13:30 - 14:35 | Module 3: Best Practices and Code Quality |
| 14:35 - 15:25 | Module 4: Testing and Debugging |
| 15:25 - 15:55 | Module 5: Contributing and Wrap-up |
| 15:55 - 16:00 | Buffer / Q&A |

## Detailed notes

### Module 1 (10:00-10:40)

- 5 min: welcome, goals, how the day runs.
- 20 min: architecture + connector types + STIX primer (slides from [docs/01](../docs/01-foundations.md)).
- 10 min: live room pre-check. Ask for a show of hands on each item in the prereq sign-off. Pair anyone blocked with a set-up neighbor now, before the lab.
- 5 min: buffer / questions.

### Module 2 (10:40-12:30)

- 30 min lecture: walk the helper, self vs platform triggers, work/state/dedup, bundle construction and the callback. Live-read the relevant solution file as you talk.
- Announce what we will build.
- 80 min lab: attendees work the starter TODOs. Float the room. Watch for the usual blockers (UUID for connector id, token, URL). Aim for everyone to see *something* land in the platform before lunch; the solution is the safety net.

### Lunch (12:30-13:30)

### Module 3 (13:30-14:35)

- 35 min lecture.
- 30 min mini lab: format + fix the bad handler. This is quick and recovers anyone who fell behind in Module 2.

### Module 4 (14:35-15:25)

- Demo-led. Project the platform, RabbitMQ management UI. Trigger a failure on purpose (e.g. an incomplete bundle) and walk the symptom -> location table live. This is the highest-retention block; keep it interactive.

### Module 5 (15:25-15:55)

- PR workflow, minimum release criteria, README standards.
- Takeaways recap and links. Point attendees at the connectors repo to keep learning.

### Buffer (15:55-16:00)

- Overflow, individual help, feedback.

## Facilitator pre-flight (day before)

- [ ] Shared lab instance up (or confirm everyone's local stack)
- [ ] Repo URL shared; prereq doc sent at least a week ahead
- [ ] Projector tested with platform + RabbitMQ UI + terminal
- [ ] Pinned versions in `requirements.txt` verified against the platform version (see reuse guide)
- [ ] A spare API token / account for attendees who arrive without one
- [ ] Workshop channel created for async help
