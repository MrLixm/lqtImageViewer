import enum
import logging
from typing import Optional

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from ._config import LIVKeyShortcuts
from ._config import BaseBackgroundStyle
from ._config import BackgroundStyleLibrary
from ._item import ImageItem
from ._scene import LIVGraphicScene
from .plugins import BasePluginType

LOGGER = logging.getLogger(__name__)


class GraphicViewState(enum.IntFlag):
    noneState = enum.auto()
    panState = enum.auto()
    zoomState = enum.auto()
    pickState = enum.auto()
    unpickState = enum.auto()


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
        new_zoom = round(new_zoom, 6)

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
        super().mousePressEvent(event)
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
        super().wheelEvent(event)
        delta = event.angleDelta().y()
        amount = 2 ** (delta * 0.001)
        self._zoom_viewport(amount, QtGui.QCursor.pos())


class LIVGraphicView(NavigableGraphicView):
    def __init__(
        self,
        scene: LIVGraphicScene,
        key_shortcuts: Optional[LIVKeyShortcuts] = None,
        background_style: Optional[BaseBackgroundStyle] = None,
    ):
        super().__init__(scene=scene, key_shortcuts=key_shortcuts)
        self._scene: LIVGraphicScene = scene
        self._plugins: list[BasePluginType] = []

        self._background_style = (
            background_style or BackgroundStyleLibrary.dark_grid_dot
        )

        self.setCacheMode(self.CacheBackground)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self._center_image()

    @property
    def background_style(self) -> BaseBackgroundStyle:
        return self._background_style

    @background_style.setter
    def background_style(self, new_background_style: BaseBackgroundStyle):
        self._background_style = new_background_style
        self.resetCachedContent()
        self.update()

    @property
    def image_item(self) -> ImageItem:
        return self._scene.image_item

    def _center_image(self):
        image_rect = self.get_image_rect()
        scene_rect = self.sceneRect()
        scene_rect.moveCenter(image_rect.center())
        self.setSceneRect(scene_rect)

    def _update_plugins(self):
        """
        Propagate zoom changes to the plugins, so they can update visually.
        """
        for plugin in self._plugins:
            plugin.transform = self.transform()
            plugin.reload()

    def add_plugin(self, plugin: BasePluginType):
        """
        Add the given plugin to handle in the scene and view.
        """
        if plugin in self._plugins:
            return

        self._plugins.append(plugin)
        self.scene().addItem(plugin)
        plugin.reload()

    def get_image_rect(self) -> QtCore.QRectF:
        """
        Get the image area in scene coordinates relative to himself.

        (top-left start at 0,0)
        """
        return self._scene.image_item.sceneBoundingRect()

    # Overrides

    def _zoom_viewport(self, amount: float, cursor_pos: QtCore.QPoint):
        super()._zoom_viewport(amount, cursor_pos)
        self._update_plugins()

    def drawBackground(self, painter: QtGui.QPainter, rect: QtCore.QRectF):
        """
        Generated a grid pattern as background.
        """
        draw_texture = self._background_style.should_use_background_texture(self._zoom)
        brush = self._background_style.generate_background_brush(draw_texture)
        painter.fillRect(rect, brush)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        """
        Configure key shortucts.
        """
        if self._shortcuts.change_background.match_event(event):
            self._background_style = BackgroundStyleLibrary.next(self._background_style)
            self.resetCachedContent()
            self.update()
            return

        elif self._shortcuts.reset_pan.match_event(event):
            self._center_image()
            return

        super().keyPressEvent(event)
