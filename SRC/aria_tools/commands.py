import re
import subprocess

BLOCKED = [
    r"\bremove-item\b", r"\bdel\b", r"\brm\b", r"\brmdir\b", r"\berase\b",
    r"\bformat\b", r"\bshutdown\b", r"\bstop-computer\b", r"\brestart-computer\b",
    r"\breg\b", r"hklm:", r"hkcu:", r"-force\b", r"\bdiskpart\b",
]

def is_blocked(command):
    return any(re.search(pattern, command, re.IGNORECASE) for pattern in BLOCKED)

def execute(command):
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True, text=True, timeout=5,
        )
    except subprocess.TimeoutExpired:
        return "ERROR: The command took too long and was stopped"
    output = result.stdout + result.stderr
    return output[:1000] or "(no output)"

def run_command(command: str):
    """
    Run a PowerShell command on the user's Windows PC and return its output.

    Args:
        command: A single PowerShell command to run.
    """
    if is_blocked(command):
        return "Blocked: This command is not allowed for safety reasons"
    answer = input(f"\nARIA wants to run:\n  {command}\nAllow? (y/n): ")
    if answer.strip().lower() != "y":
        return "Blocked: The user declined to run this command. Do not retry it; ask what they want instead."
    return execute(command)