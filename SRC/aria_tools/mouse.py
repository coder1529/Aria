import os
import pyautogui
from PIL import Image, ImageDraw, ImageGrab, ImageFont

pyautogui.FAILSAFE = True
SCREEN_FILE = os.path.join(os.path.dirname(__file__), "screen.png")
DEBUG_FILE = os.path.join(os.path.dirname(__file__), "click_debug.png")

ZOOM_FILE = os.path.join(os.path.dirname(__file__), "zoom.png")
ZOOM_SIZE = 0.2                 # zoom box covers 20% of the screen's width and height
VIEW = [0.0, 0.0, 1.0, 1.0]     # what part of the screen she's seeing: left, top, right, bottom

def mark(x, y):
    # draw a red dot where she's aiming on her last screenshot, so you can check her aim
    img = Image.open(SCREEN_FILE)
    px = x / 1000 * img.width
    py = y / 1000 * img.height
    ImageDraw.Draw(img).ellipse((px - 10, py - 10, px + 10, py + 10), outline="red", width=4)
    img.save(DEBUG_FILE)

def click(x: int, y: int):
    """
    Click on the screen. You must call zoom on the target first.

    Args:
        x: Horizontal position from 0 to 1000 in the zoomed image.
        y: Vertical position from 0 to 1000 in the zoomed image.
    """

    if VIEW == [0.0, 0.0, 1.0, 1.0]:
        return "Error: zoom in on the target first, then click using coordinates in the zoomed image."
    x, y = int(float(x)), int(float(y))
    fx, fy = to_screen(x, y)
    mark(fx * 1000, fy * 1000)
    screen_w, screen_h = pyautogui.size()
    real_x = int(fx * screen_w)
    real_y = int(fy * screen_h)
    reset_view()
    # answer = input(f"\nARIA wants to click at ({real_x}, {real_y}). Check click_debug.png. Allow? (y/n): ")
    # if answer.strip().lower() != "y":
    #     return "The user declined. Do not retry; ask what they want instead."
    pyautogui.click(real_x, real_y)
    return f"Clicked at ({x}, {y})."

def reset_view():
    VIEW[:] = [0.0, 0.0, 1.0, 1.0]

def to_screen(x, y):
    # 0-1000 position in the current view -> fraction of the whole screen
    left, top, right, bottom = VIEW
    fx = left + x / 1000 * (right - left)
    fy = top + y / 1000 * (bottom - top)
    return fx, fy

def zoom(x: int, y: int):
    """
    Zoom in around a point to aim a click precisely. Call look with source "screen" first.

    Args:
        x: Horizontal position from 0 to 1000 in the image you are currently seeing.
        y: Vertical position from 0 to 1000 in the image you are currently seeing.
    """
    x, y = int(float(x)), int(float(y))
    cx, cy = to_screen(x, y)
    left = min(max(cx - ZOOM_SIZE / 2, 0), 1 - ZOOM_SIZE)   # keep the box inside the screen
    top = min(max(cy - ZOOM_SIZE / 2, 0), 1- ZOOM_SIZE)
    VIEW[:] = [left, top, left + ZOOM_SIZE, top + ZOOM_SIZE]

    img = ImageGrab.grab()       # full resolution, not the shrunken screenshot
    box = (int(left * img.width), int(top * img.height),
           int(VIEW[2] * img.width), int(VIEW[3] * img.height))
    crop = img.crop(box)
    draw_grid(crop.resize((1280, int(1280 * crop.height / crop.width)))).save(ZOOM_FILE)
    return ZOOM_FILE

def draw_grid(img):
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=18)
    for i in range(100, 1000, 100):          # a line every 100 units
        x = i / 1000 * img.width
        y = i / 1000 * img.height
        draw.line((x, 0, x, img.height), fill="red", width=1)
        draw.line((0, y, img.width, y), fill="red", width=1)
        draw.text((x + 2, 2), str(i), fill="red", font=font)      # label along the top
        draw.text((2, y + 2), str(i), fill="red", font=font)      # label along the left
    return img

# if __name__ == "__main__":
#     print(click(500, 500))    # should aim at the dead center of the screen

if __name__ == "__main__":
    print(zoom(900, 900))
    print(VIEW)