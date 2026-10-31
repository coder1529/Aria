import os
import cv2
from aria_tools import mouse
from PIL import ImageGrab, Image

SCREEN_FILE = os.path.join(os.path.dirname(__file__), "screen.png")
CAMERA_FILE = os.path.join(os.path.dirname(__file__), "camera.png")
MAX_WIDTH = 1280       # bigger images = more tokens = slower + more VRAM

def shrink(img):
    if img.width > MAX_WIDTH:
        ratio = MAX_WIDTH / img.width
        img = img.resize((MAX_WIDTH, int(img.height * ratio)))
    return img

def capture_screen():
    img = ImageGrab.grab()           # grabs the whole screen as a PIL image
    mouse.draw_grid(shrink(img)).save(SCREEN_FILE)
    return SCREEN_FILE

def capture_camera():
    cam = cv2.VideoCapture(0)          # 0 = first webcam
    ok, frame = cam.read()
    cam.release()                       # free the webcam so other apps can use it
    if not ok:
        return None
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)   # OpenCV uses BGR, PIL uses RGB
    shrink(Image.fromarray(frame)).save(CAMERA_FILE)
    return CAMERA_FILE

def look(source: str):
    """
    Take a picture so you can see something.

    Args:
        source: "screen" to see the user's PC screen, or "camera" to see through the webcam.
    """
    if source == "screen":
        return capture_screen()
    return capture_camera()

def drop_images(history):
    for msg in history:
        if isinstance(msg.get("content"), list):
            msg["content"] = [c for c in msg["content"] if c["type"] != "image"]

capture_screen()