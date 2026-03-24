import httpx

from app.config import JENKINS_JOB, JENKINS_URL
from app.schemas import ParsedCommand
from app.settings import settings


async def trigger_jenkins_job(cmd: ParsedCommand, db_name: str) -> None:
    """Trigger the Jenkins provisioning job via ``buildWithParameters``.

    Args:
        cmd: Validated command parameters.
        db_name: Pre-generated database name (never raw user input).

    Raises:
        RuntimeError: When Jenkins returns an unexpected status code.
        httpx.HTTPError: On network-level failures.
    """
    url = f"{JENKINS_URL.rstrip('/')}/job/{JENKINS_JOB}/buildWithParameters"
    job_params = {
        "REQUESTED_BY": cmd.user_name,
        "DB_NAME": db_name,
        "DUMP_NAME": cmd.dump,
        "TTL": cmd.ttl,
        "ROCKET_CHANNEL": cmd.channel_id,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            url,
            data=job_params,
            auth=(settings.JENKINS_USER, settings.JENKINS_TOKEN),
        )

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Jenkins responded with unexpected status {response.status_code}: {response.text[:200]}"
        )
