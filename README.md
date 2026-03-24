# Rocket.Chat DB Deployer

A minimal FastAPI service that acts as a secure gateway between Rocket.Chat and Jenkins to trigger database provisioning jobs via a slash command.

## How it works

A user types `/db <label> <dump> <ttl>` in Rocket.Chat. The outgoing webhook calls this service, which validates the request and triggers a parameterised Jenkins job.

## Project structure

```
rocketchat-db-deployer/
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI app, POST /rocketchat/db-command
│   ├── config.py      # Non-secret constants (whitelists, dumps, ttl, Jenkins URL/job)
│   ├── schemas.py     # Pydantic models: RocketChatPayload, ParsedCommand, BotResponse
│   ├── parser.py      # parse_command(): splits and validates /db text
│   ├── auth.py        # verify_token(), is_user_allowed()
│   ├── jenkins.py     # trigger_jenkins_job(): async httpx POST to Jenkins
│   ├── utils.py       # generate_db_name()
│   └── settings.py    # Env-var settings for secrets (Rocket.Chat/Jenkins)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

```bash
git clone <repository-url>

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## Configuration

Non-secret settings are stored in `app/config.py`:

| Variable | Default |
|---|---|
| `ALLOWED_USERS` | `{"ivan", "petr", "anna"}` |
| `ALLOWED_DUMPS` | `{"empty", "masked-main", "qa-snapshot"}` |
| `ALLOWED_TTLS` | `{"4h", "8h", "24h", "48h"}` |
| `JENKINS_URL` | `http://jenkins.local` |
| `JENKINS_JOB` | `provision-dev-db` |

Secrets must be provided via environment variables (`.env`):

| Variable | Description |
|---|---|
| `RC_SLASH_TOKEN` | Shared Rocket.Chat token checked against `X-Auth-Token` |
| `JENKINS_USER` | Jenkins API username |
| `JENKINS_TOKEN` | Jenkins API token |

`JENKINS_API_TOKEN` is also supported for backward compatibility.

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## Endpoint

`POST /rocketchat/db-command`

**Headers:**
```
X-Auth-Token: <RC_SLASH_TOKEN>
Content-Type: application/json
```

**Body:**
```json
{
  "user_name": "ivan",
  "text": "/db api masked-main 24h",
  "channel_id": "GENERAL"
}
```

**Command format:** `/db <label> <dump> <ttl>`
- `label` — `^[a-z0-9-]{3,16}$`
- `dump` — one of `ALLOWED_DUMPS`
- `ttl` — one of `ALLOWED_TTLS`

**Example curl:**
```bash
curl -X POST http://localhost:8000/rocketchat/db-command \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: <RC_SLASH_TOKEN>" \
  -d '{"user_name": "ivan", "text": "/db api masked-main 24h", "channel_id": "GENERAL"}'
```

**Responses:**

| Situation | Response text |
|---|---|
| Success | `Request accepted: db=db-ivan-api, dump=masked-main, ttl=24h` |
| Bad format | `Invalid command format. Use: /db <label> <dump> <ttl>` |
| Unauthorized | `Access denied` |
| Jenkins error | `Failed to trigger Jenkins job` |

## Health check

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```