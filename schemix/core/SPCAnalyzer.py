import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QTextEdit, QLabel, QLineEdit, QTabWidget,
    QMessageBox
)

# --- SPC Constants for X-bar & R Charts ---
# These values are standard in quality engineering and depend on the subgroup size. Thalkalam use those units
# A2  X-bar chart limits ne use aaka
# D3, D4: For R chart limitsne use aaka
SPC_CONSTANTS = {
    2: {'A2': 1.880, 'D3': 0, 'D4': 3.267},
    3: {'A2': 1.023, 'D3': 0, 'D4': 2.574},
    4: {'A2': 0.729, 'D3': 0, 'D4': 2.282},
    5: {'A2': 0.577, 'D3': 0, 'D4': 2.114},
    6: {'A2': 0.483, 'D3': 0, 'D4': 2.004},
    7: {'A2': 0.419, 'D3': 0.076, 'D4': 1.924},
    8: {'A2': 0.373, 'D3': 0.136, 'D4': 1.864},
    9: {'A2': 0.337, 'D3': 0.184, 'D4': 1.816},
    10: {'A2': 0.308, 'D3': 0.223, 'D4': 1.777}
}


class SPCAnalyzerDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Statistical Process Control (SPC) Analyzer", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setMinimumSize(600, 700)

        # Main container widget and layout
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)

        # Create UI sections
        self._create_input_panel()
        self._create_plot_panel()
        self._create_results_panel()

        self.setWidget(self.container)

    def _create_input_panel(self):
        panel = QWidget()
        layout = QHBoxLayout(panel)

        # Data Input Area
        input_layout = QVBoxLayout()
        input_layout.addWidget(QLabel("Paste measurement data (one per line):"))
        self.data_input = QTextEdit()
        self.data_input.setPlaceholderText("10.1\n9.9\n10.2\n...")
        input_layout.addWidget(self.data_input)

        # Settings Area
        settings_layout = QVBoxLayout()
        settings_layout.addWidget(QLabel("Subgroup Size (2-10):"))
        self.subgroup_size_input = QLineEdit("5")
        settings_layout.addWidget(self.subgroup_size_input)

        generate_btn = QPushButton("Generate Sample Data")
        generate_btn.clicked.connect(self.generate_sample_data)
        settings_layout.addWidget(generate_btn)

        analyze_btn = QPushButton("📊 Analyze Data")
        analyze_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        analyze_btn.clicked.connect(self.run_analysis)
        settings_layout.addWidget(analyze_btn)

        settings_layout.addStretch()

        layout.addLayout(input_layout, 2)  # Give more space to input
        layout.addLayout(settings_layout, 1)
        self.layout.addWidget(panel)

    def _create_plot_panel(self):
        self.plot_tabs = QTabWidget()
        self.x_bar_chart = pg.PlotWidget()
        self.r_chart = pg.PlotWidget()
        self.plot_tabs.addTab(self.x_bar_chart, "X-bar (Average) Chart")
        self.plot_tabs.addTab(self.r_chart, "R (Range) Chart")
        self.layout.addWidget(self.plot_tabs)

    def _create_results_panel(self):
        self.results_label = QLabel("Analysis results will be shown here.")
        self.results_label.setWordWrap(True)
        self.results_label.setStyleSheet("padding: 5px; border: 1px solid gray; background-color: #2a2a2a;")
        self.layout.addWidget(self.results_label)

    def generate_sample_data(self):
        """Generates sample data with a process shift to demonstrate SPC."""
        # In-control process
        in_control = np.random.normal(loc=10.0, scale=0.1, size=50)
        # Process mean shifts upwards (special cause)
        out_of_control = np.random.normal(loc=10.25, scale=0.1, size=50)

        sample_data = np.concatenate((in_control, out_of_control))
        self.data_input.setText("\n".join(f"{x:.3f}" for x in sample_data))
        self.subgroup_size_input.setText("5")

    def run_analysis(self):
        # 1. Parse Data and Settings
        try:
            data_str = self.data_input.toPlainText().strip().split()
            data = np.array([float(d) for d in data_str])
            n = int(self.subgroup_size_input.text())
            if not (2 <= n <= 10):
                raise ValueError("Subgroup size must be between 2 and 10.")
        except Exception as e:
            QMessageBox.critical(self, "Input Error", f"Invalid input data or settings.\nError: {e}")
            return

        if data.size % n != 0:
            QMessageBox.warning(self, "Data Warning",
                                f"Data size ({data.size}) is not perfectly divisible by subgroup size ({n}). Truncating data.")
            num_subgroups = data.size // n
            data = data[:num_subgroups * n]

        subgroups = data.reshape(-1, n)
        num_subgroups = subgroups.shape[0]

        # 2. Calculate Statistics
        x_bars = np.mean(subgroups, axis=1)
        ranges = np.max(subgroups, axis=1) - np.min(subgroups, axis=1)

        x_double_bar = np.mean(x_bars)
        r_bar = np.mean(ranges)

        # 3. Calculate Control Limits
        consts = SPC_CONSTANTS[n]
        A2, D3, D4 = consts['A2'], consts['D3'], consts['D4']

        # X-bar chart limits
        cl_x = x_double_bar
        ucl_x = x_double_bar + A2 * r_bar
        lcl_x = x_double_bar - A2 * r_bar

        # R chart limits
        cl_r = r_bar
        ucl_r = D4 * r_bar
        lcl_r = D3 * r_bar

        # 4. Plot Charts
        self._plot_chart(self.x_bar_chart, "Process Average", x_bars, cl_x, ucl_x, lcl_x)
        self._plot_chart(self.r_chart, "Process Range", ranges, cl_r, ucl_r, lcl_r)

        # 5. Check for Violations and Display Results
        violations = self._check_rules(x_bars, cl_x, ucl_x, lcl_x, ranges, cl_r, ucl_r, lcl_r)

        results_text = (
            f"<b>Analysis Complete:</b><br>"
            f"Overall Average (X&#773;&#773;): {x_double_bar:.4f} | Average Range (R&#773;): {r_bar:.4f}<br><hr>"
            f"<b>X-bar Chart Limits:</b> UCL={ucl_x:.4f}, CL={cl_x:.4f}, LCL={lcl_x:.4f}<br>"
            f"<b>R Chart Limits:</b> UCL={ucl_r:.4f}, CL={cl_r:.4f}, LCL={lcl_r:.4f}<br><hr>"
            f"<b>Detected Rule Violations:</b><br>"
        )
        if violations:
            results_text += "<ul>" + "".join(f"<li>{v}</li>" for v in violations) + "</ul>"
        else:
            results_text += "None. The process appears to be in statistical control."

        self.results_label.setText(results_text)

    def _plot_chart(self, plot_widget, title, data, cl, ucl, lcl):
        plot_widget.clear()
        plot_widget.setTitle(title, size="12pt")
        plot_widget.setLabel('left', 'Measurement')
        plot_widget.setLabel('bottom', 'Subgroup Number')

        # Plot data points
        plot_widget.plot(range(1, len(data) + 1), data, pen=None, symbol='o', symbolBrush='b', symbolSize=8)

        # Plot control lines
        plot_widget.addItem(pg.InfiniteLine(pos=cl, angle=0, pen=pg.mkPen('g', width=2)))
        plot_widget.addItem(pg.InfiniteLine(pos=ucl, angle=0, pen=pg.mkPen('r', width=2, style=Qt.PenStyle.DashLine)))
        plot_widget.addItem(pg.InfiniteLine(pos=lcl, angle=0, pen=pg.mkPen('r', width=2, style=Qt.PenStyle.DashLine)))

    def _check_rules(self, x_bars, cl_x, ucl_x, lcl_x, ranges, cl_r, ucl_r, lcl_r):
        violations = []
        # Rule 1: Point outside control limits
        for i, x in enumerate(x_bars):
            if not (lcl_x <= x <= ucl_x):
                violations.append(f"X-bar Chart: Subgroup {i + 1} is outside control limits.")
        for i, r in enumerate(ranges):
            if not (lcl_r <= r <= ucl_r):
                violations.append(f"R Chart: Subgroup {i + 1} is outside control limits.")
        return violations
