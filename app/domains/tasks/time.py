from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings


def local_timezone() -> ZoneInfo:
    return ZoneInfo(settings.timezone)


def now_local() -> datetime:
    return datetime.now(local_timezone())


def today_local():
    return now_local().date()


def local_day_bounds():
    tz = local_timezone()
    today = today_local()

    start = datetime.combine(
        today,
        time.min,
        tzinfo=tz,
    )

    end = start + timedelta(days=1)

    return start, end