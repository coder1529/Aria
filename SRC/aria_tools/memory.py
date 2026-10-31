import os

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "../memory.txt")

def remember(fact: str):
    """
    Save a fact about the user to long-term memory.

    Args:
        fact: One short fact, like "His birthday is December 4".
    """
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:   # which mode adds to the end instead of erasing?
        f.write(fact + "\n")
    return "Saved to memory."

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return ""                      # first run: no file yet
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return f.read()