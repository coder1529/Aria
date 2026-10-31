import time
import pyautogui

pyautogui.FAILSAFE = True    # slam the mouse into a screen corner to stop everything

def confirm(action):
    answer = input(f"\nARIA wants to {action}\nAllow? (y/n): ")
    return answer.strip().lower() == "y"

def type_text(text: str):
    """
    Type text on the keyboard into the window the user has open.

    Args:
        text: The text to type.
    """
    text = str(text)
    if not confirm(f"type: {text}"):
        return "The user declined. Do not retry; ask what they want instead."
    print("Click the window to type into... typing in 3 seconds")
    time.sleep(3)
    pyautogui.write(text, interval=0.02)
    return "Typed."

def press_keys(keys: str):
    """
    Press a key or keyboard shortcut.

    Args:
        keys: Keys joined with +, like "ctrl+s" or "enter". Media keys: playpause, nexttrack, prevtrack, volumeup, volumedown, volumemute.
    """
    keys = str(keys)
    key_list = keys.lower().split("+")
    for k in key_list:
        if k not in pyautogui.KEYBOARD_KEYS:
            return f"Error: unknown key '{k}'."
    # if not confirm(f"press: {keys}"):
    #     return "The user declined. Do not retry; ask what they want instead."
    pyautogui.hotkey(*key_list)
    return f"Pressed {keys}."

if __name__ == "__main__":
    print(press_keys("volumemute"))   # run twice: mute, then unmute