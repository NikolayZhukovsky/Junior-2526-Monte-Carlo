from typing import Dict, Optional, Tuple


def get_optical_properties(tumor_type: str, wavelength: float, photosensitizer: Optional[str] = None) -> Dict[
    str, float]:
    """
    Определяет оптические коэффициенты (mu_a, mu_s, g, n) для опухоли,
    учитывая ее тип, окружающую ткань, длину волны лазера и фотосенсибилизатор.

    ЭТА ФУНКЦИЯ ЯВЛЯЕТСЯ ПРИМЕРОМ РЕАЛИЗАЦИИ И ТРЕБУЕТ НАПОЛНЕНИЯ РЕАЛЬНЫМИ
    ЭКСПЕРИМЕНТАЛЬНЫМИ ДАННЫМИ ИЛИ ИНТЕГРАЦИИ С ФИЗИЧЕСКИМИ МОДЕЛЯМИ.
    Представленные значения являются упрощенными и демонстрационными.

    Параметры:
        tumor_type (str): Тип опухоли (например, "меланома", "фиброма", "здоровая ткань").
        wavelength (float): Длина волны лазера в нанометрах (нм).
        photosensitizer (Optional[str]): Вводимый фотосенсибилизатор (например, "PpIX", "Вертепорфин"),
                                         или None, если не используется.
    """

    # --- База данных оптических свойств ---
    # Это упрощенная база данных. В реальном приложении потребуются более обширные
    # данные, возможно, с интерполяцией по длине волны.
    # Ключи для диапазонов длин волн заданы как кортежи (min_wavelength, max_wavelength).
    # Значения mu_a, mu_s в [см^-1], g, n безразмерные.
    optical_data = {
        "Меланома": {  # Опухоль с высоким содержанием меланина, сильнее поглощает в сине‑зелёном
            (350, 400): {"mu_a": 10.0, "mu_s": 350.0, "g": 0.78, "n": 1.41},
            (400, 500): {"mu_a": 5.0, "mu_s": 300.0, "g": 0.80, "n": 1.40},
            (500, 600): {"mu_a": 5.0, "mu_s": 220.0, "g": 0.83, "n": 1.395},
            (600, 700): {"mu_a": 1.0, "mu_s": 180.0, "g": 0.85, "n": 1.39}
        },
        "Базалиома": {  # Пример другого типа опухоли
            (350, 400): {"mu_a": 4.0, "mu_s": 190.0, "g": 0.85, "n": 1.39},
            (400, 500): {"mu_a": 3.5, "mu_s": 180.0, "g": 0.86, "n": 1.385},
            (500, 600): {"mu_a": 3.0, "mu_s": 170.0, "g": 0.865, "n": 1.382},
            (600, 700): {"mu_a": 2.5, "mu_s": 160.0, "g": 0.87, "n": 1.38}
        }
    }

    # --- Вклад поглощения фотосенсибилизаторами ---
    # Это также упрощенные данные, показывающие пики поглощения.
    # Ключи для диапазонов длин волн заданы как кортежи (min_wavelength, max_wavelength).
    # Значение - дополнительный вклад в mu_a (см^-1) на данных длинах волн.
    photosensitizer_absorption = {
        "PpIX": {  # Протопорфирин IX (часто образуется из 5-АЛК)
            (620, 650): 5.0,  # Пик поглощения в красном диапазоне (терапевтическое окно)
            (400, 420): 10.0  # Пик Соре (более сильное поглощение, но меньше проникновение)
        },
        "Вертепорфин": {  # Используется в ФДТ для макулярной дегенерации
            (680, 690): 4.0  # Пик поглощения
        },
        "Фотофрин": {  # Классический фотосенсибилизатор
            (625, 635): 6.0
        }
        # Здесь можно добавить другие фотосенсибилизаторы
    }

    # Инициализация результатов
    mu_a, mu_s, g, n = None, None, None, None

    tissue_tumor_properties = optical_data[tumor_type]
    for (min_wl, max_wl), props in tissue_tumor_properties.items():
        if min_wl <= wavelength <= max_wl:
            mu_a = props["mu_a"]
            mu_s = props["mu_s"]
            g = props["g"]
            n = props["n"]
            break

    if photosensitizer:
        ps_data = photosensitizer_absorption[photosensitizer]
        ps_found_wavelength_range = False
        for (min_wl_ps, max_wl_ps), ps_mu_a_contrib in ps_data.items():
            if min_wl_ps <= wavelength <= max_wl_ps:
                mu_a += ps_mu_a_contrib  # Добавляем вклад фотосенсибилизатора к базовому поглощению
                # print(f"Учтен '{photosensitizer}' в mu_a: +{ps_mu_a_contrib:.2f}")
                ps_found_wavelength_range = True
                break
        if not ps_found_wavelength_range:
            # print(f"'{photosensitizer}' не найдено специфического вклада {wavelength} нм.")
            pass

    return {"mu_a": mu_a, "mu_s": mu_s, "g": g, "n": n}


# --- Примеры использования функции ---
if __name__ == "__main__":
    # Пример 2: Меланома в коже при 630 нм с PpIX
    props_melanoma_skin_ppix = get_optical_properties("меланома", 630, "PpIX")
    print(f"Меланома в коже (630 нм, с PpIX): {props_melanoma_skin_ppix}")

    # Пример 4: Базалиома в коже при 690 нм с Вертепорфином
    props_basalioma_verteporfin = get_optical_properties("базалиома", 690, "Вертепорфин")
    print(f"Базалиома в коже (690 нм, с Вертепорфином): {props_basalioma_verteporfin}")
