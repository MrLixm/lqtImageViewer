import enum
import logging
from typing import Optional

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from lqtImageViewer._grids import generate_points_grid

LOGGER = logging.getLogger(__name__)


class NodegraphViewState(enum.IntFlag):
    noneState = enum.auto()
    panState = enum.auto()
    zoomState = enum.auto()
    selectState = enum.auto()
    pickState = enum.auto()
    unpickState = enum.auto()


class LIVGraphicView(QtWidgets.QGraphicsView):
    states = NodegraphViewState

    zoom_min = 0.1
    zoom_max = 7

    selection_mode = QtCore.Qt.IntersectsItemShape

    def __init__(self, scene: QtWidgets.QGraphicsScene):
        super().__init__(scene)

        self._state = NodegraphViewState.noneState
        # save at each move
        self._mouse_previous_pos: Optional[QtCore.QPoint] = None
        # save at each click
        self._mouse_initial_pos: Optional[QtCore.QPoint] = None
        self._selected_items_initial: list[QtWidgets.QGraphicsItem] = []
        self._rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)

        self._background_color = QtGui.QColor(240, 240, 238)
        self._background_grid_color = QtGui.QColor(200, 200, 200)
        self._zoom: float = 1.0

        # TODO evaluate if caching make a difference
        # seems it cause some minor graphical imperfection
        self.setCacheMode(self.CacheBackground)
        self.setRenderHint(QtGui.QPainter.Antialiasing)

    def _pan_viewport(self, x_amount: float, y_amount: float):
        """
        Args:
            x_amount: amount to pan on the x axis, 0 to not pan [+-1-1+] range
            y_amount: amount to pan on the y axis, 0 to not pan [+-1-1+] range
        """
        scene_rect = self.sceneRect()
        new_scene_rect = scene_rect.adjusted(x_amount, y_amount, x_amount, y_amount)
        self.setSceneRect(new_scene_rect)

    def _reset_zoom(self):
        """
        Reset any zoom applied previously.
        """
        zoom_inverse = 1.0 / self._zoom
        self._zoom_viewport(zoom_inverse, QtGui.QCursor.pos())

    def _update_scene_rect(self):
        """
        apply zoom and resize to the sceneRect
        """
        scene_rect = self.sceneRect()

        # -0.5 to avoid instability, else we sometime have scrollbar popping
        scene_rect.setWidth(self.viewport().size().width() / self._zoom - 0.5)
        scene_rect.setHeight(self.viewport().size().height() / self._zoom - 0.5)
        self.setSceneRect(scene_rect)

        transform = QtGui.QTransform()
        transform.scale(self._zoom, self._zoom)
        self.setTransform(transform)

    def _zoom_viewport(self, amount: float, cursor_pos: QtCore.QPoint):
        """
        Args:
            cursor_pos: cursor position in global coordinates, used to "center" the zoom
            amount: zoom amount to apply, 1 means no zoom, [0-1] range
        """
        new_zoom = self._zoom * amount

        # limit zoom
        if new_zoom < self.zoom_min or new_zoom > self.zoom_max:
            return

        self._zoom = new_zoom
        previous_pos = self.mapToScene(self.mapFromGlobal(cursor_pos))
        self._update_scene_rect()
        after_pos = self.mapToScene(self.mapFromGlobal(cursor_pos))
        pos_diff = previous_pos - after_pos
        # offset back the viewport to make it look like we zoom relative to
        # the cursor position
        self._pan_viewport(pos_diff.x(), pos_diff.y())

    # Overrides

    def drawBackground(self, painter: QtGui.QPainter, rect: QtCore.QRectF):
        """
        Generated a grid pattern as background.
        """
        painter.fillRect(rect, self._background_color)
        grid_thickness = 2.0
        grid_size = 20

        # too low zoom produce performance issue and mess up visually anyway
        if self._zoom <= 0.3:
            return

        pen = QtGui.QPen(self._background_grid_color, grid_thickness)
        painter.setPen(pen)

        points = generate_points_grid(surface=rect, size=grid_size)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        painter.drawPoints(points)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        """
        Configure key shortucts.
        """
        # TODO expose shortcuts as variables
        if event.key() == QtCore.Qt.Key_Home:
            self._reset_zoom()
            return

        super().keyPressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        super().mouseMoveEvent(event)

        if self._state == self.states.noneState:
            return

        self._mouse_previous_pos = self._mouse_previous_pos or event.pos()
        self._mouse_initial_pos = self._mouse_initial_pos or QtGui.QCursor.pos()
        diff_x = float(self._mouse_previous_pos.x() - event.pos().x())
        diff_y = float(self._mouse_previous_pos.y() - event.pos().y())

        if self._state & self.states.panState:
            # need to compensate as sceneRect change size if zoomed
            diff_x = diff_x / self._zoom
            diff_y = diff_y / self._zoom
            self._pan_viewport(diff_x, diff_y)

        if self._state & self.states.zoomState:
            amount = 1 + (diff_x or diff_y) * 0.01
            self._zoom_viewport(amount, self._mouse_initial_pos)

        # TODO select, pick, unpick states

        self._mouse_previous_pos = event.pos()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """
        On mouse button pressed, set states depending on buttons.
        """
        super().mousePressEvent(event)
        self._mouse_initial_pos = QtGui.QCursor.pos()
        self._selected_items_initial = self.scene().selectedItems()

        # TODO expose shortcuts as variables
        if (
            event.button() == QtCore.Qt.LeftButton
            and event.modifiers() == QtCore.Qt.AltModifier
        ) or (
            event.button() == QtCore.Qt.MiddleButton
            and event.modifiers() == QtCore.Qt.NoModifier
        ):
            self._state = self._state | self.states.panState

        elif (
            event.button() == QtCore.Qt.MiddleButton
            and event.modifiers() == QtCore.Qt.AltModifier
        ):
            self._state = self._state | self.states.zoomState

        elif (
            event.button() == QtCore.Qt.LeftButton
            and event.modifiers() == QtCore.Qt.NoModifier
            # ensure the user is not clicking an item
            and not self.items(event.pos())
        ):
            self._rubber_band.setGeometry(QtCore.QRect(event.pos(), QtCore.QSize()))
            self._rubber_band.show()
            self._state = self._state | self.states.selectState

        elif (
            event.button() == QtCore.Qt.LeftButton
            and event.modifiers() == QtCore.Qt.ControlModifier
            # ensure the user is not clicking an item
            and not self.items(event.pos())
        ):
            self._rubber_band.setGeometry(QtCore.QRect(event.pos(), QtCore.QSize()))
            self._rubber_band.show()
            self._state = self._state | self.states.unpickState

        elif (
            event.button() == QtCore.Qt.LeftButton
            and event.modifiers() == QtCore.Qt.ShiftModifier
            # ensure the user is not clicking an item
            and not self.items(event.pos())
        ):
            self._rubber_band.setGeometry(QtCore.QRect(event.pos(), QtCore.QSize()))
            self._rubber_band.show()
            self._state = self._state | self.states.pickState

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        """
        On mouse button release, reset all variables.
        """
        super().mouseReleaseEvent(event)
        self._mouse_previous_pos = None
        self._mouse_initial_pos = None
        self._selected_items_initial = []
        self._rubber_band.hide()

        if event.button() == QtCore.Qt.LeftButton and not self.scene().selectedItems():
            self.scene().setSelectionArea(QtGui.QPainterPath())

        if self._state & self.states.panState:
            self._state = self._state ^ self.states.panState
        if self._state & self.states.zoomState:
            self._state = self._state ^ self.states.zoomState
        if self._state & self.states.selectState:
            self._state = self._state ^ self.states.selectState
        if self._state & self.states.unpickState:
            self._state = self._state ^ self.states.unpickState
        if self._state & self.states.pickState:
            self._state = self._state ^ self.states.pickState

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._update_scene_rect()

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """
        On mouse wheel active, zoom the viewport.
        """
        delta = event.angleDelta().y()
        amount = 2 ** (delta * 0.001)
        self._zoom_viewport(amount, QtGui.QCursor.pos())
