from typing import Dict, Optional


def get_optical_properties(tumor_type: str, wavelength: float, photosensitizer: Optional[str] = None) -> Dict[
    str, float]:

    optical_data = {
        "Меланома": {
            (350, 400): {"mu_a": 10.0, "mu_s": 350.0, "g": 0.78, "n": 1.41},
            (400, 500): {"mu_a": 5.0, "mu_s": 300.0, "g": 0.80, "n": 1.40},
            (500, 600): {"mu_a": 5.0, "mu_s": 220.0, "g": 0.83, "n": 1.395},
            (600, 700): {"mu_a": 1.0, "mu_s": 180.0, "g": 0.85, "n": 1.39}
        },
        "Базалиома": {
            (350, 400): {"mu_a": 4.0, "mu_s": 190.0, "g": 0.85, "n": 1.39},
            (400, 500): {"mu_a": 3.5, "mu_s": 180.0, "g": 0.86, "n": 1.385},
            (500, 600): {"mu_a": 3.0, "mu_s": 170.0, "g": 0.865, "n": 1.382},
            (600, 700): {"mu_a": 2.5, "mu_s": 160.0, "g": 0.87, "n": 1.38}
        }
    }

    photosensitizer_absorption = {
        "PpIX": {
            (620, 650): 5.0,
            (400, 420): 10.0
        },
        "Вертепорфин": {
            (680, 690): 4.0
        },
        "Фотофрин": {
            (625, 635): 6.0
        }
    }

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
                mu_a += ps_mu_a_contrib
                ps_found_wavelength_range = True
                break
        if not ps_found_wavelength_range:
            pass

    return {"mu_a": mu_a, "mu_s": mu_s, "g": g, "n": n}
