from datetime import date, timedelta

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

def next_weekday(weekday: str):
    """
    Get the date of the next given weekday after today.

    Args:
        weekday: Day name in English, like "saturday".
    """
    today = date.today()
    target = WEEKDAYS.index(weekday.lower())
    days_ahead = (target - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7        # today is that weekday: return next week's, not today
    result = today + timedelta(days=days_ahead)
    return result.strftime("%A, %B %d, %Y")

def days_until(target_date: str):
    """
    Count calendar days from today until a date.

    Args:
        target_date: The date in YYYY-MM-DD format, like "2026-12-25".
    """
    target = date.fromisoformat(target_date)
    return f"{(target - date.today()).days} days until {target_date}"

if __name__ == "__main__":
    print(next_weekday("saturday"))    # should be Saturday, October 17, 2026
    print(next_weekday("friday"))      # today is Friday, so should be October 23, not 16
    print(days_until("2026-12-25"))    # should be 70