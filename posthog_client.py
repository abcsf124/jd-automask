"""Shared PostHog client for the application process."""

import atexit
import os
import sys

from dotenv import load_dotenv
from posthog import Posthog


load_dotenv()


def _shutdown_posthog(client):
    try:
        client.shutdown()
    except Exception:
        pass


def _initialize_posthog():
    """Create the process-wide client when PostHog is configured."""
    project_token = os.getenv("POSTHOG_PROJECT_TOKEN")
    host = os.getenv("POSTHOG_HOST")

    if not project_token:
        print(
            "WARNING: POSTHOG_PROJECT_TOKEN variable required by PostHog is missing "
            "or un-configured, this causes events to be silently missed. This error "
            "stops appearing once POSTHOG_PROJECT_TOKEN is configured",
            file=sys.stderr,
        )
        return None

    if not host:
        print(
            "WARNING: POSTHOG_HOST variable required by PostHog is missing or "
            "un-configured, this causes events to be silently missed. This error stops "
            "appearing once POSTHOG_HOST is configured",
            file=sys.stderr,
        )
        return None

    client = Posthog(
        project_token,
        host=host,
        enable_exception_autocapture=True,
    )
    atexit.register(_shutdown_posthog, client)
    return client


posthog_client = _initialize_posthog()
