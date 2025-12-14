import sys
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QLineEdit, QGroupBox, QLabel, QCheckBox, QSpinBox
)

from PySide6.QtCore import Qt
from MC_algo import get_data
from MC_set_layers import get_config
from MC_set_tumor import get_config_for_tumor

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib

matplotlib.rcParams['toolbar'] = 'None'


class MplCanvas(FigureCanvas):
    """Класс-холдер для Matplotlib Figure внутри PySide6."""

    def __init__(self, parent=None, width=6, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Junior_25-26 | Monte Carlo")
        self.resize(900, 700)

        self._photons_colorbar_ax = None  # отдельная ось под colorbar для photons
        self._photons_colorbar = None  # ссылка на сам colorbar

        # Данные по умолчанию (демо-данные; можно заменить на реальные)
        self.BINS = 51
        self.microns_per_bin = 100.0
        self.heat = []
        self.bit_value = 1.0
        self.photons_value = 10000
        self.wavelength = 650
        self.final_x = []
        self.final_z = []

        self.mu_a = 5.0
        self.mu_s = 95.0
        self.g = 0.5
        self.n = 1.5

        self.is_vessel = False
        self.is_heterogeneous = True
        self.is_tumor = True
        self.tumor_type_index = 0
        self.ps_type_index = 0

        # Хранение параметров опухоли
        self.tumor_params = {'cx': 7.5, 'cz': 4.5, 'rx': 2.6, 'rz': 4.0}

        self.layers_a = [("Эпидермис", 0.0, 3.5), ("Дерма", 3.5, 10.0)]
        self.layers_b = [("Эпидермис", 0.0, 2.5), ("Дерма", 2.5, 7.0), ("Гипподерма", 7.0, 12.0)]

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout(central_widget)

        self.params_widget = QWidget()
        params_layout = QVBoxLayout(self.params_widget)

        self.layout.addWidget(self.params_widget)

        # Верхняя и средняя панель: виджеты
        self.combo = QComboBox()
        self.combo.addItems([
            "Зависимость плотности нагрева от глубины",
            "Градиент распределения конечных координат фотонов (X vs Z)"
        ])
        self.combo.setCurrentIndex(1)

        self.btn_update = QPushButton("Update data")
        self.btn_save = QPushButton("Save plot")

        self.canvas1 = MplCanvas(self, width=8, height=6, dpi=100)
        self.canvas2 = MplCanvas(self, width=8, height=6, dpi=100)
        self.layout.addWidget(self.canvas1)

        self.combo_2 = QComboBox()
        self.combo_2.addItems([
            "Поверхностная задача",
            "Глубинная терапия",
            "Изотропное рассеяние"
        ])
        self.combo_2.setCurrentIndex(0)

        self.tumor_params_btn = QPushButton("Параметры опухоли")
        self.layers_btn = QPushButton("Параметры слоёв")
        self.isotropic_params_btn = QPushButton("Параметры изотропного рассеяния")

        # Сборка верхней и нижней панели
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.combo)
        control_layout.addWidget(self.combo_2)
        control_layout.addStretch()

        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.tumor_params_btn)
        settings_layout.addWidget(self.layers_btn)
        settings_layout.addWidget(self.btn_update)
        settings_layout.addWidget(self.btn_save)
        settings_layout.addStretch()

        self.layout.addLayout(control_layout)
        self.layout.addLayout(settings_layout)

        # ---- start: опции + поле для числа фотонов ----
        self.cb_vessel = QCheckBox("Сосуд")
        self.cb_vessel.setChecked(self.is_vessel)
        self.cb_vessel.stateChanged.connect(lambda s: self._on_flag_changed('is_vessel', s))


        self.cb_tumor = QCheckBox("Опухоль")
        self.cb_tumor.setChecked(self.is_tumor)
        self.cb_tumor.stateChanged.connect(lambda s: self._on_flag_changed('is_tumor', s))

        flags_box = QGroupBox("Опции:")
        flags_layout = QHBoxLayout()
        # flags_layout.addWidget(self.cb_vessel)
        flags_layout.addWidget(self.cb_tumor)
        # flags_layout.addStretch()
        flags_box.setLayout(flags_layout)

        # Блок справа: ввод числа фотонов
        photons_box = QGroupBox("Число фотонов:")
        p_layout = QHBoxLayout()
        self.photons_input = QSpinBox()
        self.photons_input.setRange(1, 10_000_000)
        self.photons_input.setSingleStep(10000)
        self.photons_input.setValue(int(self.photons_value))
        p_layout.addWidget(QLabel("Количество:"))
        p_layout.addWidget(self.photons_input)
        photons_box.setLayout(p_layout)

        # Блок справа: ввод длины волны
        wave_box = QGroupBox("Длина волны:")
        p_layout_2 = QHBoxLayout()
        self.wave_input = QSpinBox()
        self.wave_input.setRange(350, 700)
        self.wave_input.setSingleStep(25)
        self.wave_input.setValue(int(self.wavelength))
        p_layout_2.addWidget(QLabel("λ (нм):"))
        p_layout_2.addWidget(self.wave_input)
        wave_box.setLayout(p_layout_2)

        # params_layout.addWidget(opts_widget)

        opts_widget = QWidget()
        opts_layout = QHBoxLayout(opts_widget)
        opts_layout.addWidget(flags_box)
        opts_layout.addWidget(photons_box)
        opts_layout.addWidget(wave_box)
        opts_layout.addStretch()
        params_layout.insertWidget(0, opts_widget)

        # Подключаем сигнал изменения числа фотонов
        self.photons_input.valueChanged.connect(self._on_photons_changed)
        self.wave_input.valueChanged.connect(self._on_wavelength_changed)
        # ---- end ----

        # Подключения
        self.combo.currentIndexChanged.connect(self.update_plot)
        self.combo_2.currentIndexChanged.connect(self.update_mode)
        self.btn_update.clicked.connect(self.update_data)

        self.btn_save.clicked.connect(self.save_plot)

        self.tumor_params_btn.clicked.connect(self.open_tumor_params_dialog)
        self.layers_btn.clicked.connect(self.open_layer_dialog)

        # Первичный отрисов
        self.update_data()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.update_data()
            event.accept()
        else:
            super().keyPressEvent(event)

    def open_layer_dialog(self):
        config_in, coef_in = get_config(new_layers_a=self.layers_a, new_layers_b=self.layers_b,
                                        new_wave=self.wavelength,
                                        curr_coef={'mu_s': self.mu_s, 'mu_a': self.mu_a, 'g': self.g, 'n': self.n})
        if coef_in:
            self.mu_a, self.mu_s, self.g, self.n = coef_in['mu_a'], coef_in['mu_s'], coef_in['g'], coef_in['n']
        if config_in:
            self.layers_a = config_in['scenarios']['A']['layers']
            self.layers_b = config_in['scenarios']['B']['layers']
            print("Полученная конфигурация слоёв и параметров:", self.layers_a, self.layers_b)
        else:
            print("Изменения параметров опухоли отменены")
            return
        self.update_data()

    def open_tumor_params_dialog(self):
        config = get_config_for_tumor(new_wave=self.wavelength, curr_coef=self.tumor_params)
        if config:
            print(config)
            self.tumor_params = config['coefficients']
            self.tumor_type_index = config['tumor_type_index']
            self.ps_type_index = config['ps_type_index']
            self.update_data()
        else:
            print('Отмена')

    def _on_photons_changed(self, value):
        self.photons_value = int(value)

    def _on_wavelength_changed(self, value):
        self.wavelength = int(value)

    def _on_flag_changed(self, attr_name, state):
        setattr(self, attr_name, bool(state))

    def update_plot(self):
        idx = self.combo.currentIndex()
        if idx == 0:
            self.layout.removeWidget(self.canvas2)
            self.canvas1.setParent(None)
            self.layout.addWidget(self.canvas1)

            self.plot_heat_density()
        else:
            self.layout.removeWidget(self.canvas1)
            self.canvas1.setParent(None)
            self.layout.addWidget(self.canvas2)

            self.plot_photons()

    def update_mode(self):  # обработка изменения режима
        idx = self.combo_2.currentIndex()
        if idx == 0:
            self.is_heterogeneous = True
            self.update_data()
        elif idx == 1:
            self.is_heterogeneous = True
            self.update_data()
        else:
            self.is_heterogeneous = False
            self.update_data()
        return

    def update_data(self):
        curr_mode = ("", [])
        if self.combo_2.currentIndex() == 0:
            curr_mode = ('A', self.layers_a)
        elif self.combo_2.currentIndex() == 1:
            curr_mode = ('B', self.layers_b)
        res = get_data(self.mu_a, self.mu_s, self.g, self.n, new_is_vessel=self.is_vessel,
                       new_is_heterogeneous=self.is_heterogeneous, new_is_tumor=self.is_tumor,
                       new_photons=self.photons_value, new_wave=self.wavelength, new_cx=self.tumor_params['cx'],
                       new_cz=self.tumor_params['cz'], new_rx=self.tumor_params['rx'], new_rz=self.tumor_params['rz'],
                       new_mode=curr_mode, tt_index=self.tumor_type_index, ps_index=self.ps_type_index)
        heat_res, bit_res, self.final_x, self.final_z = res

        self.heat = heat_res
        self.bit_value = bit_res
        self.update_plot()

    def plot_heat_density_0(self):
        depths = [i * self.microns_per_bin / 1000 for i in range(self.BINS - 1)]
        densities = []
        for i in range(self.BINS - 1):
            val = self.heat[i] / self.microns_per_bin * 1e4 / (self.bit_value + self.photons_value)
            densities.append(val)

        self.canvas1.axes.clear()
        self.canvas1.axes.plot(depths, densities, marker='o', linestyle='-')
        self.canvas1.axes.set_xlabel('Depth (mm)')
        self.canvas1.axes.set_ylabel('Heat density (W/cm^3)')
        self.canvas1.axes.set_title('График зависимости плотности нагрева от глубины')
        self.canvas1.axes.grid(True)
        self.canvas1.draw()

    def save_plot(self):
        from pathlib import Path
        import re
        import os
        from PySide6.QtWidgets import QFileDialog

        def last_photons_index(dir_path, base='photons_XZ', ext='png'):
            dir_p = Path(dir_path)
            pattern_with = re.compile(rf'^{re.escape(base)}_(\d+)\.{re.escape(ext)}$')
            pattern_base = re.compile(rf'^{re.escape(base)}\.{re.escape(ext)}$')
            max_i = -1
            for f in dir_p.iterdir():
                if not f.is_file():
                    continue
                name = f.name
                m = pattern_with.match(name)
                if m:
                    idx = int(m.group(1))
                    if idx > max_i:
                        max_i = idx
                elif pattern_base.match(name):
                    max_i = max(max_i, 0)
            return max_i

        def next_photons_filename(dir_path, base='photons_XZ', ext='png', pad=4):
            last = last_photons_index(dir_path, base, ext)
            next_idx = last + 1
            return Path(dir_path) / f'{base}_{next_idx:0{pad}d}.{ext}'

        # Предполагаем стартовую директорию как текущую
        save_dir = os.getcwd()
        next_path = next_photons_filename(save_dir, base='photons_XZ', ext='png', pad=3)

        path, _ = QFileDialog.getSaveFileName(self, "Save photons plot",
                                              str(next_path),
                                              "PNG Image (*.png);;PDF Image (*.pdf);;SVG Image (*.svg)")
        if not path:
            return

        p = Path(path)
        if p.suffix == '':
            path = str(p.with_suffix('.png'))
        else:
            path = str(p)

        # Сохранение графика
        idx = self.combo.currentIndex()
        if idx == 0:
            plot = self.canvas1
        else:
            plot = self.canvas2
        plot.figure.savefig(path, dpi=300, bbox_inches='tight')
        print("Plot saved to", path)

    def plot_heat_density(self):
        # depths = [i * self.microns_per_bin / 1000 for i in range(self.BINS - 1)]
        # densities = []
        # for i in range(self.BINS - 1):
        #     val = self.heat[i] / self.microns_per_bin * 1e4 / (self.bit_value + self.photons_value)
        #     densities.append(val)

        depths = []
        densities = []
        t = 4 * 3.14159 * (self.microns_per_bin ** 3) * self.photons_value / 1e12
        for i in range(self.BINS - 1):
            r = i * self.microns_per_bin
            val = self.heat[i] / t / (i * i + i + 1.0 / 3.0)
            depths.append(r / 1000)
            densities.append(val)


        self.canvas1.axes.clear()
        self.canvas1.axes.plot(depths, densities, marker='o', linestyle='-')
        self.canvas1.axes.set_xlabel('Depth (mm)')
        self.canvas1.axes.set_ylabel('Heat density (W/cm^3)')
        self.canvas1.axes.set_title('График зависимости плотности нагрева от глубины')
        self.canvas1.axes.grid(True)

        from matplotlib.ticker import MultipleLocator
        self.canvas1.axes.xaxis.set_major_locator(MultipleLocator(0.5))

        self.canvas1.draw()

    def plot_photons(self):
        from matplotlib.colors import LinearSegmentedColormap

        nbins = 250
        xs = np.array(self.final_x)
        zs = np.array(self.final_z)

        colors = [
            # '#3b4b6e',
            '#0b1f4a',  # deep blue
            '#1f5eb3',  # blue
            '#2cc4d0',  # cyan
            '#4edb68',  # spring green / зелёный
            '#8bd72e',  # chartreuse
            '#f0d91a',  # yellow
            '#f07a1a',  # orange
            '#e23b3d',  # red
            '#7f0000'  # deep red
        ]

        contrast_cmap = LinearSegmentedColormap.from_list('contrast_rainbow', colors, N=256)

        self.canvas2.axes.clear()
        if xs.size == 0:
            self.canvas2.axes.text(0.5, 0.5, 'Нет данных для графика',
                                   transform=self.canvas2.axes.transAxes,
                                   ha='center', va='center')
            self.canvas2.draw()
            return
        mx_z = 0.6 * max(zs)
        if self.combo_2.currentIndex() == 0:
            mx_z = self.layers_a[1][2]
        elif self.combo_2.currentIndex() == 1:
            mx_z = self.layers_b[2][2]
        # mx_xs = [0.75 * min(xs), 0.75 * max(xs)]
        mx_xs = [-30, 30]

        H, xedges, zedges = np.histogram2d(xs, zs, bins=[nbins, nbins],
                                           range=[mx_xs, [-0.2, mx_z]])
        # H, xedges, zedges = np.histogram2d(xs, zs, bins=[nbins, nbins], range=[[-25, 25], [-0.2, 25]])
        H *= 2
        extent = [xedges[0], xedges[-1], zedges[0], zedges[-1]]
        im = self.canvas2.axes.imshow(H.T, extent=extent, origin='lower', aspect='auto', cmap=contrast_cmap)

        # Фиксируем объект colorbar (если он уже создан, обновляем его mappable)
        if not hasattr(self, '_photons_colorbar') or self._photons_colorbar is None:
            self._photons_colorbar = self.canvas2.figure.colorbar(im, ax=self.canvas2.axes, label='Number of photons')
        else:
            self._photons_colorbar.update_normal(im)

        self.canvas2.axes.set_xlabel('X final (mm)')
        self.canvas2.axes.set_ylabel('Z final (mm)')
        self.canvas2.axes.set_title('Градиент распределения конечных координат фотонов (X vs Z)')

        # Принудительно зафиксировать диапазоны осей
        self.canvas2.axes.set_xlim(extent[0], extent[1])
        self.canvas2.axes.set_ylim(extent[2], extent[3])

        from matplotlib.ticker import MultipleLocator
        self.canvas2.axes.xaxis.set_major_locator(MultipleLocator((0.75 * max(xs) - 0.75 * min(xs)) // 10))
        self.canvas2.axes.yaxis.set_major_locator(MultipleLocator(2))

        self.canvas2.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
