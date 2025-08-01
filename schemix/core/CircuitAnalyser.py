# core/CircuitAnalyser.py
import json
import uuid
import numpy as np
import pyqtgraph as pg
from collections import deque
from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QVBoxLayout, QHBoxLayout, QPushButton, QMenu, QFileDialog, QTabWidget,
    QFormLayout, QLineEdit, QLabel, QComboBox, QMessageBox, QGraphicsTextItem,
    QScrollArea, QGraphicsLineItem
)
from PyQt6.QtCore import Qt, QPointF, QLineF, QRectF, pyqtSignal
from PyQt6.QtGui import QPen, QPainter, QAction, QColor, QPainterPath


# ==============================================================================
# --- UI WIDGETS ---
# ==============================================================================

class PropertyEditor(QWidget):
    """A widget to edit the properties of the selected component."""
    property_changed = pyqtSignal(str, str, object)

    def __init__(self):
        super().__init__()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.scroll)
        self.clear()

    def set_component(self, component):
        self.clear()
        if not component or not isinstance(component, Component):
            return

        container = QWidget()
        form_layout = QFormLayout(container)
        form_layout.addRow(QLabel(f"<h3>{component.properties['id']} ({component.__class__.__name__})</h3>"))

        self.editors = {}
        for key, value in component.properties.items():
            if key == 'id':
                form_layout.addRow(key, QLabel(str(value)))
            else:
                editor = QLineEdit(str(value))
                editor.editingFinished.connect(lambda k=key: self.on_edit_finished(k))
                self.editors[key] = editor
                form_layout.addRow(key, editor)
        self.scroll.setWidget(container)

    def on_edit_finished(self, key):
        editor = self.editors[key]
        try:
            value = float(editor.text())
        except ValueError:
            value = editor.text()
        self.property_changed.emit(key, editor.text(), value)

    def clear(self):
        empty_widget = QWidget()
        empty_widget.setLayout(QFormLayout())
        empty_widget.layout().addRow(QLabel("No item selected."))
        self.scroll.setWidget(empty_widget)


class PlotWidget(QWidget):
    """A widget for plotting analysis results using pyqtgraph."""

    def __init__(self):
        super().__init__()
        self.plot_item = pg.PlotWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot_item)

    def plot_ac(self, freqs, mags, phases):
        self.plot_item.clear()
        self.plot_item.setLogMode(x=True, y=True)
        self.plot_item.setLabel('bottom', 'Frequency', units='Hz')
        self.plot_item.setLabel('left', 'Magnitude', units='dB')
        self.plot_item.showGrid(x=True, y=True)
        self.plot_item.plot(freqs, 20 * np.log10(mags), pen='y', name='Magnitude (dB)')

    def plot_transient(self, time, data_map):
        self.plot_item.clear()
        self.plot_item.setLogMode(x=False, y=False)
        self.plot_item.setLabel('bottom', 'Time', units='s')
        self.plot_item.setLabel('left', 'Voltage / Current')
        self.plot_item.showGrid(x=True, y=True)
        self.plot_item.addLegend()
        for i, (name, values) in enumerate(data_map.items()):
            pen = pg.mkPen(color=pg.intColor(i, hues=len(data_map) + 1), width=2)
            self.plot_item.plot(time, values, pen=pen, name=name)


# ==============================================================================
# --- CIRCUIT COMPONENTS ---
# ==============================================================================

class Terminal(QGraphicsItem):
    """A connection point on a component."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.radius = 5
        self.connected_wires = []

    def boundingRect(self):
        return QRectF(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)

    def paint(self, painter, option, widget):
        painter.setBrush(QColor("red"))
        painter.drawEllipse(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)


class Component(QGraphicsItem):
    """Base class for all circuit components. Now handles move updates."""

    def __init__(self, props=None):
        super().__init__()
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            # This flag is now on the component itself
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.terminals = []
        self.properties = {'id': f"{self.__class__.__name__[0]}{uuid.uuid4().hex[:4]}", 'value': 0, 'unit': ''}
        if props: self.properties.update(props)

        self.label = QGraphicsTextItem(self)
        self.update_label()

    def itemChange(self, change, value):
        """When the component moves, tell all connected wires to update."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for terminal in self.terminals:
                for wire in terminal.connected_wires:
                    wire.update_position()
        return super().itemChange(change, value)

    def add_terminal(self, x, y):
        term = Terminal(self)
        term.setPos(x, y)
        self.terminals.append(term)

    def update_label(self):
        val = self.properties.get('value', '')
        unit = self.properties.get('unit', '')
        self.label.setPlainText(f"{self.properties['id']}\n{val} {unit}")
        self.label.setPos(self.boundingRect().topRight() + QPointF(5, -10))

    def rotate(self):
        self.setRotation(self.rotation() + 90)

    def serialize(self):
        return {
            'type': self.__class__.__name__,
            'id': self.properties['id'],
            'pos': [self.scenePos().x(), self.scenePos().y()],
            'rotation': self.rotation(),
            'properties': self.properties
        }

    def delete(self):
        for t in self.terminals:
            for wire in list(t.connected_wires):
                wire.delete()
        if self.scene():
            self.scene().removeItem(self)


class Resistor(Component):
    def __init__(self, props=None):
        base_props = {'value': 1000, 'unit': 'Ω'}
        if props: base_props.update(props)
        super().__init__(base_props)
        self.add_terminal(-30, 0)
        self.add_terminal(30, 0)

    def boundingRect(self): return QRectF(-30, -10, 60, 20)

    def paint(self, p, o, w):
        p.setPen(QPen(QColor("black"), 2))
        p.drawRect(-25, -8, 50, 16)
        p.drawLine(-30, 0, -25, 0)
        p.drawLine(25, 0, 30, 0)


class Capacitor(Component):
    def __init__(self, props=None):
        base_props = {'value': 1e-6, 'unit': 'F'}
        if props: base_props.update(props)
        super().__init__(base_props)
        self.add_terminal(-10, 0)
        self.add_terminal(10, 0)

    def boundingRect(self): return QRectF(-10, -15, 20, 30)

    def paint(self, p, o, w):
        p.setPen(QPen(QColor("black"), 2))
        p.drawLine(-10, 0, -2, 0)
        p.drawLine(10, 0, 2, 0)
        p.drawLine(-2, -15, -2, 15)
        p.drawLine(2, -15, 2, 15)


class Inductor(Component):
    def __init__(self, props=None):
        base_props = {'value': 1e-3, 'unit': 'H'}
        if props: base_props.update(props)
        super().__init__(base_props)
        self.add_terminal(-20, 0)
        self.add_terminal(20, 0)

    def boundingRect(self): return QRectF(-20, -10, 40, 20)

    def paint(self, p, o, w):
        p.setPen(QPen(QColor("black"), 2))
        p.drawLine(-20, 0, -15, 0)
        p.drawArc(QRectF(-15, -5, 10, 10), 180 * 16, -180 * 16)
        p.drawArc(QRectF(-5, -5, 10, 10), 180 * 16, -180 * 16)
        p.drawArc(QRectF(5, -5, 10, 10), 180 * 16, -180 * 16)
        p.drawLine(15, 0, 20, 0)


class VoltageSource(Component):
    def __init__(self, props=None):
        base_props = {'value': 9, 'unit': 'V', 'ac_mag': 1, 'ac_phase': 0}
        if props: base_props.update(props)
        super().__init__(base_props)
        self.add_terminal(0, 20)  # Negative
        self.add_terminal(0, -20)  # Positive

    def boundingRect(self): return QRectF(-20, -20, 40, 40)

    def paint(self, p, o, w):
        p.setPen(QPen(QColor("black"), 2))
        p.drawEllipse(QPointF(0, 0), 15, 15)
        p.drawLine(0, -20, 0, -15)
        p.drawLine(0, 15, 0, 20)
        p.drawLine(-8, -5, 8, -5)
        p.drawLine(0, -10, 0, 0)
        p.drawLine(-8, 10, 8, 10)


class Diode(Component):
    def __init__(self, props=None):
        base_props = {'value': 0, 'unit': '', 'Is': 1e-14, 'Vt': 0.02585}
        if props: base_props.update(props)
        super().__init__(base_props)
        self.add_terminal(-10, 0)
        self.add_terminal(10, 0)

    def boundingRect(self): return QRectF(-10, -10, 20, 20)

    def paint(self, p, o, w):
        p.setPen(QPen(QColor("black"), 2))
        path = QPainterPath()
        path.moveTo(-10, 0)
        path.lineTo(0, 0)
        path.moveTo(0, -10)
        path.lineTo(10, 0)
        path.lineTo(0, 10)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(10, -10, 10, 10)


class Ground(Component):
    def __init__(self, props=None):
        super().__init__({'id': 'GND', 'value': 0, 'unit': 'V'})
        self.add_terminal(0, 0)

    def boundingRect(self): return QRectF(-15, 0, 30, 15)

    def paint(self, p, o, w):
        p.setPen(QPen(QColor("black"), 2))
        p.drawLine(0, 0, 0, 5)
        p.drawLine(-15, 5, 15, 5)
        p.drawLine(-10, 10, 10, 10)
        p.drawLine(-5, 15, 5, 15)


class VoltageProbe(Component):
    def __init__(self, props=None):
        super().__init__({'id': f"VP{uuid.uuid4().hex[:2]}", 'value': 0, 'unit': 'V'})
        self.add_terminal(0, 0)

    def boundingRect(self): return QRectF(-15, -15, 30, 30)

    def paint(self, p, o, w):
        p.setPen(QPen(QColor("blue"), 2))
        p.drawEllipse(self.boundingRect())
        p.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, "V")


COMPONENT_MAP = {
    'Resistor': Resistor, 'Capacitor': Capacitor, 'Inductor': Inductor,
    'VoltageSource': VoltageSource, 'Diode': Diode, 'Ground': Ground,
    'VoltageProbe': VoltageProbe
}


# ==============================================================================
# --- ANALYSIS ENGINES ---
# ==============================================================================

class BaseAnalysis:
    """Base class for different analysis types."""

    def __init__(self, components):
        self.components = components
        self.nodes = {}
        self.node_count = 0
        self.gnd_node = 0
        self.solution = None

    def build_node_map(self):
        visited = set()
        node_idx = 1
        for comp in self.components:
            for term in comp.terminals:
                if term in visited: continue
                is_gnd = False
                q = deque([term])
                group = set()
                while q:
                    t = q.popleft()
                    if t in visited: continue
                    visited.add(t)
                    group.add(t)
                    if isinstance(t.parentItem(), Ground): is_gnd = True
                    for wire in t.connected_wires:
                        other_t = wire.start_term if wire.end_term == t else wire.end_term
                        q.append(other_t)

                n_id = self.gnd_node if is_gnd else node_idx
                if not is_gnd: node_idx += 1
                for t in group: self.nodes[t] = n_id
        self.node_count = node_idx - 1
        has_ground = any(isinstance(c, Ground) for c in self.components)
        return has_ground


class DCAnalysis(BaseAnalysis):
    def run(self, max_iter=100, tolerance=1e-6):
        if not self.build_node_map(): return False, "Circuit must have a Ground"
        num_v = len([c for c in self.components if isinstance(c, VoltageSource)])
        size = self.node_count + num_v
        x = np.zeros(size)
        for i in range(max_iter):
            A = np.zeros((size, size))
            z = np.zeros(size)
            self._stamp_linear(A, z)
            J = np.zeros((size, size))
            f = np.zeros(size)
            has_nonlinear = self._stamp_nonlinear(x, J, f)
            if not has_nonlinear:
                self.solution = np.linalg.solve(A, z)
                return True, "DC solution found."
            A_iter = A + J
            z_iter = z - f
            try:
                dx = np.linalg.solve(A_iter, z_iter - A_iter @ x)
                x += dx
                if np.all(np.abs(dx) < tolerance):
                    self.solution = x
                    return True, f"DC solution converged in {i + 1} iterations."
            except np.linalg.LinAlgError:
                return False, "Singular matrix, check circuit."
        return False, "DC analysis failed to converge."

    def _stamp_linear(self, A, z):
        v_idx = self.node_count
        for c in self.components:
            n = [self.nodes.get(t, -1) for t in c.terminals]
            if isinstance(c, Resistor):
                g = 1.0 / c.properties['value']
                if n[0] != 0: A[n[0] - 1, n[0] - 1] += g
                if n[1] != 0: A[n[1] - 1, n[1] - 1] += g
                if n[0] != 0 and n[1] != 0: A[n[0] - 1, n[1] - 1] -= g; A[n[1] - 1, n[0] - 1] -= g
            elif isinstance(c, VoltageSource):
                if n[1] != 0: A[n[1] - 1, v_idx] = 1; A[v_idx, n[1] - 1] = 1
                if n[0] != 0: A[n[0] - 1, v_idx] = -1; A[v_idx, n[0] - 1] = -1
                z[v_idx] = c.properties['value']
                v_idx += 1

    def _stamp_nonlinear(self, x, J, f):
        has_nonlinear = False
        for c in self.components:
            if isinstance(c, Diode):
                has_nonlinear = True
                n_anode, n_cathode = [self.nodes.get(t, -1) for t in c.terminals]
                v_anode = x[n_anode - 1] if n_anode != 0 else 0
                v_cathode = x[n_cathode - 1] if n_cathode != 0 else 0
                vd = v_anode - v_cathode
                Is, Vt = c.properties['Is'], c.properties['Vt']
                Id = Is * (np.exp(vd / Vt) - 1)
                gd = (Is / Vt) * np.exp(vd / Vt)
                Ieq = Id - gd * vd
                if n_anode != 0: J[n_anode - 1, n_anode - 1] += gd; f[n_anode - 1] += Ieq
                if n_cathode != 0: J[n_cathode - 1, n_cathode - 1] += gd; f[n_cathode - 1] -= Ieq
                if n_anode != 0 and n_cathode != 0: J[n_anode - 1, n_cathode - 1] -= gd; J[
                    n_cathode - 1, n_anode - 1] -= gd
        return has_nonlinear


class ACAnalysis(BaseAnalysis):
    def run(self, start_freq, stop_freq, num_points):
        if not self.build_node_map(): return False, "Circuit must have a Ground"
        freqs = np.logspace(np.log10(start_freq), np.log10(stop_freq), num_points)
        num_v = len([c for c in self.components if isinstance(c, VoltageSource)])
        size = self.node_count + num_v
        results = np.zeros((size, num_points), dtype=np.complex128)
        for i, freq in enumerate(freqs):
            w = 2 * np.pi * freq
            A = np.zeros((size, size), dtype=np.complex128)
            z = np.zeros(size, dtype=np.complex128)
            v_idx = self.node_count
            for c in self.components:
                n = [self.nodes.get(t, -1) for t in c.terminals]
                val = c.properties['value']
                g = 0
                if isinstance(c, Resistor):
                    g = 1.0 / val
                elif isinstance(c, Capacitor):
                    g = 1j * w * val
                elif isinstance(c, Inductor):
                    g = 1.0 / (1j * w * val) if w > 0 else 1e9
                if g != 0:
                    if n[0] != 0: A[n[0] - 1, n[0] - 1] += g
                    if n[1] != 0: A[n[1] - 1, n[1] - 1] += g
                    if n[0] != 0 and n[1] != 0: A[n[0] - 1, n[1] - 1] -= g; A[n[1] - 1, n[0] - 1] -= g
                elif isinstance(c, VoltageSource):
                    mag, phase = c.properties['ac_mag'], np.deg2rad(c.properties['ac_phase'])
                    if n[1] != 0: A[n[1] - 1, v_idx] = 1; A[v_idx, n[1] - 1] = 1
                    if n[0] != 0: A[n[0] - 1, v_idx] = -1; A[v_idx, n[0] - 1] = -1
                    z[v_idx] = mag * np.exp(1j * phase)
                    v_idx += 1
            try:
                results[:, i] = np.linalg.solve(A, z)
            except np.linalg.LinAlgError:
                return False, f"Singular matrix at {freq:.2f} Hz"
        self.solution = results
        return True, freqs


class TransientAnalysis(BaseAnalysis):
    def run(self, t_stop, t_step):
        if not self.build_node_map(): return False, "Circuit must have a Ground"

        time_pts = np.arange(0, t_stop, t_step)
        num_v = len([c for c in self.components if isinstance(c, VoltageSource)])
        inductors = [c for c in self.components if isinstance(c, Inductor)]
        num_l = len(inductors)
        size = self.node_count + num_v + num_l

        x = np.zeros(size)
        results = np.zeros((size, len(time_pts)))

        for i, t in enumerate(time_pts):
            A = np.zeros((size, size))
            z = np.zeros(size)

            v_idx = self.node_count
            l_idx_base = self.node_count + num_v

            for c in self.components:
                n = [self.nodes.get(t, -1) for t in c.terminals]
                val = c.properties['value']

                if isinstance(c, Resistor):
                    g = 1.0 / val
                    if n[0] != 0: A[n[0] - 1, n[0] - 1] += g
                    if n[1] != 0: A[n[1] - 1, n[1] - 1] += g
                    if n[0] != 0 and n[1] != 0: A[n[0] - 1, n[1] - 1] -= g; A[n[1] - 1, n[0] - 1] -= g

                elif isinstance(c, Capacitor):
                    g_eq = val / t_step
                    n0_prev = results[n[0] - 1, i - 1] if n[0] != 0 and i > 0 else 0
                    n1_prev = results[n[1] - 1, i - 1] if n[1] != 0 and i > 0 else 0
                    i_eq = g_eq * (n0_prev - n1_prev)
                    if n[0] != 0: A[n[0] - 1, n[0] - 1] += g_eq; z[n[0] - 1] += i_eq
                    if n[1] != 0: A[n[1] - 1, n[1] - 1] += g_eq; z[n[1] - 1] -= i_eq
                    if n[0] != 0 and n[1] != 0: A[n[0] - 1, n[1] - 1] -= g_eq; A[n[1] - 1, n[0] - 1] -= g_eq

                elif isinstance(c, Inductor):
                    l_idx = l_idx_base + inductors.index(c)
                    if n[0] != 0: A[n[0] - 1, l_idx] = 1
                    if n[1] != 0: A[n[1] - 1, l_idx] = -1
                    if n[0] != 0: A[l_idx, n[0] - 1] = 1
                    if n[1] != 0: A[l_idx, n[1] - 1] = -1
                    A[l_idx, l_idx] = -val / t_step
                    z[l_idx] = -val / t_step * (results[l_idx, i - 1] if i > 0 else 0)

                elif isinstance(c, VoltageSource):
                    if n[1] != 0: A[n[1] - 1, v_idx] = 1; A[v_idx, n[1] - 1] = 1
                    if n[0] != 0: A[n[0] - 1, v_idx] = -1; A[v_idx, n[0] - 1] = -1
                    z[v_idx] = val
                    v_idx += 1

            try:
                x = np.linalg.solve(A, z)
                results[:, i] = x
            except np.linalg.LinAlgError:
                return False, f"Singular matrix at t={t:.4f}s"

        self.solution = results
        return True, time_pts


# ==============================================================================
# --- MAIN UI AND SCENE ---
# ==============================================================================

class Wire(QGraphicsItem):
    """A graphical wire connecting two terminals."""

    def __init__(self, start_terminal, end_terminal):
        super().__init__()
        self.start_term = start_terminal
        self.end_term = end_terminal
        self.setZValue(-1)
        self.line = QLineF()

        self.start_term.connected_wires.append(self)
        self.end_term.connected_wires.append(self)
        self.update_position()

    def update_position(self):
        """Called by component terminals to update the wire's geometry."""
        if self.start_term and self.end_term:
            self.prepareGeometryChange()
            self.line = QLineF(self.start_term.scenePos(), self.end_term.scenePos())
            self.update()

    def boundingRect(self):
        extra = 10
        return self.line.boundingRect().adjusted(-extra, -extra, extra, extra)

    def paint(self, p, o, w):
        p.setPen(QPen(QColor("black"), 2))
        p.drawLine(self.line)

    def delete(self):
        self.start_term.connected_wires.remove(self)
        self.end_term.connected_wires.remove(self)
        if self.scene():
            self.scene().removeItem(self)

    def serialize(self):
        start_id = self.start_term.parentItem().properties['id']
        end_id = self.end_term.parentItem().properties['id']
        start_idx = self.start_term.parentItem().terminals.index(self.start_term)
        end_idx = self.end_term.parentItem().terminals.index(self.end_term)
        return {'type': 'Wire', 'start': [start_id, start_idx], 'end': [end_id, end_idx]}


class CircuitScene(QGraphicsScene):
    """The main scene for drawing and interacting with the circuit."""

    def __init__(self, property_editor_callback):
        super().__init__()
        self.temp_line = None
        self.start_terminal = None
        self.property_editor_callback = property_editor_callback
        self.annotations = []

    def selectionChanged(self):
        items = self.selectedItems()
        self.property_editor_callback(items[0] if items else None)
        super().selectionChanged()

    def mousePressEvent(self, e):
        item = self.itemAt(e.scenePos(), self.views()[0].transform())
        if isinstance(item, Terminal):
            self.start_terminal = item
            self.temp_line = QGraphicsLineItem(QLineF(self.start_terminal.scenePos(), e.scenePos()))
            self.temp_line.setPen(QPen(QColor("black"), 1, Qt.PenStyle.DashLine))
            self.addItem(self.temp_line)
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self.temp_line:
            self.temp_line.setLine(QLineF(self.start_terminal.scenePos(), e.scenePos()))
        else:
            super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None
            item = self.itemAt(e.scenePos(), self.views()[0].transform())
            if isinstance(item, Terminal) and item != self.start_terminal:
                self.addItem(Wire(self.start_terminal, item))
            self.start_terminal = None
        else:
            super().mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_R:
            for item in self.selectedItems():
                if isinstance(item, Component): item.rotate()
        elif e.key() == Qt.Key.Key_Delete:
            for item in list(self.selectedItems()):
                item.delete()
        else:
            super().keyPressEvent(e)

    def clear_annotations(self):
        for ann in self.annotations:
            self.removeItem(ann)
        self.annotations.clear()


class ElectricalCircuitDock(QDockWidget):

    def __init__(self, parent=None):
        super().__init__("Advanced Circuit Simulator", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)

        container = QWidget()
        main_layout = QHBoxLayout(container)

        left_panel = QWidget()
        left_v_layout = QVBoxLayout(left_panel)
        self.prop_editor = PropertyEditor()
        self.prop_editor.property_changed.connect(self.on_property_changed)
        self.scene = CircuitScene(self.prop_editor.set_component)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)

        left_v_layout.addWidget(self.view, 5)
        left_v_layout.addWidget(self.prop_editor, 2)

        right_panel = QWidget()
        right_v_layout = QVBoxLayout(right_panel)
        right_panel.setFixedWidth(250)

        self._create_file_controls(right_v_layout)
        self._create_component_toolbox(right_v_layout)
        self._create_analysis_panel(right_v_layout)
        self.plot_widget = PlotWidget()
        right_v_layout.addWidget(self.plot_widget)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        self.setWidget(container)

    def _create_file_controls(self, layout):
        layout.addWidget(QLabel("<b>File Operations</b>"))
        file_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_circuit)
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.load_circuit)
        file_layout.addWidget(save_btn)
        file_layout.addWidget(load_btn)
        layout.addLayout(file_layout)

    def _create_component_toolbox(self, layout):
        layout.addWidget(QLabel("<b>Component Toolbox</b>"))
        comp_layout = QFormLayout()
        for name, comp_class in COMPONENT_MAP.items():
            btn = QPushButton(f"Add {name}")
            btn.clicked.connect(lambda ch, c=comp_class: self.add_component(c()))
            comp_layout.addRow(btn)
        layout.addLayout(comp_layout)

    def _create_analysis_panel(self, layout):
        layout.addWidget(QLabel("<b>Analysis Control</b>"))
        form = QFormLayout()
        self.analysis_type = QComboBox()
        self.analysis_type.addItems(["DC", "AC", "Transient"])
        form.addRow("Type:", self.analysis_type)

        self.analysis_stack = QTabWidget()
        self.ac_settings = QWidget()
        self.ac_form = QFormLayout(self.ac_settings)
        self.tran_settings = QWidget()
        self.tran_form = QFormLayout(self.tran_settings)

        self.ac_start = QLineEdit("1")
        self.ac_stop = QLineEdit("1e6")
        self.ac_pts = QLineEdit("100")
        self.ac_form.addRow("Start Freq (Hz):", self.ac_start)
        self.ac_form.addRow("Stop Freq (Hz):", self.ac_stop)
        self.ac_form.addRow("Points:", self.ac_pts)

        self.tran_stop = QLineEdit("1e-3")
        self.tran_step = QLineEdit("1e-6")
        self.tran_form.addRow("Stop Time (s):", self.tran_stop)
        self.tran_form.addRow("Time Step (s):", self.tran_step)

        self.analysis_stack.addTab(QWidget(), "DC")
        self.analysis_stack.addTab(self.ac_settings, "AC")
        self.analysis_stack.addTab(self.tran_settings, "Transient")
        self.analysis_type.currentIndexChanged.connect(self.analysis_stack.setCurrentIndex)

        run_btn = QPushButton("▶️ Run Analysis")
        run_btn.clicked.connect(self.run_analysis)

        layout.addLayout(form)
        layout.addWidget(self.analysis_stack)
        layout.addWidget(run_btn)

    def add_component(self, component):
        pos = self.view.mapToScene(self.view.viewport().rect().center())
        component.setPos(pos)
        self.scene.addItem(component)

    def on_property_changed(self, key, text_value, actual_value):
        selected = self.scene.selectedItems()
        if selected:
            selected[0].properties[key] = actual_value
            selected[0].update_label()

    def run_analysis(self):
        self.scene.clear_annotations()
        components = [i for i in self.scene.items() if isinstance(i, Component)]
        analysis_type = self.analysis_type.currentText()

        if analysis_type == "DC":
            eng = DCAnalysis(components)
            success, msg = eng.run()
            if success:
                for term, node_idx in eng.nodes.items():
                    voltage = 0 if node_idx == 0 else eng.solution[node_idx - 1]
                    ann = QGraphicsTextItem(f"{voltage:.2f}V")
                    ann.setDefaultTextColor(QColor("darkgreen"))
                    ann.setPos(term.scenePos() + QPointF(5, -10))
                    self.scene.addItem(ann)
                    self.scene.annotations.append(ann)
            else:
                QMessageBox.critical(self, "Analysis Error", msg)

        elif analysis_type == "AC":
            try:
                start, stop, pts = float(self.ac_start.text()), float(self.ac_stop.text()), int(self.ac_pts.text())
                eng = ACAnalysis(components)
                success, data = eng.run(start, stop, pts)
                if success:
                    probe = next((c for c in components if isinstance(c, VoltageProbe)), None)
                    if probe:
                        node_idx = eng.nodes[probe.terminals[0]]
                        mags = np.abs(eng.solution[node_idx - 1, :]) if node_idx != 0 else np.zeros_like(data)
                        self.plot_widget.plot_ac(data, mags, None)
                    else:
                        QMessageBox.information(self, "Plotting", "Add a Voltage Probe to plot AC results.")
                else:
                    QMessageBox.critical(self, "Analysis Error", data)
            except ValueError:
                QMessageBox.critical(self, "Input Error", "Invalid AC settings.")

        elif analysis_type == "Transient":
            try:
                stop, step = float(self.tran_stop.text()), float(self.tran_step.text())
                eng = TransientAnalysis(components)
                success, time_pts = eng.run(stop, step)
                if success:
                    plot_data = {p.properties['id']: eng.solution[eng.nodes[p.terminals[0]] - 1, :] if eng.nodes.get(
                        p.terminals[0], 0) != 0 else np.zeros_like(time_pts) for p in components if
                                 isinstance(p, VoltageProbe)}
                    if plot_data:
                        self.plot_widget.plot_transient(time_pts, plot_data)
                    else:
                        QMessageBox.information(self, "Plotting", "Add Voltage Probes to plot Transient results.")
                else:
                    QMessageBox.critical(self, "Analysis Error", time_pts)
            except ValueError:
                QMessageBox.critical(self, "Input Error", "Invalid Transient settings.")

    def save_circuit(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Circuit", "", "JSON Files (*.json)")
        if path:
            data = [i.serialize() for i in self.scene.items() if hasattr(i, 'serialize')]
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

    def load_circuit(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Circuit", "", "JSON Files (*.json)")
        if path:
            self.scene.clear()
            self.prop_editor.clear()
            with open(path, 'r') as f:
                data = json.load(f)
            comp_map = {}
            for item_data in data:
                if item_data['type'] in COMPONENT_MAP:
                    cls = COMPONENT_MAP[item_data['type']]
                    comp = cls(props=item_data['properties'])
                    comp.setPos(QPointF(*item_data['pos']))
                    comp.setRotation(item_data['rotation'])
                    self.scene.addItem(comp)
                    comp_map[item_data['id']] = comp
            for item_data in data:
                if item_data['type'] == 'Wire':
                    start_id, start_idx = item_data['start']
                    end_id, end_idx = item_data['end']
                    start_term = comp_map[start_id].terminals[start_idx]
                    end_term = comp_map[end_id].terminals[end_idx]
                    self.scene.addItem(Wire(start_term, end_term))
