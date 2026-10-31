import os
from datetime import datetime, timedelta

REMINDER_FILE = os.path.join(os.path.dirname(__file__), "../reminders.txt")
FMT = "%Y-%m-%d %H:%M"

def set_reminder(minutes: int, text: str):
    """
    Set a reminder or timer that ARIA will say out loud after some minutes.

    Args:
        minutes: How many minutes from now, like 10.
        text: What to remind the user about, like "take out the trash".
    """
    due = datetime.now() + timedelta(minutes=int(minutes))
    with open(REMINDER_FILE, "a", encoding="utf-8") as f:
        f.write(f"{due.strftime(FMT)}|{text}\n")
    return f"Reminder set for {due.strftime('%H:%M')}."

def due_reminders():
    if not os.path.exists(REMINDER_FILE):
        return []
    with open(REMINDER_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    now = datetime.now()
    due, waiting = [], []
    for line in lines:
        time_str, text = line.split("|", 1)
        if datetime.strptime(time_str, FMT) <= now:
            due.append(text)
        else:
            waiting.append(line)

    with open(REMINDER_FILE, "w", encoding="utf-8") as f:   # rewrite with only the waiting ones
        for line in waiting:
            f.write(line + "\n")
    return due
    print(set_reminder(0, "test reminder"))
    print(due_reminders())   # should print ['test reminder']
    print(due_reminders())   # should print [] since it was already removed