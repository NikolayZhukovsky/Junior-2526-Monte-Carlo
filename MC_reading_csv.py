import csv
from typing import Dict, List, Tuple

# Типы
CoeffEntry = Dict[str, float]  # например {'mu_s': ..., 'g': ..., 'n': ...}
TissueData = List[Tuple[float, CoeffEntry]]  # список (λ, coeffs)
AllData = Dict[str, TissueData]  # ткань -> список (λ, coeffs)


def _to_float_safe(s: str) -> float:
    s = s.strip()
    if not s:
        raise ValueError("Empty value")
    s = s.replace(',', '.')  # локализация: запятая -> точка
    return float(s)


def load_coefficients_csv(path: str, delimiter: str = ';') -> AllData:
    """
    Загружает коэффициенты из CSV файла.
    Формат файла:
    Ткань;λ;μa;μs;g;n
    ...
    """
    data: AllData = {}
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            if not row:
                continue
            # Пробуем разобрать строку как данные. Если строка - заголовок, она будет пропущена.
            if len(row) < 6:
                continue
            tissue = row[0].strip()

            lam_str = row[1].strip()
            mu_a_str = row[2].strip()
            mu_s_str = row[3].strip()
            g_str = row[4].strip()
            n_str = row[5].strip()

            # Пробуем преобразовать в float. Если не удалось, считаем, что это заголовок и пропускаем.
            try:
                lam = _to_float_safe(lam_str)
            except Exception:
                continue  # пропускаем заголовок или некорректную строку

            try:
                mu_a = _to_float_safe(mu_a_str)
                mu_s = _to_float_safe(mu_s_str)
                g = _to_float_safe(g_str)
                n = _to_float_safe(n_str)
            except Exception:
                continue  # пропускаем некорректную строку

            coeffs = {'mu_a': mu_a, 'mu_s': mu_s, 'g': g, 'n': n}
            if tissue not in data:
                data[tissue] = []
            data[tissue].append((lam, coeffs))

    # Сортируем по λ внутри каждой ткани для удобной интерполяции
    for tissue in data:
        data[tissue].sort(key=lambda item: item[0])

    return data


def get_coefficients_for(tissue: str, wavelength: float, method: str = 'nearest') -> CoeffEntry:
    """
    Возвращает коэффициенты для указанной ткани и длины волны.
    method:
      - 'nearest'  - возвращает коэффициенты при ближайшей λ
      - 'linear'   - линейная интерполяция между соседними λ
    Возвращает словарь {'mu_a': ..., 'mu_s': ..., 'g': ..., 'n': ...}
    """
    data = load_coefficients_csv("MC_parameters.csv", delimiter=';')

    if tissue not in data:
        raise KeyError(f"Unknown tissue type: {tissue}")
    entries = data[tissue]
    if not entries:
        raise ValueError(f"No coefficients for tissue {tissue}")

    lam_values = [lam for lam, _ in entries]
    coeffs_list = [coeff for _, coeff in entries]

    if method == 'neares':
        idx = min(range(len(lam_values)), key=lambda i: abs(lam_values[i] - wavelength))
        return coeffs_list[idx]

    if method == 'linear':
        # Если точное совпадение - вернем его
        for lam, coeff in entries:
            if lam == wavelength:
                return coeff

        # Найдем сегмент между lam[i] <= wavelength <= lam[i+1]
        if wavelength <= lam_values[0]:
            i = 0
            j = 0
        elif wavelength >= lam_values[-1]:
            i = len(lam_values) - 2
            j = len(lam_values) - 1 if len(lam_values) >= 2 else 0
        else:
            # найти индекс i максимального lam <= wavelength
            i = max(idx for idx in range(len(lam_values)) if lam_values[idx] <= wavelength)
            j = i + 1

        lam_i = lam_values[i]
        lam_j = lam_values[j]
        c_i = coeffs_list[i]
        c_j = coeffs_list[j]

        if lam_j == lam_i:
            return c_i

        t = (wavelength - lam_i) / (lam_j - lam_i)
        interp: CoeffEntry = {}
        for k in c_i.keys():
            interp[k] = c_i[k] + (c_j[k] - c_i[k]) * t
        return interp

    raise ValueError(f"Unknown method: {method}. Use 'nearest' or 'linear'.")
