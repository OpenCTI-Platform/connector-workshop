# 00 - Prerequisites and Dev Environment Pre-Check

Complete this **before** the workshop. Budget 45-60 minutes. If something fails, post in the workshop channel ahead of time.

## What you need

| Requirement | Notes |
|-------------|-------|
| A running OpenCTI instance | Local Docker Compose stack, or access to a shared lab instance |
| Python 3.11+ | `python --version` |
| Git | `git --version` |
| Docker + Docker Compose | Required for running the platform and your connector as a container |
| A code editor | VS Code or PyCharm recommended |
| An OpenCTI API token | Generated from your user profile in the platform |

> **WSL users:** run everything from inside WSL. Docker should be installed natively on the WSL side with the daemon reachable at the Unix socket, not via Docker Desktop integration. All commands below assume a WSL/Ubuntu shell.

## Step 1: Clone this repo

```bash
git clone <this-repo-url> connector-workshop
cd connector-workshop
```

## Step 2: Get OpenCTI running

If you are using a shared lab instance, confirm you can log in and have an API token. It is sufficient to run the Step 3 connectivity check from your local machine, you do not need to run the platform locally.

The fastest path is the official Docker Compose stack. Follow the [OpenCTI deployment docs](https://docs.opencti.io/latest/deployment/installation/) and bring it up:

```bash
git clone https://github.com/OpenCTI-Platform/docker.git opencti-docker
cd opencti-docker
cp .env.sample .env   # then edit the required variables
docker compose up -d
```

Wait for the platform to be healthy, then open it in your browser. Confirm you can log in.

Or you can locally run the lab stack with the provided `docker-compose.yml` in ./octi-lab.

```bash
cd ./octi-lab
cp .env.sample .env   # then edit the required variables
docker compose up -d
```

Wait for the platform to be healthy, then open it in your browser. Confirm you can log in.

## Step 3: Generate an API token

1. Log in to OpenCTI.
2. Open your profile (top-right avatar).
3. Copy the **API key** shown on the profile page.

Keep this token handy, you will set it as `OPENCTI_TOKEN` in the labs. Treat it like a password.

## Step 4: Verify connectivity from Python

Go to the `octi-lab` folder and edit the `check-connection.py` script. Replace the placeholder token with your API token. And follow the instruction in the [README](../octi-lab/README.md)

If you see a version string, your environment is ready. If you get a connection error, the platform is not reachable; if you get an auth error, the token is wrong.

## Pre-check sign-off

You are ready if **all** of these are true:

- [ ] OpenCTI loads in the browser and you can log in
- [ ] You have copied your API token
- [ ] The Step 3 script printed a version
- [ ] You have cloned this repo
- [ ] `docker`, `python`, and `git` all run from your shell

## Common setup problems

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Browser shows nothing on the platform URL | Stack still starting, or Elasticsearch unhealthy | Check `docker compose ps` and `docker compose logs` |
| `Connection refused` from Python | Wrong URL or platform not up | Confirm the port and that containers are healthy |
| `401` / auth error | Bad or missing token | Re-copy the token from your profile |
| Docker commands fail on WSL | Daemon not running natively in WSL | Start the daemon in WSL; do not rely on Docker Desktop |
