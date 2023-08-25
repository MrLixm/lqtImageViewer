import dataclasses
import enum
import logging
from typing import Optional

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

LOGGER = logging.getLogger(__name__)


class GraphicViewState(enum.IntFlag):
    noneState = enum.auto()
    panState = enum.auto()
    zoomState = enum.auto()
    selectState = enum.auto()
    pickState = enum.auto()
    unpickState = enum.auto()


@dataclasses.dataclass(frozen=True)
class _BackgroundStyle:
    label: str
    primary: QtGui.QColor
    secondary: QtGui.QColor
    draw_grid: bool


class BackgroundStyle(enum.Enum):
    light = _BackgroundStyle(
        "Light",
        QtGui.QColor(240, 240, 238),
        QtGui.QColor(200, 200, 200),
        False,
    )
    light_grid_dot = _BackgroundStyle(
        "Light Grid of Dots",
        QtGui.QColor(240, 240, 238),
        QtGui.QColor(200, 200, 200),
        True,
    )
    mid_grey = _BackgroundStyle(
        "Mid Grey",
        QtGui.QColor(125, 125, 125),
        QtGui.QColor(100, 100, 100),
        False,
    )
    dark_grid_dot = _BackgroundStyle(
        "Dark Grid of Dots",
        QtGui.QColor(0, 0, 0),
        QtGui.QColor(30, 30, 30),
        True,
    )
    dark = _BackgroundStyle(
        "Dark",
        QtGui.QColor(0, 0, 0),
        QtGui.QColor(30, 30, 30),
        False,
    )

    @classmethod
    def all(cls):
        return [
            cls.light,
            cls.light_grid_dot,
            cls.mid_grey,
            cls.dark,
            cls.dark_grid_dot,
        ]

    @classmethod
    def next(cls, style: "BackgroundStyle"):
        all_styles = cls.all()
        index = all_styles.index(style)
        try:
            return all_styles[index + 1]
        except IndexError:
            return all_styles[0]


def create_dot_grid(background_color: QtGui.QColor, foreground_color: QtGui.QColor):
    """
    Generate the pattern necessary to build a grid of dots once tiles.
    """
    resolution = 1024
    dot_size = 50
    center = QtCore.QPointF(resolution // 2, resolution // 2)

    gradient = QtGui.QRadialGradient(center, 50)
    gradient.setColorAt(1, QtCore.Qt.transparent)
    gradient.setColorAt(0, foreground_color)
    gradient.setFocalRadius(44)

    pixmap = QtGui.QPixmap(QtCore.QSize(resolution, resolution))
    pixmap.fill(background_color)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(painter.Antialiasing)

    painter.setPen(QtCore.Qt.PenStyle.NoPen)
    painter.setBrush(QtGui.QBrush(gradient))
    painter.drawEllipse(center, dot_size, dot_size)
    painter.end()
    return pixmap


class LIVGraphicView(QtWidgets.QGraphicsView):
    states = GraphicViewState

    zoom_min = 0.1
    zoom_max = 7

    selection_mode = QtCore.Qt.IntersectsItemShape

    def __init__(self, scene: QtWidgets.QGraphicsScene):
        super().__init__(scene)

        self._state = GraphicViewState.noneState
        # save at each move
        self._mouse_previous_pos: Optional[QtCore.QPoint] = None
        # save at each click
        self._mouse_initial_pos: Optional[QtCore.QPoint] = None
        self._selected_items_initial: list[QtWidgets.QGraphicsItem] = []
        self._rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)

        self._background_style = BackgroundStyle.dark_grid_dot
        self._zoom: float = 1.0

        self._grid_cache = self._cache_grid()

        self.setCacheMode(self.CacheBackground)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

    @property
    def background_style(self) -> BackgroundStyle:
        return self._background_style

    @background_style.setter
    def background_style(self, new_background_style: BackgroundStyle):
        self._background_style = new_background_style

    def _cache_grid(self):
        grid_shape = create_dot_grid(
            self._background_style.value.primary,
            self._background_style.value.secondary,
        )

        grid_brush = QtGui.QBrush(self._background_style.value.primary)
        grid_brush.setTexture(grid_shape)
        # hack to avoid pixelated image when zooming
        transform = QtGui.QTransform()
        transform.scale(0.05, 0.05)
        grid_brush.setTransform(transform)

        self._grid_cache = grid_brush
        return self._grid_cache

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
        brush = self._background_style.value.primary
        if self._zoom > 0.3 and self._background_style.value.draw_grid:
            brush = self._grid_cache
        painter.fillRect(rect, brush)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        """
        Configure key shortucts.
        """
        # TODO expose shortcuts as variables
        if event.key() == QtCore.Qt.Key_Home:
            self._reset_zoom()
            return

        elif event.key() == QtCore.Qt.Key_B:
            self._background_style = self._background_style.next(self._background_style)
            self._cache_grid()
            self.resetCachedContent()
            self.update()
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
