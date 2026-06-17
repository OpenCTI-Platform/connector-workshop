# OpenCTI Connector Development Workshop

A one-day, hands-on workshop for building OpenCTI connectors. By the end, each attendee will have built a working connector from scratch and understand how to contribute it back.

**Audience:** developers new to or wanting an update on OpenCTI connector development

**Format:** 1 day, ~20 attendees, mix of lecture and labs

**Outcome:** a minimal working connector (EXTERNAL_IMPORT or INTERNAL_ENRICHMENT)

## **Experience required**

- [ ]  Comfortable working in Python 3.x and using virtual environments (venv, uv, or pip)
- [ ]  Solid Git workflow: branching, commits, pull requests, and resolving merge conflicts
- [ ]  Familiarity with Docker and Docker Compose: running services locally and inspecting logs
- [ ]  Basic command-line and terminal proficiency
- [ ]  Prior experience with JSON and data modeling; exposure to STIX 2.1 concepts is a plus
- [ ]  Comfortable debugging with breakpoints and logging, reading stack traces, and working in an IDE
- [ ]  Able to follow coding standards and tooling (black, flake8, isort) and write or adjust simple unit tests

## 💻 Laptop Ready checklist

- [ ]  macOS, Linux, or Windows 11 with admin rights (able to install tools)
- [ ]  Python 3.12 installed and available on PATH (or Python 3.11+)
- [ ]  Virtual env tooling working: `venv` (uv or Poetry/pipx)
- [ ]  Git 2.x installed; GitHub access working; SSH keys configured (recommended)
- [ ]  IDE/editor: VS Code or PyCharm (with Python + Docker extensions/plugins)
- [ ]  Connector repository forked and cloned: https://github.com/OpenCTI-Platform/connectors
- [ ]  Be able to clone workshop repository during workshop
- [ ]  Ports available for local services (e.g., 3000/4000/8080/5672) or ability to remap
- [ ]  Access to lab instance for both Web UI and API access or OpenCTI running locally via Docker Compose (see [octi-lab](./octi-lab/README.md))

## Before you arrive

Complete the [dev environment pre-check](docs/00-prerequisites.md). The labs assume a working OpenCTI instance if deployed locally and Python toolchain. Do not leave this for the morning of, the setup takes time and we will not pause the room to debug installs.

## Schedule

| Time | Module |
|------|--------|
| 10:00 - 10:40 | Module 1: Foundations and Ecosystem |
| 10:40 - 12:30 | Module 2: Deep Dive, Building a Connector (incl. hands-on lab) |
| 12:30 - 13:30 | Lunch |
| 13:30 - 14:35 | Module 3: Best Practices and Code Quality |
| 14:35 - 15:25 | Module 4: Testing and Debugging |
| 15:25 - 15:55 | Module 5: Contributing and Wrap-up |
| 15:55 - 16:00 | Buffer / Q&A |
