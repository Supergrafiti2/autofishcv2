import cv2
import numpy as np
import mss
import os
import pyautogui
import time
import threading
import Quartz

def get_minecraft_bounds():
    options = Quartz.kCGWindowListOptionOnScreenOnly
    window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
    for window in window_list:
        owner_name = window.get('kCGWindowOwnerName', '')
        name = window.get('kCGWindowName', '')
        if 'java' in owner_name or 'java' in name:
            bounds = window.get('kCGWindowBounds')
            return {
                'top': int(bounds['Y']),
                'left': int(bounds['X']),
                'width': int(bounds['Width']),
                'height': int(bounds['Height'])
            }
    raise RuntimeError("Minecraft window not found")

monitor = get_minecraft_bounds()
screen_width, screen_height = monitor['width'], monitor['height']

# Параметри для перевірки зміни висоти
previous_position = None
displacement_threshold = 20  # Поріг зміщення по висоті (пикселів)
missing_threshold = 1 # Кількість пропусків поплавка перед правим кліком
missing_count = 1

# Завантаження зображень поплавків один раз
float_images = []
for filename in os.listdir("float_examples"):
    if filename.endswith('.png') or filename.endswith('.jpg'):
        float_image = cv2.imread(os.path.join("float_examples", filename), cv2.IMREAD_GRAYSCALE)
        float_images.append((filename, float_image))

# Функція для кліків миші
def right_click():
    pyautogui.click(button='right')
    time.sleep(0.3)
    pyautogui.click(button='right')
    time.sleep(1)

# Функція для обробки екрана
def process_screen(frame_data):
    global previous_position, missing_count

    print("Починаємо через 5 секунд...")
    time.sleep(5)

    with mss.mss() as sct:
        while True:
            # Захоплюємо поточний кадр екрана
            screenshot = sct.grab(monitor)

            # Перетворюємо його в масив NumPy
            img = np.array(screenshot)

            # Перетворюємо кадр в відтінки сірого
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)

            # Змінні для відслідковування найкращої знахідки
            best_match = None
            best_match_value = -1

            # Шукаємо шаблони (поплавки) на екрані
            for filename, float_image in float_images:
                # Використовуємо шаблонне порівняння
                float_image_resized = cv2.resize(float_image, (0, 0), fx=0.5, fy=0.5)
                result = cv2.matchTemplate(gray, float_image_resized, cv2.TM_CCOEFF_NORMED)

                # Знаходимо максимальний коефіцієнт
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                # Якщо знайдений кращий збіг, зберігаємо координати
                if max_val > best_match_value:
                    best_match_value = max_val
                    best_match = max_loc

            # Якщо знайдений хороший збіг, відображаємо його на екрані
            if best_match:
                top_left = best_match
                bottom_right = (top_left[0] + float_image.shape[1], top_left[1] + float_image.shape[0])

                # Відображаємо результат
                cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 2)

                # Виводимо координати
                print(f"Поплавок знайдено на координатах: {top_left}")

                # Якщо поплавок змістився вниз на певну кількість пікселів, робимо правий клік
                if previous_position:
                    delta_y = top_left[1] - previous_position[1]
                    if delta_y > displacement_threshold:
                        print("Поплавок сильно змістився вниз!")
                        right_click()

                # Оновлюємо попереднє положення
                previous_position = top_left
                missing_count = 0  # Скидаємо лічильник, якщо поплавок знайдено

            else:
                # Якщо поплавок не знайдений, збільшуємо лічильник відсутності
                missing_count += 1

                # Якщо поплавок не знайдений кілька разів, робимо правий клік
                if missing_count >= missing_threshold:
                    print("Поплавок не знайдений кілька разів, робимо правий клік!")
                    right_click()
                    missing_count = 0  # Скидаємо лічильник

            # Зменшуємо розмір зображення тільки для відображення результатів
            small_img = cv2.resize(img, (screen_width // 2, screen_height // 2))

            # Передаємо зображення для відображення в головний потік
            frame_data['frame'] = small_img
            time.sleep(0.03)  # Обмеження до ~30 FPS

# Головний потік програми
if __name__ == "__main__":
    frame_data = {}

    # Запускаємо функцію обробки екрана в окремому потоці
    process_thread = threading.Thread(target=process_screen, args=(frame_data,))
    process_thread.daemon = True
    process_thread.start()

    # Головний цикл програми
    while True:
        time.sleep(1)  # Зменшене використання CPU