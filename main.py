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

# Параметры для проверки изменения высоты
previous_position = None
displacement_threshold = 20  # Порог смещения по высоте (пикселей)
missing_threshold = 1 # Количество пропусков поплавка перед правым кликом
missing_count = 1

# Загрузка изображений поплавков один раз
float_images = []
for filename in os.listdir("float_examples"):
    if filename.endswith('.png') or filename.endswith('.jpg'):
        float_image = cv2.imread(os.path.join("float_examples", filename), cv2.IMREAD_GRAYSCALE)
        float_images.append((filename, float_image))

# Функция для кликов мыши
def right_click():
    pyautogui.click(button='right')
    time.sleep(0.3)
    pyautogui.click(button='right')
    time.sleep(1)

# Функция для обработки экрана
def process_screen(frame_data):
    global previous_position, missing_count

    print("Начинаем через 5 секунд...")
    time.sleep(5)

    with mss.mss() as sct:
        while True:
            # Захватываем текущий кадр экрана
            screenshot = sct.grab(monitor)

            # Преобразуем его в массив NumPy
            img = np.array(screenshot)

            # Переводим кадр в оттенки серого
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)

            # Переменные для отслеживания лучшего совпадения
            best_match = None
            best_match_value = -1

            # Ищем шаблоны (поплавки) на экране
            for filename, float_image in float_images:
                # Используем шаблонное сравнение
                float_image_resized = cv2.resize(float_image, (0, 0), fx=0.5, fy=0.5)
                result = cv2.matchTemplate(gray, float_image_resized, cv2.TM_CCOEFF_NORMED)

                # Находим максимальный коэффициент совпадения
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                # Если найдено лучшее совпадение, сохраняем координаты
                if max_val > best_match_value:
                    best_match_value = max_val
                    best_match = max_loc

            # Если найдено хорошее совпадение, отображаем его на экране
            if best_match:
                top_left = best_match
                bottom_right = (top_left[0] + float_image.shape[1], top_left[1] + float_image.shape[0])

                # Отображаем результат
                cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 2)

                # Выводим координаты
                print(f"Поплавок найден на координатах: {top_left}")

                # Если поплавок сместился вниз на определённое количество пикселей — делаем правый клик
                if previous_position:
                    delta_y = top_left[1] - previous_position[1]
                    if delta_y > displacement_threshold:
                        print("Поплавок сильно сместился вниз!")
                        right_click()

                # Обновляем предыдущее положение
                previous_position = top_left
                missing_count = 0  # Сброс счётчика, если поплавок найден

            else:
                # Если поплавок не найден — увеличиваем счётчик отсутствия
                missing_count += 1

                # Если поплавок не найден несколько раз — делаем правый клик
                if missing_count >= missing_threshold:
                    print("Поплавок не найден несколько раз, делаем правый клик!")
                    right_click()
                    missing_count = 0  # Сброс счётчика

            # Уменьшаем размер изображения только для отображения результатов
            small_img = cv2.resize(img, (screen_width // 2, screen_height // 2))

            # Передаём изображение для отображения в главный поток
            frame_data['frame'] = small_img
            time.sleep(0.03)  # Ограничение до ~30 FPS

# Главный поток программы
if __name__ == "__main__":
    frame_data = {}

    # Запускаем функцию обработки экрана в отдельном потоке
    process_thread = threading.Thread(target=process_screen, args=(frame_data,))
    process_thread.daemon = True
    process_thread.start()

    # Главный цикл программы
    while True:
        time.sleep(1)  # Меньшее использование CPU