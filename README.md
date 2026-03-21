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
│   ├── config.py      # Hardcoded allowed users, dumps, TTLs, Jenkins/RC settings
│   ├── schemas.py     # Pydantic models: RocketChatPayload, ParsedCommand, BotResponse
│   ├── parser.py      # parse_command(): splits and validates /db text
│   ├── auth.py        # verify_token(), is_user_allowed()
│   ├── jenkins.py     # trigger_jenkins_job(): async httpx POST to Jenkins
│   ├── utils.py       # generate_db_name()
│   └── settings.py    # Env-var config via pydantic-settings (optional overrides)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

```bash
git clone <repository-url>
cd rocketchat-db-deployer

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## Configuration

All settings are hardcoded in `app/config.py` for now:

| Variable | Default |
|---|---|
| `ALLOWED_USERS` | `{"ivan", "petr", "anna"}` |
| `ALLOWED_DUMPS` | `{"empty", "masked-main", "qa-snapshot"}` |
| `ALLOWED_TTLS` | `{"4h", "8h", "24h", "48h"}` |
| `JENKINS_URL` | `http://jenkins.local` |
| `JENKINS_JOB` | `provision-dev-db` |
| `ROCKETCHAT_TOKEN` | `supersecrettoken` |

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## Endpoint

`POST /rocketchat/db-command`

**Headers:**
```
X-Auth-Token: supersecrettoken
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
  -H "X-Auth-Token: supersecrettoken" \
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