import math
import random
from MC_reading_csv import get_coefficients_for
from MC_reading_tumor_coef import get_optical_properties

BINS = 51
mu_a = 5.0  # поглощение, 1/cm
mu_s = 95.0  # рассеяние, 1/cm
g = 0.5  # анизотропия
n = 1.5  # индекс преломления
microns_per_bin = 100.0  # толщина одного bin слоя (микрон)

photons = 20000  # количество фотонов
wave = 650

# Глобальные переменные фотона
x = y = z = 0.0
u = v = 0.0
w = 1.0
weight = 0.0

# Результаты
rs = 0.0  # специальная рефлексия (до входа в medium)
albedo = 0.0
crit_angle = 0.0
bins_per_mfp = 0.0
heat = [0.0] * BINS
rd = 0.0  # backscattered energy
bit = 0.0  # сумма энергий для рулетки

final_x = []
final_z = []

# Параметры сосуда и фоновые оптические свойства (значения по умолчанию можно менять)
is_vessel = True  # включить/выключить сосуд
is_heterogeneous = True  # включить/выключить пространственную зависимость свойств
is_tumor = True  # включить/выключить опухоль

X_TRANS = 5.0

VESSEL_CENTER_X = -8.0
VESSEL_CENTER_Z = 3.5  # в микронах
VESSEL_RADIUS = 0.2  # радиус
BOUNDARY_THICKNESS = 0.2  # ширина переходной зоны в мкм (плавность)

TUMOR_CENTER_X = 7.5
TUMOR_CENTER_Z = 4.4
TUMOR_RADIUS_X = 2.6
TUMOR_RADIUS_Z = 1.7

MU_A_T = 5
MU_S_T = 180
G_T = 0.85
N_T = 1.39

# фоновые свойства (единицы: 1/cm для mu_a, mu_s; безразмерно для g; n — безразмерно)
MU_A_BG = mu_a
MU_S_BG = mu_s
G_BG = g
N_BG = n

# свойства сосуда (примерные контрастные значения)
MU_A_VESSEL = MU_A_BG * 20.0  # сосуд намного более поглощающий
MU_S_VESSEL = MU_S_BG * 0.9  # немного меньший сечением рассеяния
G_VESSEL = 0.35  # более изотропное рассеяние в содержимом сосуда
N_VESSEL = 1.36  # показатель преломления крови примерно 1.36

MODE = "A"
data_mode = []
COEF = []


def _vessel_weight(x, z, x0=VESSEL_CENTER_X, z0=VESSEL_CENTER_Z,
                   r_v=VESSEL_RADIUS, t=BOUNDARY_THICKNESS):
    """Плавный вес 0..1 — 1 внутри сосуда, 0 вне, сигмоида по радиусу (r в мкм)."""
    r = math.hypot(x - x0, z - z0)
    # сигмоидный переход: when r << r_v -> weight ~1, when r >> r_v -> ~0
    return 1.0 / (1.0 + math.exp((r - r_v) / t))


def coef_for_vessel(coef, coef_v):
    w = _vessel_weight(x, z)
    return coef * (1.0 - w) + coef_v * w


def coef_for_tumor(coef_tumor):
    x0, z0, rx, rz = TUMOR_CENTER_X, TUMOR_CENTER_Z, TUMOR_RADIUS_X, TUMOR_RADIUS_Z
    r2 = ((x - x0) / rx) ** 2 + ((z - z0) / rz) ** 2
    return coef_tumor * (1.0 + 4.0 * math.exp(-r2))
    # return MU_A_T * (1.0 + 4.0 * math.exp(-r2))


def coef_for_hetero(coef_main, coef_bg, coef_v, x0, z0):
    if is_vessel and is_tumor:
        if _vessel_weight(x0, z0) < 10 ** -3:
            return coef_for_tumor(coef_main)
        else:
            return coef_for_vessel(coef_bg, coef_v)
    if is_vessel:
        return coef_for_vessel(coef_bg, coef_v)
    if is_tumor:
        return coef_for_tumor(coef_main)
    return coef_main


def mu_a_at(x, z, mu_a_bg=MU_A_BG, mu_a_v=MU_A_VESSEL):
    mu_a_local_1 = COEF[0][0]
    mu_a_local_2 = COEF[1][0]
    mu_a_local_3 = COEF[2][0]
    if is_heterogeneous:
        if (MODE == 'A' and z < data_mode[0][2]) or (MODE == 'B' and z < data_mode[0][2]):
            return coef_for_hetero(mu_a_local_1, mu_a_bg, mu_a_v, x, z)
        else:
            if (MODE == 'A' and z >= data_mode[0][2]) or (MODE == 'B' and z < data_mode[1][2]):
                return coef_for_hetero(mu_a_local_2, mu_a_bg * 3, mu_a_v, x, z)
            elif MODE == 'B' and z >= data_mode[1][2]:
                return coef_for_hetero(mu_a_local_3, mu_a_bg * 1.5, mu_a_v, x, z)
    return mu_a


def mu_s_at(x, z, mu_s_bg=MU_S_BG, mu_s_v=MU_S_VESSEL):
    if is_heterogeneous:
        if is_vessel:
            return coef_for_vessel(mu_s_bg, mu_s_v)
        else:
            if (MODE == 'A' and z < data_mode[0][2]) or (MODE == 'B' and z < data_mode[0][2]):
                return COEF[0][1]
            else:
                if (MODE == 'A' and z >= data_mode[0][2]) or (MODE == 'B' and z < data_mode[1][2]):
                    return COEF[1][1]
                elif MODE == 'B' and z >= data_mode[1][2]:
                    return COEF[2][1]
    return mu_s


def g_at(x, z, g_bg=G_BG, g_v=G_VESSEL):
    if is_heterogeneous:
        if is_vessel:
            coef_for_vessel(g_bg, g_v)
        else:
            if (MODE == 'A' and z < data_mode[0][2]) or (MODE == 'B' and z < data_mode[0][2]):
                return COEF[0][2]
            else:
                if (MODE == 'A' and z >= data_mode[0][2]) or (MODE == 'B' and z < data_mode[1][2]):
                    return COEF[1][2]
                elif MODE == 'B' and z >= data_mode[1][2]:
                    return COEF[2][2]
    return g


def n_at(z, n_bg=N_BG, n_v=N_VESSEL):
    if is_heterogeneous:
        if is_vessel:
            return coef_for_vessel(n_bg, n_v)
        else:
            if (MODE == 'A' and z < data_mode[0][2]) or (MODE == 'B' and z < data_mode[0][2]):
                return COEF[0][3]
            else:
                if (MODE == 'A' and z >= data_mode[0][2]) or (MODE == 'B' and z < data_mode[1][2]):
                    return COEF[1][3]
                elif MODE == 'B' and z >= data_mode[1][2]:
                    return COEF[2][3]
    return n


def launch():
    global x, y, z, u, v, w, weight
    x = y = z = 0.0
    u = v = 0.0
    w = 1.0
    weight = 1.0 - rs


def bounce():
    global z, w, rd, weight
    n_local = n

    # if is_vessel:
    #     n_local = n_spatial(x, z)
    if is_heterogeneous:
        n_local = n_at(z)

    w = -w
    z = -z
    if w <= crit_angle:
        return
    t = math.sqrt(max(0.0, 1.0 - n_local * n_local * (1.0 - w * w)))
    temp1 = (w - n_local * t) / (w + n_local * t)
    temp = (t - n_local * w) / (t + n_local * w)
    rf = (temp1 * temp1 + temp * temp) / 2.0
    rd += (1.0 - rf) * weight
    weight -= (1.0 - rf) * weight


def move():
    global x, y, z, u, v, w
    r = random.random()
    d = -math.log(r if r > 0.0 else 1e-15)
    x += d * u
    y += d * v
    z += d * w
    if z <= 0.0:
        bounce()


def absorb():
    global heat, weight, bit

    mu_a_local = mu_a
    mu_s_local = mu_s

    if is_heterogeneous:
        mu_a_local = mu_a_at(x, z)
        mu_s_local = mu_s_at(x, z)

    albedo = mu_s_local / (mu_a_local + mu_s_local)

    dist = math.sqrt(x * x + y * y + z * z)
    bin_idx = int(dist * bins_per_mfp)
    if bin_idx < 0:
        bin_idx = 0
    if bin_idx >= BINS:
        bin_idx = BINS - 1
    heat[bin_idx] += (1.0 - albedo) * weight
    weight *= albedo

    if weight < 0.001:
        bit -= weight
        if random.random() > 0.1:
            final_x.append(x)
            final_z.append(z)
            weight = 0.0
        else:
            weight /= 0.1
        bit += weight


def scatter():
    global u, v, w  # Новое направление

    g_local = g
    # if is_vessel:
    #     g_local = g_spatial(x, z)
    if is_heterogeneous:
        g_local = g_at(x, z)

    while True:
        x1 = 2.0 * random.random() - 1.0
        x2 = 2.0 * random.random() - 1.0
        x3 = x1 * x1 + x2 * x2
        if x3 <= 1.0:
            break

    if g_local == 0.0:
        # изотропия
        u = 2.0 * x3 - 1.0
        denom = max(x3, 1e-12)
        factor = math.sqrt(max(0.0, (1.0 - u * u) / denom))
        v = x1 * factor
        w = x2 * factor
        return

    # Гамма-раскрытие Хение-Гринштейна
    r = random.random()
    mu = (1.0 - g_local * g_local) / (1.0 - g_local + 2.0 * g_local * r)
    mu = (1.0 + g_local * g_local - mu * mu) / (2.0 * g_local)
    if abs(w) < 0.9:
        denom1 = max(1.0 - w * w, 1e-12)
        a = math.sqrt(max(0.0, (1.0 - mu * mu) / denom1 / x3))
        t = mu * u + a * (x1 * u * w - x2 * v)
        b = math.sqrt(max(0.0, (1.0 - mu * mu) / denom1 / x3))
        v = mu * v + b * (x1 * v * w + x2 * u)
        c = math.sqrt(max(0.0, (1.0 - mu * mu) * (1.0 - w * w) / x3))
        w = mu * w - c * x1
        u = t
    else:
        denom2 = max(1.0 - v * v, 1e-12)
        a = math.sqrt(max(0.0, (1.0 - mu * mu) / denom2 / x3))
        t = mu * u + a * (x1 * u * v + x2 * w)
        b = math.sqrt(max(0.0, (1.0 - mu * mu) / denom2 / x3))
        w = mu * w + b * (x1 * v * w - x2 * u)
        c = math.sqrt(max(0.0, (1.0 - mu * mu) * (1.0 - v * v) / x3))
        v = mu * v - c * x1
        u = t


def print_results():
    print(f"Scattering = {mu_s:8.3f}/cm\nAbsorption = {mu_a:8.3f}/cm")
    print(f"Anisotropy = {g:8.3f}\nRefr Index = {n:8.3f}\nPhotons = {photons:8d}")
    print(f"\n\nSpecular Refl = {rs:10.5f}\nBackscattered Refl = {rd / (bit + photons):10.5f}")
    print(f"\n\n Depth Heat\n[microns] [W/cm^3]\n")
    for i in range(BINS - 1):
        depth = i * microns_per_bin
        value = heat[i] / microns_per_bin * 1e4 / (bit + photons)
        print(f"{depth:6.0f} {value:12.5f}")
    extra = heat[BINS - 1] / (bit + photons)
    print(f" extra {extra:12.5f}")


def run_mc():
    global rs, albedo, crit_angle, bins_per_mfp, heat, rd, bit

    albedo = mu_s / (mu_s + mu_a)
    rs = (n - 1.0) * (n - 1.0) / ((n + 1.0) * (n + 1.0))
    crit_angle = math.sqrt(max(0.0, 1.0 - 1.0 / (n * n)))
    bins_per_mfp = 1e4 / microns_per_bin / (mu_a + mu_s)

    heat = [0.0] * BINS
    rd = 0.0
    bit = 0.0

    for i in range(photons):
        if i == photons // 4:
            print('...25%')
        elif i == photons // 2:
            print('...50%')
        elif i == 3 * photons // 4:
            print('...75%')
        elif i == photons - 1:
            print('..100%')
        launch()
        while weight > 0:
            move()
            absorb()
            scatter()

    return heat, bit


def get_data(new_mu_a, new_mu_s, new_g, new_n, new_is_vessel=True, new_is_heterogeneous=True, new_is_tumor=True,
             new_photons=20000, new_wave=680, new_cx=7.5, new_cz=4.5, new_rx=2.5, new_rz=1.5, new_mode=None,
             tt_index=0, ps_index=0):
    global MU_A_T

    MU_A_T = get_optical_properties(["Меланома", "Базалиома"][tt_index], new_wave,
                                    ["PpIX", "Вертепорфин", "Фотофрин"][ps_index])['mu_a']
    print(f'mu_a_tumor: {MU_A_T}')
    global MODE, data_mode
    MODE = new_mode[0]
    data_mode = new_mode[1]
    # print(f'ALGO: {MODE} {data_mode}')
    global is_vessel, is_heterogeneous, is_tumor
    global photons, wave
    photons = new_photons // 2
    wave = new_wave
    is_vessel, is_heterogeneous, is_tumor = new_is_vessel, new_is_heterogeneous, new_is_tumor
    final_x.clear()
    final_z.clear()
    global mu_a, mu_s, g, n
    global MU_A_BG, MU_S_BG, G_BG, N_BG, MU_S_VESSEL, MU_A_VESSEL
    MU_A_BG, MU_S_BG, G_BG, N_BG = new_mu_a, new_mu_s, new_g, new_n
    MU_A_VESSEL, MU_S_VESSEL = MU_A_BG * 20.0, MU_S_BG * 0.9

    global TUMOR_CENTER_X, TUMOR_CENTER_Z, TUMOR_RADIUS_X, TUMOR_RADIUS_Z
    TUMOR_CENTER_X, TUMOR_CENTER_Z, TUMOR_RADIUS_X, TUMOR_RADIUS_Z = new_cx, new_cz, new_rx, new_rz

    mu_a_1, mu_s_1, g_1, n_1 = get_coefficients_for(tissue="Эпидермис_светлый", wavelength=wave,
                                                    method='linear').values()
    mu_a_2, mu_s_2, g_2, n_2 = get_coefficients_for(tissue="Дерма_человека", wavelength=wave,
                                                    method='linear').values()
    mu_a_3, mu_s_3, g_3, n_3 = get_coefficients_for(tissue="Подкожный_жир_n10", wavelength=wave,
                                                    method='linear').values()
    # mu_a = new_mu_a
    mu_a, mu_s, g, n = new_mu_a, new_mu_s, new_g, new_n
    global COEF
    COEF = [[mu_a_1, mu_s_1, g_1, n_1], [mu_a_2, mu_s_2, g_2, n_2], [mu_a_3, mu_s_3, g_3, n_3]]
    # mu_s, g, n = COEF[0]
    print(wave, ':', mu_a, mu_s, g, n)
    print(wave, ':', COEF)

    heat_res, bit_res = run_mc()
    return heat, bit_res, final_x, final_z


def main():
    get_data(5.0, 95.0, 0.5, 1.5, new_is_vessel=False,
             new_is_heterogeneous=True, new_is_tumor=True, new_photons=16000, new_wave=680)
    return


if __name__ == "__main__":
    main()
