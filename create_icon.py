from PIL import Image, ImageDraw

def draw_icon(size):
    """Рисует иконку ChatList: несколько пузырей чата на градиентном фоне."""
    # Создаем RGB изображение с градиентным фоном (от тёмно-синего к синему)
    img = Image.new("RGB", (size, size), (25, 35, 60))  # Тёмно-синий фон
    draw = ImageDraw.Draw(img)
    
    # Рисуем градиентный фон (простой вариант - радиальный градиент)
    center_x, center_y = size // 2, size // 2
    max_radius = int(size * 0.7)
    
    # Создаём градиент через несколько концентрических кругов
    for i in range(max_radius, 0, -5):
        alpha = int(255 * (1 - i / max_radius) * 0.3)
        color = (25 + alpha // 10, 35 + alpha // 8, 60 + alpha // 5)
        draw.ellipse([
            center_x - i, center_y - i,
            center_x + i, center_y + i
        ], fill=color)
    
    # Рисуем три пузыря чата разного размера (представляют список диалогов)
    bubble_colors = [
        (100, 150, 255),  # Светло-синий
        (80, 130, 240),   # Средний синий
        (60, 110, 220)    # Более тёмный синий
    ]
    
    # Первый пузырь (большой, слева вверху)
    bubble1_size = int(size * 0.35)
    bubble1_x = int(size * 0.3)
    bubble1_y = int(size * 0.25)
    bubble1_coords = [
        bubble1_x - bubble1_size // 2,
        bubble1_y - bubble1_size // 2,
        bubble1_x + bubble1_size // 2,
        bubble1_y + bubble1_size // 2
    ]
    draw.ellipse(bubble1_coords, fill=bubble_colors[0])
    # Хвостик пузыря
    tail_points = [
        (bubble1_x - bubble1_size // 4, bubble1_y + bubble1_size // 2),
        (bubble1_x - bubble1_size // 3, bubble1_y + bubble1_size // 2 + bubble1_size // 6),
        (bubble1_x - bubble1_size // 6, bubble1_y + bubble1_size // 2)
    ]
    draw.polygon(tail_points, fill=bubble_colors[0])
    
    # Второй пузырь (средний, справа внизу)
    bubble2_size = int(size * 0.28)
    bubble2_x = int(size * 0.7)
    bubble2_y = int(size * 0.65)
    bubble2_coords = [
        bubble2_x - bubble2_size // 2,
        bubble2_y - bubble2_size // 2,
        bubble2_x + bubble2_size // 2,
        bubble2_y + bubble2_size // 2
    ]
    draw.ellipse(bubble2_coords, fill=bubble_colors[1])
    # Хвостик пузыря (направлен в другую сторону)
    tail_points2 = [
        (bubble2_x + bubble2_size // 4, bubble2_y + bubble2_size // 2),
        (bubble2_x + bubble2_size // 3, bubble2_y + bubble2_size // 2 + bubble2_size // 6),
        (bubble2_x + bubble2_size // 6, bubble2_y + bubble2_size // 2)
    ]
    draw.polygon(tail_points2, fill=bubble_colors[1])
    
    # Третий пузырь (маленький, в центре справа)
    bubble3_size = int(size * 0.22)
    bubble3_x = int(size * 0.75)
    bubble3_y = int(size * 0.35)
    bubble3_coords = [
        bubble3_x - bubble3_size // 2,
        bubble3_y - bubble3_size // 2,
        bubble3_x + bubble3_size // 2,
        bubble3_y + bubble3_size // 2
    ]
    draw.ellipse(bubble3_coords, fill=bubble_colors[2])
    
    # Добавляем небольшие точки внутри пузырей (символизируют текст)
    dot_color = (255, 255, 255)  # Белый
    dot_size = max(2, size // 40)
    
    # Точки в первом пузыре
    draw.ellipse([
        bubble1_x - bubble1_size // 4 - dot_size,
        bubble1_y - dot_size,
        bubble1_x - bubble1_size // 4 + dot_size,
        bubble1_y + dot_size
    ], fill=dot_color)
    draw.ellipse([
        bubble1_x - dot_size,
        bubble1_y - dot_size,
        bubble1_x + dot_size,
        bubble1_y + dot_size
    ], fill=dot_color)
    draw.ellipse([
        bubble1_x + bubble1_size // 4 - dot_size,
        bubble1_y - dot_size,
        bubble1_x + bubble1_size // 4 + dot_size,
        bubble1_y + dot_size
    ], fill=dot_color)
    
    # Точки во втором пузыре
    draw.ellipse([
        bubble2_x - bubble2_size // 4 - dot_size,
        bubble2_y - dot_size,
        bubble2_x - bubble2_size // 4 + dot_size,
        bubble2_y + dot_size
    ], fill=dot_color)
    draw.ellipse([
        bubble2_x - dot_size,
        bubble2_y - dot_size,
        bubble2_x + dot_size,
        bubble2_y + dot_size
    ], fill=dot_color)
    
    # Точка в третьем пузыре
    draw.ellipse([
        bubble3_x - dot_size,
        bubble3_y - dot_size,
        bubble3_x + dot_size,
        bubble3_y + dot_size
    ], fill=dot_color)
    
    return img

# Размеры иконки
sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
icons = [draw_icon(s) for s, _ in sizes]

# Изображения уже в RGB режиме, просто убеждаемся
rgb_icons = []
for icon in icons:
    # Убеждаемся, что изображение в RGB режиме (не палитра)
    if icon.mode != "RGB":
        rgb_img = icon.convert("RGB")
    else:
        rgb_img = icon
    rgb_icons.append(rgb_img)

# Сохранение с явным указанием формата и цветов
# ВАЖНО: Изображения уже в RGB режиме с красным фоном, что гарантирует
# сохранение цветов и избегает автоматической конвертации в градации серого
try:
    rgb_icons[0].save(
        "app.ico",
        format="ICO",
        sizes=sizes,
        append_images=rgb_icons[1:]
    )
    print("[OK] Иконка 'app.ico' создана!")
    print("   Дизайн: три пузыря чата на градиентном фоне")
    print("   Символизирует: список диалогов с AI-моделями")
except Exception as e:
    print(f"[ERROR] Ошибка при сохранении: {e}")
    # Альтернативный способ - сохранить каждое изображение отдельно
    print("Попытка альтернативного метода сохранения...")
    rgb_icons[0].save("app.ico", format="ICO")
    print("[OK] Иконка 'app.ico' создана (только один размер)")