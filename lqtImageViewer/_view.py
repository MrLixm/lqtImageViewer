import enum
import logging
import typing
from typing import Optional

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from ._config import LIVKeyShortcuts
from ._config import BackgroundStyle
from ._item import ImageItem
from ._scene import LIVGraphicScene
from ._scene import ScreenSpaceGraphicsScene

LOGGER = logging.getLogger(__name__)


class GraphicViewState(enum.IntFlag):
    noneState = enum.auto()
    panState = enum.auto()
    zoomState = enum.auto()
    pickState = enum.auto()
    unpickState = enum.auto()


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


class NavigableGraphicView(QtWidgets.QGraphicsView):
    states = GraphicViewState

    zoom_enable = True
    """
    Used to disable zoom capabilities on subclasses
    """
    zoom_min = 0.1
    zoom_max = 20

    def __init__(
        self,
        scene: QtWidgets.QGraphicsScene,
        key_shortcuts: Optional[LIVKeyShortcuts] = None,
    ):
        super().__init__(scene)
        self._shortcuts = key_shortcuts or LIVKeyShortcuts.get_default()
        self._state = GraphicViewState.noneState
        self._zoom: float = 1.0
        # save at each move
        self._mouse_previous_pos: Optional[QtCore.QPoint] = None
        # save at each click
        self._mouse_initial_pos: Optional[QtCore.QPoint] = None

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

        if self.zoom_enable:
            # -0.5 to avoid instability, else we sometime have scrollbar popping
            width = self.viewport().size().width() / self._zoom - 0.5
            height = self.viewport().size().height() / self._zoom - 0.5
        else:
            width = self.viewport().size().width()
            height = self.viewport().size().height()

        scene_rect.setWidth(width)
        scene_rect.setHeight(height)
        self.setSceneRect(scene_rect)

        if self.zoom_enable:
            transform = QtGui.QTransform()
            transform.scale(self._zoom, self._zoom)
            self.setTransform(transform)

    def _zoom_viewport(self, amount: float, cursor_pos: QtCore.QPoint):
        """
        Args:
            cursor_pos: cursor position in global coordinates, used to "center" the zoom
            amount: zoom amount to apply, 1 means no zoom, [0-1] range
        """
        if not self.zoom_enable:
            return

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

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        """
        Configure key shortucts.
        """
        if self._shortcuts.reset_zoom.match_event(event):
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

        self._mouse_previous_pos = event.pos()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """
        On mouse button pressed, set states depending on buttons.
        """
        self._mouse_initial_pos = QtGui.QCursor.pos()
        self._selected_items_initial = self.scene().selectedItems()

        if self._shortcuts.pan1.match_event(event) or self._shortcuts.pan2.match_event(
            event
        ):
            self._state = self._state | self.states.panState

        elif self._shortcuts.zoom2.match_event(event):
            self._state = self._state | self.states.zoomState

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        """
        On mouse button release, reset all variables.
        """
        super().mouseReleaseEvent(event)
        self._mouse_previous_pos = None
        self._mouse_initial_pos = None
        self._selected_items_initial = []

        if self._state & self.states.panState:
            self._state = self._state ^ self.states.panState
        if self._state & self.states.zoomState:
            self._state = self._state ^ self.states.zoomState

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


class LIVGraphicView(NavigableGraphicView):
    def __init__(
        self,
        scene: LIVGraphicScene,
        key_shortcuts: Optional[LIVKeyShortcuts] = None,
        background_style: Optional[BackgroundStyle] = None,
    ):
        super().__init__(scene=scene, key_shortcuts=key_shortcuts)
        self._scene: LIVGraphicScene = scene

        self._background_style = background_style or BackgroundStyle.dark_grid_dot
        self._grid_cache = self._cache_grid()

        self.setCacheMode(self.CacheBackground)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self._center_image()

    @property
    def background_style(self) -> BackgroundStyle:
        return self._background_style

    @background_style.setter
    def background_style(self, new_background_style: BackgroundStyle):
        self._background_style = new_background_style

    @property
    def image_item(self) -> ImageItem:
        return self._scene.image_item

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

    def _center_image(self):
        image_rect = self.get_image_rect()
        scene_rect = self.sceneRect()
        scene_rect.moveCenter(image_rect.center())
        self.setSceneRect(scene_rect)

    def get_image_rect(self) -> QtCore.QRectF:
        """
        Get the image area in scene coordinates relative to himself.

        (top-left start at 0,0)
        """
        return self._scene.image_item.sceneBoundingRect()

    @typing.overload
    def map_to_image_coordinates(self, obj: QtGui.QPainterPath) -> QtGui.QPainterPath:
        ...

    @typing.overload
    def map_to_image_coordinates(self, obj: QtCore.QPoint) -> QtCore.QPointF:
        ...

    @typing.overload
    def map_to_image_coordinates(self, obj: QtCore.QRect) -> QtGui.QPolygonF:
        ...

    @typing.overload
    def map_to_image_coordinates(self, obj: QtGui.QPolygon) -> QtGui.QPolygonF:
        ...

    def map_to_image_coordinates(self, obj):
        """
        Convert local widget coordinates to image scene coordinates.

        Image coordinates assume top-left is x=0,y=0
        """
        return self.image_item.mapFromScene(self.mapToScene(obj))

    @typing.overload
    def map_from_image_coordinates(self, obj: QtGui.QPainterPath) -> QtGui.QPainterPath:
        ...

    @typing.overload
    def map_from_image_coordinates(self, obj: QtCore.QPointF) -> QtCore.QPoint:
        ...

    @typing.overload
    def map_from_image_coordinates(self, obj: QtCore.QRectF) -> QtGui.QPolygon:
        ...

    @typing.overload
    def map_from_image_coordinates(self, obj: QtGui.QPolygonF) -> QtGui.QPolygon:
        ...

    def map_from_image_coordinates(self, obj):
        """
        Convert scene image coordinates to local widget coordinates.

        Image coordinates assume top-left is x=0,y=0
        """
        return self.mapFromScene(self.image_item.mapToScene(obj))

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
        if self._shortcuts.change_background.match_event(event):
            self._background_style = self._background_style.next(self._background_style)
            self._cache_grid()
            self.resetCachedContent()
            self.update()
            return

        elif self._shortcuts.reset_pan.match_event(event):
            self._center_image()
            return

        super().keyPressEvent(event)


class ScreenSpaceGraphicsView(NavigableGraphicView):
    states = GraphicViewState
    zoom_enable = False

    def __init__(
        self,
        scene: ScreenSpaceGraphicsScene,
        view_background: LIVGraphicView,
        key_shortcuts: Optional[LIVKeyShortcuts] = None,
    ):
        super().__init__(scene=scene, key_shortcuts=key_shortcuts)
        self._scene: ScreenSpaceGraphicsScene = scene
        self._view_background: LIVGraphicView = view_background
        # XXX: only way to make the background transparent
        self.setStyleSheet("background: transparent;")

    def get_image_rect(self):
        """
        Get the image area in scene coordinates relative to himself.

        (top-left start at 0,0)
        """
        return self._view_background.get_image_rect()

    @typing.overload
    def map_to_image_coordinates(self, obj: QtGui.QPainterPath) -> QtGui.QPainterPath:
        ...

    @typing.overload
    def map_to_image_coordinates(self, obj: QtCore.QPoint) -> QtCore.QPointF:
        ...

    @typing.overload
    def map_to_image_coordinates(self, obj: QtCore.QRect) -> QtGui.QPolygonF:
        ...

    @typing.overload
    def map_to_image_coordinates(self, obj: QtGui.QPolygon) -> QtGui.QPolygonF:
        ...

    def map_to_image_coordinates(self, obj):
        """
        Convert local widget coordinates to image scene coordinates.

        Image coordinates assume top-left is x=0,y=0
        """
        mapped = self.mapFromScene(self._view_background.map_to_image_coordinates(obj))
        if isinstance(mapped, QtGui.QPolygon):
            mapped = QtGui.QPolygonF(mapped)
        elif isinstance(mapped, QtCore.QRect):
            mapped = QtCore.QRectF(mapped)
        elif isinstance(mapped, QtCore.QPoint):
            mapped = QtCore.QPointF(mapped)
        return mapped

    @typing.overload
    def map_from_image_coordinates(self, obj: QtGui.QPainterPath) -> QtGui.QPainterPath:
        ...

    @typing.overload
    def map_from_image_coordinates(self, obj: QtCore.QPointF) -> QtCore.QPoint:
        ...

    @typing.overload
    def map_from_image_coordinates(self, obj: QtCore.QRectF) -> QtGui.QPolygon:
        ...

    @typing.overload
    def map_from_image_coordinates(self, obj: QtGui.QPolygonF) -> QtGui.QPolygon:
        ...

    def map_from_image_coordinates(self, obj):
        """
        Convert image coordinates to local widget coordinates.

        Image coordinates assume top-left is x=0,y=0
        """
        mapped = self.mapToScene(self._view_background.map_from_image_coordinates(obj))
        if isinstance(mapped, QtGui.QPolygonF):
            mapped = mapped.toPolygon()
        elif isinstance(mapped, QtCore.QRectF):
            mapped = mapped.toRect()
        elif isinstance(mapped, QtCore.QPointF):
            mapped = mapped.toPoint()
        return mapped
