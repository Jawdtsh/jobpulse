import logging
import sys

from config.settings import get_settings


def setup_logging() -> None:
    settings = get_settings()
    level = logging.DEBUG if settings.monitoring.debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )

    sentry_dsn = settings.monitoring.sentry_dsn
    if sentry_dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=settings.monitoring.environment,
                traces_sample_rate=0.1,
            )
            logger = logging.getLogger(__name__)
            logger.info(
                "Sentry initialized for environment=%s", settings.monitoring.environment
            )
        except ImportError:
            logging.getLogger(__name__).warning(
                "sentry_sdk not installed, skipping Sentry init"
            )
