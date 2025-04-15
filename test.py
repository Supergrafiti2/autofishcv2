import mss
import Quartz
import numpy as np
import cv2

def get_minecraft_bounds():
    options = Quartz.kCGWindowListOptionOnScreenOnly
    window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
    for window in window_list:
        owner_name = window.get('kCGWindowOwnerName', '')
        name = window.get('kCGWindowName', '')
        if 'Minecraft' in owner_name or 'java' in owner_name:
            bounds = window.get('kCGWindowBounds')
            print(f"[DEBUG] Знайдено вікно: {owner_name} - {name}")
            print(f"[DEBUG] Bounds: {bounds}")
            return {
                'top': int(bounds['Y']),
                'left': int(bounds['X']),
                'width': int(bounds['Width']),
                'height': int(bounds['Height'])
            }
    raise RuntimeError("Minecraft window not found")

def save_minecraft_screenshot():
    monitor = get_minecraft_bounds()

    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        cv2.imwrite("screenshot.png", cv2.cvtColor(img, cv2.COLOR_BGRA2BGR))
        print("✅ Скриншот збережено як 'screenshot.png'")

if __name__ == "__main__":
    save_minecraft_screenshot()