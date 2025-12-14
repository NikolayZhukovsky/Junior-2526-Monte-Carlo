from PySide6.QtWidgets import (
    QDialog, QDoubleSpinBox, QComboBox, QDialogButtonBox, QLineEdit, QApplication, QGroupBox,
    QFormLayout,  QVBoxLayout
)

import sys
from MC_reading_tumor_coef import get_optical_properties


class TumorParamsDialog(QDialog):
    def __init__(self, parent=None, initial=None, wavelength_nm=None):
        super().__init__(parent)
        self.setWindowTitle("Параметры опухоли")

        # Длина волны (в нм) для расчета оптических свойств
        self.wavelength_nm = int(wavelength_nm) if wavelength_nm is not None else 650

        form = QFormLayout(self)

        # Координаты опухоли
        self.cx = QDoubleSpinBox()
        self.cx.setRange(-100.0, 100.0)
        self.cx.setDecimals(1)

        self.cz = QDoubleSpinBox()
        self.cz.setRange(0.0, 100.0)
        self.cz.setDecimals(1)

        self.rx = QDoubleSpinBox()
        self.rx.setRange(0.0, 50.0)
        self.rx.setDecimals(1)

        self.rz = QDoubleSpinBox()
        self.rz.setRange(0.0, 100.0)
        self.rz.setDecimals(1)

        # Тип опухоли
        self.tumor_box = QComboBox()
        # self.tumor_types = ['Меланома', 'Базалиома', 'Глиобластома', 'Аденокарцинома']
        self.tumor_types = ['Меланома', 'Базалиома']
        for t in self.tumor_types:
            self.tumor_box.addItem(t)

        # Тип фотосенсибилизатора
        self.ps_box = QComboBox()
        self.ps_types = ['PpIX', 'Вертепорфин', 'Фотофрин']
        for p in self.ps_types:
            self.ps_box.addItem(p)

        # Блок вывода оптических параметров
        # disp_g = QGroupBox(f'Коэффициенты (при λ = {self.wavelength_nm} нм)')
        # layout = QHBoxLayout()

        self.coeff_group = QGroupBox(f'Коэффициенты (при λ = {self.wavelength_nm} нм)')
        coeff_layout = QVBoxLayout(self.coeff_group)

        coeff_form = QFormLayout()  # для аккуратной подписи к каждому полю

        self.mu_a_disp = QLineEdit()
        self.mu_a_disp.setReadOnly(True)
        self.mu_s_disp = QLineEdit()
        self.mu_s_disp.setReadOnly(True)
        self.g_disp = QLineEdit()
        self.g_disp.setReadOnly(True)
        self.n_disp = QLineEdit()
        self.n_disp.setReadOnly(True)

        coeff_form.addRow("mu_a (1/см):", self.mu_a_disp)
        coeff_form.addRow("mu_s (1/см):", self.mu_s_disp)
        coeff_form.addRow("g:", self.g_disp)
        coeff_form.addRow("n:", self.n_disp)
        coeff_layout.addLayout(coeff_form)

        form.addRow("Center X (mm):", self.cx)
        form.addRow("Center Z (mm):", self.cz)
        form.addRow("Radius X (mm):", self.rx)
        form.addRow("Radius Z (mm):", self.rz)
        form.addRow("Тип опухоли:", self.tumor_box)
        form.addRow("Тип фотосенсибилизатора:", self.ps_box)
        form.addRow(self.coeff_group)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        form.addRow(self.button_box)

        # Заполнение начальными значениями (если переданы)
        if initial:
            self.cx.setValue(initial.get('cx', 7.5))
            self.cz.setValue(initial.get('cz', 4.5))
            self.rx.setValue(initial.get('rx', 2.5))
            self.rz.setValue(initial.get('rz', 4.0))

            if 'tumor_type_index' in initial:
                idx = int(initial['tumor_type_index'])
                if 0 <= idx < len(self.tumor_types):
                    self.tumor_box.setCurrentIndex(idx)
            if 'ps_type_index' in initial:
                idx = int(initial['ps_type_index'])
                if 0 <= idx < len(self.ps_types):
                    self.ps_box.setCurrentIndex(idx)

        else:
            self.tumor_box.setCurrentIndex(0)
            self.ps_box.setCurrentIndex(0)

        # Подключение к изменению выбора для обновления вывода
        self.tumor_box.currentIndexChanged.connect(self.update_optical_display)
        self.ps_box.currentIndexChanged.connect(self.update_optical_display)

        # Первый вывод
        self.update_optical_display()

    def update_optical_display(self):
        tumor_type = self.tumor_box.currentText()
        wavelength = self.wavelength_nm
        ps_type = self.ps_box.currentText()

        props = get_optical_properties(tumor_type, wavelength, ps_type)

        self.mu_a_disp.setText(f"{props.get('mu_a', 0.0):.2f}")
        self.mu_s_disp.setText(f"{props.get('mu_s', 0.0):.2f}")
        self.g_disp.setText(f"{props.get('g', 0.0):.2f}")
        self.n_disp.setText(f"{props.get('n', 1.0):.2f}")

    def get_values(self):
        return {
            'cx': self.cx.value(),
            'cz': self.cz.value(),
            'rx': self.rx.value(),
            'rz': self.rz.value(),
        }

    def export_data(self) -> dict:
        """
        Возвращает полный словарь параметров, включая индексы типов:
        - tumor_type_index: int (0..n)
        - ps_type_index: int (0..m)
        - tissue_type: str
        """
        return {
            'coefficients': {
                'cx': self.cx.value(),
                'cz': self.cz.value(),
                'rx': self.rx.value(),
                'rz': self.rz.value(),
            },
            'tumor_type_index': int(self.tumor_box.currentIndex()),
            'ps_type_index': int(self.ps_box.currentIndex()),
        }


def get_config_for_tumor(new_wave=650, curr_coef=None):
    dialog = TumorParamsDialog(initial=curr_coef, wavelength_nm=new_wave)
    if dialog.exec() == QDialog.Accepted:
        config = dialog.export_data()
        return config
    else:
        return None

if __name__ == "__main__":
    curr_coef = {'cx': 7.5, 'cz': 4.5, 'rx': 3.0, 'rz': 4.0}
    app = QApplication(sys.argv)
    dialog = TumorParamsDialog(initial=curr_coef, wavelength_nm=650)
    if dialog.exec() == QDialog.Accepted:
        config = dialog.export_data()
        # Здесь можно передать конфигурацию в модель/симулятор.
        # Пример вывода в консоль (для демонстрации):
        print("Полученная конфигурация слоёв и параметров:")
        print(config)
    sys.exit(0)
