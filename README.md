# Rocket.Chat + Telegram Template Restore Gateway

A minimal FastAPI service that proxies a validated template restore request to Jenkins from Rocket.Chat or Telegram.

## How it works

A user sends `/db <templatebases>` (or just `<templatebases>`). The service checks that template value against an allowlist and runs Jenkins `buildWithParameters` with `templatebases=<value>`.

## Project structure

```
rocketchat-db-deployer/
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI app, POST /rocketchat/db-command
│   ├── config.py      # Non-secret constants (allowed templates, Jenkins URL/job)
│   ├── schemas.py     # Pydantic models: RocketChatPayload, ParsedCommand, BotResponse
│   ├── parser.py      # parse_command(): validates templatebases from command text
│   ├── auth.py        # verify_token()
│   ├── jenkins.py     # trigger_jenkins_job(): async httpx POST to Jenkins
│   └── settings.py    # Env-var settings for secrets (Rocket.Chat/Jenkins)
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
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
| `ALLOWED_TEMPLATEBASES` | `{"erp_borzenkova"}` |
| `ALLOWED_TELEGRAM_FULL_ACCESS_USER_IDS` | `{123456789}` |
| `ALLOWED_TELEGRAM_OWN_TEMPLATEBASE_BY_USER_ID` | `{}` |
| `JENKINS_URL` | `http://172.16.0.139:8080` |
| `JENKINS_JOB` | `restore_erp_for_dev` |

Secrets must be provided via environment variables (`.env`):

| Variable | Description |
|---|---|
| `RC_SLASH_TOKEN` | Shared Rocket.Chat token checked against `X-Auth-Token` |
| `JENKINS_USER` | Jenkins API username |
| `JENKINS_TOKEN` | Jenkins API token |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token used to send responses |
| `TELEGRAM_WEBHOOK_SECRET` | Secret header value for Telegram webhook verification |

`JENKINS_API_TOKEN` is also supported for backward compatibility.

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## Run In Docker

Build image:

```bash
docker build -t rocketchat-db-deployer .
```

Run container:

```bash
docker run --rm -p 8000:8000 --env-file .env rocketchat-db-deployer
```

Or use Docker Compose:

```bash
docker compose up -d --build
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
  "text": "/db erp_borzenkova"
}
```

**Command format:** `/db <templatebases>`
- `templatebases` — one of `ALLOWED_TEMPLATEBASES`

**Example curl:**
```bash
curl -X POST http://localhost:8000/rocketchat/db-command \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: <RC_SLASH_TOKEN>" \
  -d '{"text": "/db erp_borzenkova"}'
```

Equivalent Jenkins call performed by this service:
```bash
curl -X POST "http://172.16.0.139:8080/job/restore_erp_for_dev/buildWithParameters" \
  --user "<JENKINS_USER>:<JENKINS_TOKEN>" \
  --data "templatebases=erp_borzenkova"
```

**Responses:**

| Situation | Response text |
|---|---|
| Success | `Request accepted: templatebases=erp_borzenkova` |
| Bad format | `Invalid command format. Use: /db <templatebases>` |
| Unauthorized | `Access denied` |
| Jenkins error | `Failed to trigger Jenkins job` |

## Health check

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

## Telegram Webhook

Endpoint:

`POST /telegram/webhook`

Header:

`X-Telegram-Bot-Api-Secret-Token: <TELEGRAM_WEBHOOK_SECRET>`

Telegram command format:

- `/db <templatebases>`
- `/db@<bot_name> <templatebases>`
- `/whoami`

Telegram deduplication:

1. The service keeps a recent in-memory cache of processed `update_id` values.
2. Repeated webhook deliveries with the same `update_id` are ignored.

Telegram access control:

1. Send `/whoami` to the bot.
2. Take the returned Telegram user id.
3. For full access, add id to `ALLOWED_TELEGRAM_FULL_ACCESS_USER_IDS` in [app/config.py](app/config.py).
4. For restricted access (only one base), add mapping in `ALLOWED_TELEGRAM_OWN_TEMPLATEBASE_BY_USER_ID` in [app/config.py](app/config.py), e.g. `111111111: "erp_test"`.
5. Restart the service.

Set webhook (replace placeholders):

```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -d "url=https://<your-domain>/telegram/webhook" \
  -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>"
```