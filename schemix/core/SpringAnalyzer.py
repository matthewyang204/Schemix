import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QWidget, QVBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QFormLayout, QMessageBox,
    QGroupBox, QGraphicsView, QGraphicsScene, QGraphicsPathItem
)
from PyQt6.QtGui import QFont, QDoubleValidator, QPen, QColor, QPainterPath
from PyQt6.QtCore import Qt, QRectF

MATERIAL_PROPERTIES = {
    "Music Wire (ASTM A228)": {"G": 80.0, "A": 2211, "m": 0.146, "rho": 7.85e-6},
    "Stainless Steel 302 (ASTM A313)": {"G": 69.0, "A": 1856, "m": 0.138, "rho": 8.00e-6},
    "Stainless Steel 17-7PH (ASTM A313)": {"G": 76.0, "A": 2296, "m": 0.081, "rho": 7.81e-6},
    "Chrome-Vanadium (ASTM A231)": {"G": 79.3, "A": 1969, "m": 0.155, "rho": 7.85e-6},
    "Chrome-Silicon (ASTM A401)": {"G": 79.3, "A": 2154, "m": 0.111, "rho": 7.85e-6},
    "Hard-Drawn MB (ASTM A227)": {"G": 79.3, "A": 1618, "m": 0.187, "rho": 7.85e-6},
    "Phosphor-Bronze (ASTM B159)": {"G": 41.4, "A": 1017, "m": 0.028, "rho": 8.80e-6},
    "Beryllium-Copper (ASTM B197)": {"G": 48.3, "A": 1582, "m": 0.042, "rho": 8.25e-6}
}

END_TYPE_COILS = {
    "Squared & Ground": {"Nt": "Na + 2"},
    "Squared Only": {"Nt": "Na + 2"},
    "Plain & Ground": {"Nt": "Na + 1"},
    "Plain Ends": {"Nt": "Na"}
}

END_CONDITIONS_BUCKLING = {
    "Fixed & Parallel": 0.5,
    "Pivoted & Parallel": 0.707,
    "Pivoted & Free": 2.0,
    "Fixed & Pivoted": 1.0
}

STANDARD_WIRE_DIAMETERS_MM = sorted([
    0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4,
    1.5, 1.6, 1.8, 2.0, 2.3, 2.5, 2.8, 3.0, 3.2, 3.5, 3.8, 4.0, 4.5, 5.0, 5.5,
    6.0, 6.5, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0
])


class SpringCalculatorDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Advanced Spring Design Calculator", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setMinimumWidth(450)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._create_input_widgets()
        self._create_output_widgets()
        self._create_visualization_widgets()

        self.setWidget(self.container)
        self.service_type_changed()

    def _create_input_widgets(self):
        main_group = QGroupBox("Inputs")
        main_layout = QVBoxLayout(main_group)

        loading_group = QGroupBox("Loading Conditions")
        loading_layout = QFormLayout(loading_group)

        double_validator = QDoubleValidator()
        double_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        double_validator.setBottom(0)

        self.service_type_combo = QComboBox()
        self.service_type_combo.addItems(["Static", "Cyclic (Fatigue)"])
        self.service_type_combo.currentIndexChanged.connect(self.service_type_changed)

        self.min_force_input = QLineEdit("0")
        self.min_force_input.setValidator(double_validator)
        self.max_force_input = QLineEdit("100")
        self.max_force_input.setValidator(double_validator)

        loading_layout.addRow("Service Type:", self.service_type_combo)
        loading_layout.addRow("Min Force (N):", self.min_force_input)
        loading_layout.addRow("Max Force (N):", self.max_force_input)

        geom_group = QGroupBox("Geometry, Material & Ends")
        geom_layout = QFormLayout(geom_group)

        self.deflection_input = QLineEdit("20")
        self.deflection_input.setValidator(double_validator)
        self.coil_dia_input = QLineEdit("25")
        self.coil_dia_input.setValidator(double_validator)

        self.material_combo = QComboBox()
        self.material_combo.addItems(MATERIAL_PROPERTIES.keys())
        self.end_type_combo = QComboBox()
        self.end_type_combo.addItems(END_TYPE_COILS.keys())
        self.end_condition_combo = QComboBox()
        self.end_condition_combo.addItems(END_CONDITIONS_BUCKLING.keys())

        geom_layout.addRow("Working Deflection (mm):", self.deflection_input)
        geom_layout.addRow("Mean Coil Diameter (mm):", self.coil_dia_input)
        geom_layout.addRow("Material:", self.material_combo)
        geom_layout.addRow("End Type (Geometry):", self.end_type_combo)
        geom_layout.addRow("End Condition (Buckling):", self.end_condition_combo)

        calc_button = QPushButton("⚙️ Calculate Spring Design")
        calc_button.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        calc_button.clicked.connect(self.calculate_design)

        main_layout.addWidget(loading_group)
        main_layout.addWidget(geom_group)
        main_layout.addWidget(calc_button)
        self.layout.addWidget(main_group)

    def _create_output_widgets(self):
        group = QGroupBox("Calculated Design")
        layout = QFormLayout(group)

        self.results = {}
        output_params = [
            "Status", "Wire Diameter (d)", "Spring Rate (k)", "Spring Index (C)",
            "Active Coils (Na)", "Total Coils (Nt)", "Solid Length (Ls)", "Free Length (Lf)",
            "Max Stress (τ_max)", "Factor of Safety (Fs)"
        ]

        for param in output_params:
            label = QLabel("-")
            label.setStyleSheet("font-weight: bold;")
            self.results[param] = label
            layout.addRow(f"{param}:", label)

        self.layout.addWidget(group)

    def _create_visualization_widgets(self):
        group = QGroupBox("Visualization")
        layout = QVBoxLayout(group)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setMinimumHeight(150)
        layout.addWidget(self.view)
        self.layout.addWidget(group)

    def service_type_changed(self):
        is_static = self.service_type_combo.currentText() == "Static"
        self.min_force_input.setEnabled(not is_static)
        if is_static:
            self.min_force_input.setText("0")

    def calculate_design(self):
        try:
            F_max = float(self.max_force_input.text())
            F_min = float(self.min_force_input.text())
            delta_working = float(self.deflection_input.text())
            D_mean = float(self.coil_dia_input.text())
            material = self.material_combo.currentText()
            service_type = self.service_type_combo.currentText()

            if F_max <= 0 or delta_working <= 0 or D_mean <= 0 or F_max <= F_min:
                raise ValueError("Inputs must be positive. F_max must be > F_min.")

        except (ValueError, TypeError) as e:
            QMessageBox.critical(self, "Input Error", f"Invalid input value.\n{e}")
            return

        k_spring_rate = F_max / delta_working
        material_props = MATERIAL_PROPERTIES[material]
        G_gpa = material_props["G"]
        G_mpa = G_gpa * 1000
        A, m = material_props["A"], material_props["m"]

        best_design = None
        for d_wire in STANDARD_WIRE_DIAMETERS_MM:
            C_index = D_mean / d_wire
            if not (4 <= C_index <= 12):
                continue

            K_wahl = ((4 * C_index - 1) / (4 * C_index - 4)) + (0.615 / C_index)
            S_ut = A / (d_wire ** m)
            S_su = 0.67 * S_ut

            tau_max = K_wahl * (8 * F_max * D_mean) / (np.pi * d_wire ** 3)

            Fs = 0
            if service_type == "Static":
                tau_allow_static = 0.45 * S_ut
                if tau_max < tau_allow_static:
                    Fs = tau_allow_static / tau_max
            else:  # Cyclic (Fatigue)
                S_se = 0.22 * S_ut
                F_a = (F_max - F_min) / 2
                F_m = (F_max + F_min) / 2
                tau_a = K_wahl * (8 * F_a * D_mean) / (np.pi * d_wire ** 3)
                tau_m = K_wahl * (8 * F_m * D_mean) / (np.pi * d_wire ** 3)

                # Using Goodman criterion for fatigue
                if tau_a > 0:
                    Fs = 1 / ((tau_a / S_se) + (tau_m / S_su))

            if Fs > 1.2:  # Minimum acceptable Factor of Safety
                best_design = {
                    "d": d_wire, "k": k_spring_rate, "C": C_index,
                    "tau_max": tau_max, "Fs": Fs
                }
                break

        if not best_design:
            self._update_results(
                error="No suitable standard wire diameter found. Try increasing coil diameter or reducing load.")
            self.scene.clear()
            return

        d = best_design['d']
        k = best_design['k']
        Na_active_coils = (d ** 4 * G_mpa) / (8 * D_mean ** 3 * k)

        end_type = self.end_type_combo.currentText()
        Nt_total_coils = eval(END_TYPE_COILS[end_type]["Nt"], {"Na": Na_active_coils})

        Ls_solid_length = Nt_total_coils * d

        delta_solid = F_max / k if k > 0 else 0
        clash_allowance = 0.15 * delta_solid
        Lf_free_length = Ls_solid_length + delta_solid + clash_allowance

        end_cond_val = END_CONDITIONS_BUCKLING[self.end_condition_combo.currentText()]
        slenderness_ratio = Lf_free_length / D_mean
        critical_ratio = np.pi * np.sqrt(2 * G_mpa / (2 * G_mpa))  # Simplified

        status = "Design OK"
        if slenderness_ratio > end_cond_val * critical_ratio:
            status = "Warning: High risk of buckling."

        best_design.update({
            "Status": status, "Na": Na_active_coils, "Nt": Nt_total_coils,
            "Ls": Ls_solid_length, "Lf": Lf_free_length
        })

        self._update_results(design=best_design)
        self._update_visualization(best_design)

    def _update_results(self, design=None, error=None):
        if error:
            self.results["Status"].setText(f"<font color='red'>{error}</font>")
            for key, label in self.results.items():
                if key != "Status": label.setText("-")
            return

        status_color = "orange" if "Warning" in design['Status'] else "green"
        self.results["Status"].setText(f"<font color='{status_color}'>{design['Status']}</font>")
        self.results["Wire Diameter (d)"].setText(f"{design['d']:.2f} mm (Standard)")
        self.results["Spring Rate (k)"].setText(f"{design['k']:.3f} N/mm")
        self.results["Spring Index (C)"].setText(f"{design['C']:.2f}")
        self.results["Active Coils (Na)"].setText(f"{design['Na']:.2f}")
        self.results["Total Coils (Nt)"].setText(f"{design['Nt']:.2f}")
        self.results["Solid Length (Ls)"].setText(f"{design['Ls']:.2f} mm")
        self.results["Free Length (Lf)"].setText(f"{design['Lf']:.2f} mm")
        self.results["Max Stress (τ_max)"].setText(f"{design['tau_max']:.2f} MPa")
        self.results["Factor of Safety (Fs)"].setText(f"{design['Fs']:.2f}")

    def _update_visualization(self, design):
        self.scene.clear()

        d = design['d']
        D = design['C'] * d
        Nt = design['Nt']
        Lf = design['Lf']

        if Nt <= 1: return

        pitch = (Lf - 2 * d) / (Nt - 1) if Nt > 1 else 0

        path = QPainterPath()
        path.moveTo(0, 0)

        num_segments = int(Nt * 50)
        for i in range(num_segments + 1):
            angle = i / 50 * 2 * np.pi
            x = (D / 2) * np.cos(angle)
            y = (i / num_segments) * (Lf - 2 * d) + d
            path.lineTo(x, y)

        path_item = QGraphicsPathItem(path)
        pen = QPen(QColor("gray"), d)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        path_item.setPen(pen)

        self.scene.addItem(path_item)
        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)