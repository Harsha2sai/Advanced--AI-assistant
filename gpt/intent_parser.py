import re

def parse_intent(text):
    """Parse user input text to detect known intents, else return None."""
    text = text.lower().strip()

    if re.search(r'\b(time|current time|what time)\b', text):
        return ("get_time", {})

    if re.search(r'\b(date|today|current date)\b', text):
        return ("get_date", {})

    if "joke" in text:
        return ("tell_joke", {})

    m = re.match(r'calculate (.+)', text)
    if m:
        return ("calculate", {"expr": m.group(1)})

    m = re.match(r'set timer for (\d+) (seconds|minutes|hours)', text)
    if m:
        amount = int(m.group(1))
        unit = m.group(2)
        multiplier = {"seconds": 1, "minutes": 60, "hours": 3600}[unit]
        return ("set_timer", {"seconds": amount * multiplier})

    m = re.match(r'(add|create) to[- ]do (.+)', text)
    if m:
        return ("add_todo", {"item": m.group(2)})

    if re.search(r'(list|show) to[- ]dos', text):
        return ("list_todos", {})

    m = re.match(r'(complete|mark) to[- ]do (\d+)', text)
    if m:
        idx = int(m.group(2))
        return ("complete_todo", {"index": idx})

    return (None, {})
