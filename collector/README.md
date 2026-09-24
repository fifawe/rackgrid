# Collector

Ansible-based discovery agent. Two ways to use it:

## 1. Standalone (manual run)

```bash
cd collector
ansible-playbook -i inventory/hosts.ini playbook.yml \
  -e backend_base_url=http://localhost:8000 \
  -e collector_api_key=$COLLECTOR_API_KEY
```

Edit `inventory/hosts.ini` to list your real Linux servers first.

## 2. As a container, triggered by the scheduler

`docker compose up` builds this directory into the `collector` service,
which runs `agent.py` - a tiny FastAPI wrapper exposing:

- `POST /run` - runs `ansible-playbook` against `inventory/hosts.ini`
  and returns its exit code. This is what the `scheduler` service calls
  (see `backend/app/infrastructure/scheduling/collector_runner.py`) for
  both "Run Now" and scheduled runs.
- `GET /health` - container healthcheck.

## Roles

| Role              | Responsibility                                   |
|-------------------|---------------------------------------------------|
| `gather_hardware` | Hostname, serial number, manufacturer/model, CPU, RAM |
| `gather_os`       | Distribution, version, kernel, architecture, uptime |
| `gather_network`  | Primary IP, all interfaces, MAC addresses          |
| `gather_storage`  | Mounted filesystems (ansible facts, lsblk fallback) |
| `build_payload`   | Assembles the JSON payload matching PROJECT_SPEC.md |
| `submit_payload`  | POSTs to `{{ backend_base_url }}/api/v1/discovery` |

Submission always happens from the control node (`delegate_to:
localhost` in `submit_payload`), since managed hosts generally won't
have network access to the backend's internal Docker network.
