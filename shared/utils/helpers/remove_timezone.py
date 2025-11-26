from datetime import datetime


def remove_timezone(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(tz=None).replace(tzinfo=None)
    return dt
