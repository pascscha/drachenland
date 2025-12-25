import datetime
from typing import Dict, List, Any


def is_store_open(
    schedule: Dict[str, Any], current_dt: datetime.datetime = None
) -> bool:
    """
    Checks if the store is open based on the provided schedule and current time.

    Args:
        schedule: A dictionary where keys are English short day names (Mon, Tue, Wed, Thu, Fri, Sat, Sun)
                  and values are lists of time ranges (e.g. [{"start": "09:00", "end": "12:00"}]).
        current_dt: Optional datetime object to check against. Defaults to datetime.datetime.now().

    Returns:
        True if the store is open, False otherwise.
    """
    if current_dt is None:
        current_dt = datetime.datetime.now()

    day_name = current_dt.strftime("%a")  # Mon, Tue, etc.

    # Map German day names to English because the user requested Mo, Di, etc.
    # but it's better to store standard keys internally or handle mapping.
    # The user prompt: "Mo: closed, Di 09:00 - 12:00..."
    # Let's assume the config will store English keys for simplicity in code,
    # but the UI will show German. Or we can support both.
    # Let's standardize on English 3-letter codes for JSON config: Mon, Tue, Wed, Thu, Fri, Sat, Sun.

    if day_name not in schedule:
        return False

    ranges = schedule[day_name]
    if not ranges:
        return False

    current_time = current_dt.time()

    for time_range in ranges:
        try:
            start_str = time_range.get("start")
            end_str = time_range.get("end")

            if not start_str or not end_str:
                continue

            start_time = datetime.datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.datetime.strptime(end_str, "%H:%M").time()

            if start_time <= current_time <= end_time:
                return True
        except ValueError:
            # Handle potential parsing errors gracefullly
            continue

    return False


def get_default_schedule() -> Dict[str, List[Dict[str, str]]]:
    """Returns the default schedule specified in the user request."""
    return {
        "Mon": [],  # Closed
        "Tue": [{"start": "09:00", "end": "12:00"}],
        "Wed": [{"start": "09:00", "end": "12:00"}, {"start": "13:30", "end": "17:00"}],
        "Thu": [
            {"start": "09:00", "end": "12:00"},
            {"start": "13:30", "end": "17:00"},
        ],  # Note: User said 17:-- assuming 17:00 based on context
        "Fri": [{"start": "13:30", "end": "17:00"}],
        "Sat": [{"start": "09:00", "end": "16:00"}],
        "Sun": [],  # Closed
    }
