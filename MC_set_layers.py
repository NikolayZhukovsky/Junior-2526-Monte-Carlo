import sys
from typing import Dict, List, Tuple, Optional

from PySide6.QtWidgets import (
    QApplication, QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTabWidget, QWidget, QGridLayout, QGroupBox, QDoubleSpinBox, QLineEdit, QCheckBox
)

from PySide6.QtCore import Qt, Signal
from MC_reading_csv import get_coefficients_for

COEF = []

class LayerEditor(QWidget):
    """
    Виджет редактирования границ одного слоя.
    """
    boundaries_changed = Signal()

    def __init__(self, name: str, start_mm: float, end_mm: float, parent=None):
        super().__init__(parent)
        self.name = name
        self._build_ui(start_mm, end_mm)

    def _build_ui(self, start_mm: float, end_mm: float):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_name = QLabel(self.name)
        self.lbl_name.setFixedWidth(150)

        self.sb_start = QDoubleSpinBox()
        self.sb_start.setRange(0.0, 50.0)
        self.sb_start.setSingleStep(0.1)
        self.sb_start.setDecimals(1)
        self.sb_start.setValue(start_mm)

        self.sb_end = QDoubleSpinBox()
        self.sb_end.setRange(0.0, 50.0)
        self.sb_end.setSingleStep(0.1)
        self.sb_end.setDecimals(1)
        self.sb_end.setValue(end_mm)

        self.lbl_mm_start = QLabel("мм (верх)")
        self.lbl_mm_end = QLabel("мм (низ)")

        layout.addWidget(self.lbl_name)
        layout.addWidget(self.sb_start)
        layout.addWidget(self.lbl_mm_start)
        layout.addWidget(self.sb_end)
        layout.addWidget(self.lbl_mm_end)

        # Обработчик изменения границ
        self.sb_start.valueChanged.connect(self._on_boundary_changed)
        self.sb_end.valueChanged.connect(self._on_boundary_changed)

    def _on_boundary_changed(self):
        self.boundaries_changed.emit()

    def get_boundaries(self) -> Tuple[float, float]:
        return float(self.sb_start.value()), float(self.sb_end.value())

    def set_boundaries(self, start_mm: float, end_mm: float):
        self.sb_start.blockSignals(True)
        self.sb_end.blockSignals(True)
        self.sb_start.setValue(start_mm)
        self.sb_end.setValue(end_mm)
        self.sb_start.blockSignals(False)
        self.sb_end.blockSignals(False)

    def set_read_only(self, ro: bool):
        self.sb_start.setReadOnly(ro)
        self.sb_end.setReadOnly(ro)


class LayerCoeffsDisplay(QWidget):
    """
    Плашка отображения коэффициентов mu_a, mu_s, g, n для слоя.

    В реальной интеграции значения приходят из внешнего файла (для выбраннойλ).
    Здесь предусмотрено место под вывод значений и кнопка "Обновить данные" (stub).
    """

    def __init__(self, layer_name: str, parent=None):
        super().__init__(parent)
        self.layer_name = layer_name
        self._build_ui()

    def _build_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        row = 0

        self.lbl_layer = QLabel(f"Коэффициенты для слоя: {self.layer_name}")
        self.lbl_layer.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.lbl_layer, row, 0, 1, 4)
        row += 1

        # Заголовки полей
        layout.addWidget(QLabel("mu_a"), row, 0)
        layout.addWidget(QLabel("mu_s"), row, 1)
        layout.addWidget(QLabel("g"), row, 2)
        layout.addWidget(QLabel("n"), row, 3)
        row += 1

        # Значения — читаемость как read-only поля (во внешнем IO вы заполняете эти поля)
        self.le_mu_a = QLineEdit()
        self.le_mu_s = QLineEdit()
        self.le_g = QLineEdit()
        self.le_n = QLineEdit()

        for w in (self.le_mu_a, self.le_mu_s, self.le_g, self.le_n):
            w.setReadOnly(True)
            w.setFixedWidth(120)

        layout.addWidget(self.le_mu_a, row, 0)
        layout.addWidget(self.le_mu_s, row, 1)
        layout.addWidget(self.le_g, row, 2)
        layout.addWidget(self.le_n, row, 3)

        # row += 1
        # self.btn_update = QPushButton("Обновить данные (stub)")
        # self.btn_update.setEnabled(False)  # настройте подключение к реальной функции IO
        # layout.addWidget(self.btn_update, row, 0, 1, 4)

    def update_values(self, mu_a: float, mu_s: float, g: float, n: float):
        """Обновление отображаемых значений коэффициентов."""
        self.le_mu_a.setText(f"{mu_a:.6g}")
        self.le_mu_s.setText(f"{mu_s:.6g}")
        self.le_g.setText(f"{g:.6g}")
        self.le_n.setText(f"{n:.6g}")

    def clear(self):
        self.update_values(0.0, 0.0, 0.0, 0.0)


class LayerCoeffEditor(QWidget):
    """
    Виджет для редактирования коэффициентов изотропного рассеяния для одного слоя:
    mu_s, mu_a, g, n
    """

    def __init__(self, layer_name: str, parent=None):
        super().__init__(parent)
        self.layer_name = layer_name

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.lbl = QLabel(layer_name)
        layout.addWidget(self.lbl)

        # mu_s
        layout.addWidget(QLabel("mu_s"))
        self.sb_mu_s = QDoubleSpinBox()
        self.sb_mu_s.setRange(0.0, 1e6)
        self.sb_mu_s.setDecimals(6)
        self.sb_mu_s.setValue(0.0)
        layout.addWidget(self.sb_mu_s)

        # mu_a
        layout.addWidget(QLabel("mu_a"))
        self.sb_mu_a = QDoubleSpinBox()
        self.sb_mu_a.setRange(0.0, 1e6)
        self.sb_mu_a.setDecimals(6)
        self.sb_mu_a.setValue(0.0)
        layout.addWidget(self.sb_mu_a)

        # g
        layout.addWidget(QLabel("g"))
        self.sb_g = QDoubleSpinBox()
        self.sb_g.setRange(-1.0, 1.0)
        self.sb_g.setDecimals(6)
        self.sb_g.setValue(0.0)
        layout.addWidget(self.sb_g)

        # n (показатель преломления)
        layout.addWidget(QLabel("n"))
        self.sb_n = QDoubleSpinBox()
        self.sb_n.setRange(1.0, 5.0)
        self.sb_n.setDecimals(6)
        self.sb_n.setValue(1.0)
        layout.addWidget(self.sb_n)

    def get_coeffs(self) -> Tuple[float, float, float, float]:
        """
        Возвращает текущие значения коэффициентов (mu_s, mu_a, g, n)
        """
        return (
            float(self.sb_mu_s.value()),
            float(self.sb_mu_a.value()),
            float(self.sb_g.value()),
            float(self.sb_n.value()),
        )

    def set_coeffs(self, mu_s: float = 0.0, mu_a: float = 0.0, g: float = 0.0, n: float = 1.0):
        """Установить значения коэффициентов."""
        self.sb_mu_s.setValue(mu_s)
        self.sb_mu_a.setValue(mu_a)
        self.sb_g.setValue(g)
        self.sb_n.setValue(n)


class IsotropicCoeffPanel(QWidget):
    """
    Панель для ввода четырех коэффициентов mu_s, mu_a, g, n
    для одного слоя. При инициализации принимается словарь
    текущих значений: {"mu_s": ..., "mu_a": ..., "g": ..., "n": ...}.
    В окне создаются четыре поля ввода. Возвращается новый словарь
    значений через метод get_coeffs().
    """

    def __init__(self, initial: Optional[Dict[str, float]] = None, layer_name: str = "Layer", parent=None):
        super().__init__(parent)
        self.layer_name = layer_name
        self._build_ui()
        if initial:
            self.set_coeffs(initial)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(8)

        # Рамочный блок с коэффициентами
        group_box = QGroupBox("Коэффициенты рассеяния")
        group_layout = QHBoxLayout(group_box)
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(8)

        # mu_a
        group_layout.addWidget(QLabel("Поглощение (mu_a):"))
        self.sb_mu_a = QDoubleSpinBox()
        self.sb_mu_a.setRange(0.0, 500.0)
        self.sb_mu_a.setDecimals(1)
        self.sb_mu_a.setSingleStep(0.1)
        self.sb_mu_a.setValue(0.0)
        group_layout.addWidget(self.sb_mu_a)

        # mu_s
        group_layout.addWidget(QLabel("Рассеяние (mu_s):"))
        self.sb_mu_s = QDoubleSpinBox()
        self.sb_mu_s.setRange(0.0, 500.0)
        self.sb_mu_s.setDecimals(1)
        self.sb_mu_s.setSingleStep(0.1)
        self.sb_mu_s.setValue(0.0)
        group_layout.addWidget(self.sb_mu_s)

        # g
        group_layout.addWidget(QLabel("Анизотропия рассеивания (g):"))
        self.sb_g = QDoubleSpinBox()
        self.sb_g.setRange(0, 20.0)
        self.sb_g.setDecimals(1)
        self.sb_g.setSingleStep(0.1)
        self.sb_g.setValue(0.0)
        group_layout.addWidget(self.sb_g)

        # n
        group_layout.addWidget(QLabel("Преломление (n):"))
        self.sb_n = QDoubleSpinBox()
        self.sb_n.setRange(1.0, 20.0)
        self.sb_n.setDecimals(1)
        self.sb_n.setSingleStep(0.1)
        self.sb_n.setValue(1.0)
        group_layout.addWidget(self.sb_n)

        main_layout.addWidget(group_box)
        main_layout.addStretch()  # чтобы блок располагался вверху

    def get_coeffs(self) -> Dict[str, float]:
        """
        Возвращает текущие значения коэффициентов как словарь.
        """
        return {
            "mu_s": round(float(self.sb_mu_s.value()), 2),
            "mu_a": round(float(self.sb_mu_a.value()), 2),
            "g": round(float(self.sb_g.value()), 2),
            "n": round(float(self.sb_n.value()), 2),
        }

    def set_coeffs(self, data: Dict[str, float]):
        """
        Установить значения коэффициентов из словаря.
        Ожидаются ключи: "mu_s", "mu_a", "g", "n".
        """
        self.sb_mu_s.setValue(float(data.get("mu_s", 0.0)))
        self.sb_mu_a.setValue(float(data.get("mu_a", 0.0)))
        self.sb_g.setValue(float(data.get("g", 0.0)))
        self.sb_n.setValue(float(data.get("n", 1.0)))


class LayerCoeffEditor(QWidget):
    """
    Виджет для редактирования коэффициентов изотропного рассеяния для одного слоя:
    mu_s, mu_a, g, n
    """

    def __init__(self, layer_name: str, initial: Optional[Dict[str, float]] = None, parent=None):
        super().__init__(parent)
        self.layer_name = layer_name

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.lbl = QLabel(layer_name)
        layout.addWidget(self.lbl)

        # mu_s
        layout.addWidget(QLabel("mu_s"))
        self.sb_mu_s = QDoubleSpinBox()
        self.sb_mu_s.setRange(0.0, 1e6)
        self.sb_mu_s.setDecimals(6)
        self.sb_mu_s.setValue(0.0)
        layout.addWidget(self.sb_mu_s)

        # mu_a
        layout.addWidget(QLabel("mu_a"))
        self.sb_mu_a = QDoubleSpinBox()
        self.sb_mu_a.setRange(0.0, 1e6)
        self.sb_mu_a.setDecimals(6)
        self.sb_mu_a.setValue(0.0)
        layout.addWidget(self.sb_mu_a)

        # g
        layout.addWidget(QLabel("g"))
        self.sb_g = QDoubleSpinBox()
        self.sb_g.setRange(-1.0, 1.0)
        self.sb_g.setDecimals(6)
        self.sb_g.setValue(0.0)
        layout.addWidget(self.sb_g)

        # n (показатель преломления)
        layout.addWidget(QLabel("n"))
        self.sb_n = QDoubleSpinBox()
        self.sb_n.setRange(1.0, 5.0)
        self.sb_n.setDecimals(6)
        self.sb_n.setValue(1.0)
        layout.addWidget(self.sb_n)

        # Установить начальные значения, если переданы
        if initial:
            self.set_coeffs(
                mu_s=initial.get("mu_s", 0.0),
                mu_a=initial.get("mu_a", 0.0),
                g=initial.get("g", 0.0),
                n=initial.get("n", 1.0),
            )

    def get_coeffs(self) -> Tuple[float, float, float, float]:
        """
        Возвращает текущие значения коэффициентов (mu_s, mu_a, g, n)
        """
        return (
            float(self.sb_mu_s.value()),
            float(self.sb_mu_a.value()),
            float(self.sb_g.value()),
            float(self.sb_n.value()),
        )

    def set_coeffs(self, mu_s: float = 0.0, mu_a: float = 0.0, g: float = 0.0, n: float = 1.0):
        """Установить значения коэффициентов."""
        self.sb_mu_s.setValue(mu_s)
        self.sb_mu_a.setValue(mu_a)
        self.sb_g.setValue(g)
        self.sb_n.setValue(n)

    # Панель: несколько слоёв, каждый слой имеет четыре поля ввода
    class IsotropicCoeffPanel(QWidget):
        """
        Панель для ввода коэффициентов mu_s, mu_a, g, n для изотропного рассеяния
        по каждому слою. При инициализации принимается словарь текущих значений по слоям.

        layers_def: List[Tuple[str, float, float]]  # список слоёв (имя, старт_mm, конец_mm)
        initial_coeffs: Optional[Dict[str, Dict[str, float]]]  # словарь для каждого слоя:
            { "Layer 1": {"mu_s": ..., "mu_a": ..., "g": ..., "n": ...}, ... }
        """

        def __init__(
                self,
                layers_def: List[Tuple[str, float, float]],
                initial_coeffs: Optional[Dict[str, Dict[str, float]]] = None,
                parent=None
        ):
            super().__init__(parent)
            self.layers_def = layers_def
            self.layer_editors: List[LayerCoeffEditor] = []
            self._build_ui(initial_coeffs or {})

        def _build_ui(self, initial_coeffs: Dict[str, Dict[str, float]]):
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(6, 6, 6, 6)
            main_layout.setSpacing(8)

            # Раздел коэффициентов по слоям
            coeffs_group = QWidget()
            coeffs_layout = QVBoxLayout(coeffs_group)
            coeffs_layout.setContentsMargins(0, 0, 0, 0)
            coeffs_layout.setSpacing(6)

            for layer_name, _, _ in self.layers_def:
                init = initial_coeffs.get(layer_name, None) if initial_coeffs else None
                editor = LayerCoeffEditor(layer_name, initial=init, parent=self)
                self.layer_editors.append(editor)
                coeffs_layout.addWidget(editor)

            main_layout.addWidget(coeffs_group)

            main_layout.addStretch()

        def get_coeffs_per_layer(self) -> List[Tuple[str, float, float, float, float]]:
            """
            Возвращает коэффициенты по слоям:
            [(layer_name, mu_s, mu_a, g, n), ...]
            """
            res: List[Tuple[str, float, float, float, float]] = []
            for editor in self.layer_editors:
                mu_s, mu_a, g, n = editor.get_coeffs()
                res.append((editor.layer_name, mu_s, mu_a, g, n))
            return res

        def set_coeffs_per_layer(self, data: Dict[str, Dict[str, float]]):
            """
            Обновить коэффициенты для слоёв.
            data: dict[layer_name] -> {"mu_s": ..., "mu_a": ..., "g": ..., "n": ...}
            """
            for editor in self.layer_editors:
                if editor.layer_name in data:
                    d = data[editor.layer_name]
                    editor.set_coeffs(
                        mu_s=d.get("mu_s", 0.0),
                        mu_a=d.get("mu_a", 0.0),
                        g=d.get("g", 0.0),
                        n=d.get("n", 1.0),
                    )

        def set_layers_wave_coeffs(self, coeffs_per_layer: Dict[str, Dict[str, float]]):
            """
            Аналогично set_coeffs_per_layer, но для совместимости с существующим API.
            coeffs_per_layer: dict[layer_name] -> {"mu_s":, "mu_a":, "g":, "n":}
            """
            self.set_coeffs_per_layer(coeffs_per_layer)


class ScenarioPanel(QWidget):
    """
    Панель для сценария (A или B): содержит список слоёв и область коэффициентов.
    """

    def __init__(self, name: str, layers_def: List[Tuple[str, float, float]], wave=650, parent=None):
        super().__init__(parent)
        self.name = name
        self.wave = wave
        self.layers_def = layers_def  # list of (layer_name, start_mm, end_mm)
        self.layer_editors: List[LayerEditor] = []
        self.coeffs_displays: List[LayerCoeffsDisplay] = []
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(8)

        # Раздел коэффициентов (для выбранной λ - вывод из файла)
        coeffs_box = QGroupBox(f"Коэффициенты оптических свойств (для выбранной λ = {self.wave} нм)")
        coeffs_layout = QVBoxLayout(coeffs_box)

        # Архив отображения коэффициентов по слоям
        for (layer_name, _, _) in self.layers_def:
            disp = LayerCoeffsDisplay(layer_name, self)
            self.coeffs_displays.append(disp)
            coeffs_layout.addWidget(disp)

        main_layout.addWidget(coeffs_box)

        # Раздел слоев
        layers_box = QGroupBox("Слои и их границы (верх/низ, мм)")
        layers_layout = QVBoxLayout(layers_box)

        # Параллельно создаём виджеты слоёв
        for name, s, e in self.layers_def:
            editor = LayerEditor(name, s, e, self)
            editor.boundaries_changed.connect(self._on_boundaries_changed)
            self.layer_editors.append(editor)
            layers_layout.addWidget(editor)

        main_layout.addWidget(layers_box)

        # Панель управления границами (опционально — можно включить/отключить синхронизацию)
        ctrl_layout = QHBoxLayout()
        self.cb_link = QCheckBox(
            "Синхронизировать границы слоёв (верхний границы следующего слоя = нижняя граница предыдущего)")
        self.cb_link.setChecked(True)
        ctrl_layout.addWidget(self.cb_link)
        ctrl_layout.addStretch()
        main_layout.addLayout(ctrl_layout)

        # Подвал панели
        main_layout.addStretch()

    def _on_boundaries_changed(self):
        """Контроль последовательности слоёв и при необходимости синхронизация границ."""
        if not self.cb_link.isChecked():
            return
        # Пример простейшей синхронизации: нижняя граница i-го слоя = верхняя граница (i+1)-го слоя
        for i in range(len(self.layer_editors) - 1):
            end_i = self.layer_editors[i].sb_end.value()
            start_next = self.layer_editors[i + 1].sb_start.value()
            if abs(end_i - start_next) > 1e-6:
                # синхронизируем нижнюю границу i-го слоя с верхней границей следующего
                self.layer_editors[i].sb_end.blockSignals(True)
                self.layer_editors[i].sb_end.setValue(start_next)
                self.layer_editors[i].sb_end.blockSignals(False)
        # Можно реализовать более сложную логику, если нужно

    def get_layers(self) -> List[Tuple[str, float, float]]:
        """Возвращает текущие границы слоёв: [(name, start_mm, end_mm), ...]"""
        res = []
        for ed in self.layer_editors:
            s, e = ed.get_boundaries()
            res.append((ed.name, s, e))
        return res

    def set_wave_coeffs(self, coeffs_per_layer: Dict[str, Dict[str, float]]):
        """
        Обновить значения mu_a, mu_s, g, n для каждого слоя по данным from external file.

        coeffs_per_layer: dict[layer_name] -> {"mu_a":, "mu_s":, "g":, "n":}
        """
        for disp in self.coeffs_displays:
            layer = disp.layer_name
            if layer in coeffs_per_layer:
                d = coeffs_per_layer[layer]
                disp.update_values(d.get("mu_a", 0.0),
                                   d.get("mu_s", 0.0),
                                   d.get("g", 0.0),
                                   d.get("n", 1.0))
            else:
                disp.clear()


class OpticalLayersDialog(QDialog):
    """
    Диалоговое окно с двумя сценариями А и B.
    """

    def __init__(self, coefs, wave=650, parent=None, new_a=None, new_b=None):
        super().__init__(parent)
        self.setWindowTitle("Конфигурация слоёв тканей и параметры распространения лазера")
        self.resize(900, 450)
        self.curr_coef = coefs

        self.wave_length_nm = wave  # текущая длина волны (nm)
        self.wave_label: QLabel = QLabel("λ: не задано")

        self._build_ui(new_a, new_b)

    def _build_ui(self, new_a=None, new_b=None):
        main_layout = QVBoxLayout(self)

        # Вкладки сценариев
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Сценарий A: поверхностная задача (эпидермис + верхняя дерма)
        # layers_a = [
        #     ("Эпидермис", 0.0, 4),
        #     ("Дерма", 4, 10.0),
        # ]
        layers_a = new_a
        # self.set_wave_length_mm(nm=350)
        self.panel_a = ScenarioPanel("Сценарий A: поверхностная задача", layers_a, wave=self.wave_length_nm)
        self.tabs.addTab(self.panel_a, "Поверхностная задача")

        # Сценарий B: глубинная терапия (эпидермис + дерма + гиподерма до 30 мм)
        # layers_b = [
        #     ("Эпидермис", 0.0, 4),
        #     ("Дерма", 4, 8.0),
        #     ("Гипподерма", 8.0, 10.0),
        # ]
        layers_b = new_b
        self.panel_b = ScenarioPanel("Сценарий B: глубинная терапия", layers_b, self.wave_length_nm)
        self.tabs.addTab(self.panel_b, "Глубинная терапия")

        self.panel_c = IsotropicCoeffPanel(self.curr_coef)
        self.tabs.addTab(self.panel_c, "Изотропное рассеяние")

        # Низ окна
        btns_layout = QHBoxLayout()
        btns_layout.addStretch()
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Отмена")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        btns_layout.addWidget(self.btn_ok)
        btns_layout.addWidget(self.btn_cancel)
        main_layout.addLayout(btns_layout)

        self._load_coefficients_stub()

    def _load_coefficients_stub(self):
        """
        Заглушка под реальную загрузку коэффициентов из файла.
        В реальной интеграции сюда подставляйте вашу логику чтения файла.

        Ассоциация: λ выбирается из вашего внешнего файла; здесь предусмотрен вывод над
        данными mu_a/mu_s/g/n для каждого слоя.
        """
        # Пример: создаём тестовые данные для иллюстрации
        if self.wave_length_nm:
            wave = int(round(self.wave_length_nm))
        else:
            wave = 650

        mu_a_1, mu_s_1, g_1, n_1 = get_coefficients_for(tissue="Эпидермис_светлый", wavelength=wave,
                                                        method='linear').values()
        mu_a_2, mu_s_2, g_2, n_2 = get_coefficients_for(tissue="Дерма_человека", wavelength=wave,
                                                        method='linear').values()
        mu_a_3, mu_s_3, g_3, n_3 = get_coefficients_for(tissue="Подкожный_жир_n10", wavelength=wave,
                                                        method='linear').values()

        # print(mu_s_1, g_1, n_1)

        # Шаблон словаря: для каждого слоя задаём mu_a, mu_s, g, n
        # В реальности замените на чтение вашего файла.
        example_data = {
            "Сценарий A: поверхностная задача": {
                "Эпидермис": {"mu_a": mu_a_1, "mu_s": mu_s_1, "g": g_1, "n": n_1},
                "Дерма": {"mu_a": mu_a_2, "mu_s": mu_s_2, "g": g_2, "n": n_2},
            },
            "Сценарий B: глубинная терапия": {
                "Эпидермис": {"mu_a": mu_a_1, "mu_s": mu_s_1, "g": g_1, "n": n_1},
                "Дерма": {"mu_a": mu_a_2, "mu_s": mu_s_2, "g": g_2, "n": n_2},
                "Гипподерма": {"mu_a": mu_a_3, "mu_s": mu_s_3, "g": g_3, "n": n_3},
            },
        }

        # Пытаемся загрузить данные для активного волнового масштаба
        if self.wave_length_nm is not None:
            # В реальном случае ключ будет по λ, например: example_data[(wave_nm)]
            # Здесь в примере мы выбираем набор данных для сценария A и B по тексту
            for sc_name, sc_data in example_data.items():
                if sc_name == "Сценарий A: поверхностная задача":
                    self.panel_a.set_wave_coeffs(sc_data)
                    for layer_name, vals in sc_data.items():
                        pass  # Здесь уже обновлены в set_wave_coeffs
                elif sc_name == "Сценарий B: глубинная терапия":
                    self.panel_b.set_wave_coeffs(sc_data)

        # # Обновить надписи по волне на UI
        # self.set_wave_length_nm(self.wave_length_nm)

    def get_configuration(self) -> Dict[str, object]:
        """
        Собирает конфигурацию двух сценариев в общий словарь.
        Возвращает:
        {
            "wave_length_nm": float,
            "scenarios": {
                "A": {"layers": [(name, start, end), ...]},
                "B": {"layers": [(name, start, end), ...]},
            }
        }
        """
        cfg = {"wave_length_nm": self.wave_length_nm, "scenarios": {}}
        for key, panel in (("A", self.panel_a), ("B", self.panel_b)):
            layers = panel.get_layers()
            cfg["scenarios"][key] = {"layers": layers}
        return cfg

    def get_coefficients(self):
        return self.panel_c.get_coeffs()


def get_config(new_wave=650, curr_coef=None, new_layers_a=None, new_layers_b=None):
    # app = QApplication(sys.argv)
    if curr_coef is None: curr_coef = {"mu_s": 10, "mu_a": 10, "g": 9, "n": 1}
    dialog = OpticalLayersDialog(curr_coef, wave=new_wave, new_a=new_layers_a, new_b=new_layers_b)
    if dialog.exec() == QDialog.Accepted:
        config = dialog.get_configuration()
        coef = dialog.get_coefficients()
        # Здесь можно передать конфигурацию в модель/симулятор.
        # Пример вывода в консоль (для демонстрации):
        # print("Полученная конфигурация слоёв и параметров:")
        # print(config)
        return config, coef
    else:
        return {}, {}
    # sys.exit(0)


if __name__ == "__main__":
    curr_coef = {"mu_s": 10, "mu_a": 10, "g": 9, "n": 1}
    app = QApplication(sys.argv)
    dialog = OpticalLayersDialog(curr_coef, wave=650)
    if dialog.exec() == QDialog.Accepted:
        config = dialog.get_configuration()
        coef = dialog.get_coefficients()
        # Здесь можно передать конфигурацию в модель/симулятор.
        # Пример вывода в консоль (для демонстрации):
        print("Полученная конфигурация слоёв и параметров:")
        print(config)
        print(coef)
    sys.exit(0)
