import httpx
from urllib.parse import quote

from app.config import JENKINS_JOB, JENKINS_URL
from app.schemas import ParsedCommand
from app.settings import settings


async def trigger_jenkins_job(cmd: ParsedCommand) -> None:
    """Trigger Jenkins ``buildWithParameters`` with a whitelisted templatebase.

    Args:
        cmd: Validated command parameters.

    Raises:
        RuntimeError: When Jenkins returns an unexpected status code.
        httpx.HTTPError: On network-level failures.
    """
    job_path = quote(JENKINS_JOB, safe="")
    url = f"{JENKINS_URL.rstrip('/')}/job/{job_path}/buildWithParameters"
    job_params = {
        "templatebases": cmd.templatebases,
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
