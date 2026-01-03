from mss import mss
from PIL import Image
import time

def capture_screen():
   
    for attempt in range(3):
        try:
            with mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                return img
        except Exception as e:
            print(f"[WORKER] Screenshot failed (attempt {attempt+1}): {e}")
            time.sleep(0.5)

    raise RuntimeError("Screenshot capture failed after retries")
