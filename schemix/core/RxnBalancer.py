from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QLineEdit,
    QPushButton, QLabel, QTextEdit
)
from PyQt6.QtCore import Qt
from chempy import balance_stoichiometry
from chempy.util.parsing import formula_to_composition


class ReactionBalancerDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Reaction Balancer", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        # Main widget
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter reaction (e.g. Fe + HCl -> FeCl3 + H2)")

        self.balance_button = QPushButton("Balance Reaction")
        self.balance_button.clicked.connect(self.balance_reaction)

        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: red")

        layout.addWidget(self.input_field)
        layout.addWidget(self.balance_button)
        layout.addWidget(self.output_area)
        layout.addWidget(self.status_label)

        self.setWidget(main_widget)

    def balance_reaction(self):
        self.status_label.clear()
        self.output_area.clear()

        try:
            raw_input = self.input_field.text()
            if '->' in raw_input:
                lhs, rhs = raw_input.split('->')
            elif '→' in raw_input:
                lhs, rhs = raw_input.split('→')
            else:
                self.status_label.setText("Use '->' or '→' to separate reactants and products.")
                return

            reactants = {s.strip() for s in lhs.split('+')}
            products = {s.strip() for s in rhs.split('+')}

            balanced_reactants, balanced_products = balance_stoichiometry(reactants, products)

            def format_side(compounds):
                return ' + '.join(f"{coeff if coeff > 1 else ''}{compound}"
                                  for compound, coeff in compounds.items())

            result = f"{format_side(balanced_reactants)} → {format_side(balanced_products)}"
            self.output_area.setText(result)

        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
