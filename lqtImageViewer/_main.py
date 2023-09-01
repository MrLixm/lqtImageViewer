import logging

import numpy
from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from lqtImageViewer._config import LIVKeyShortcuts
from lqtImageViewer._scene import LIVGraphicScene
from lqtImageViewer._scene import ScreenSpaceGraphicsScene
from lqtImageViewer._view import LIVGraphicView
from lqtImageViewer._view import ScreenSpaceGraphicsView
from lqtImageViewer._encoding import convert_bit_depth
from lqtImageViewer._encoding import ensure_rgba_array
from lqtImageViewer._plugin import BasePluginType
from lqtImageViewer._plugin import BaseScreenSpacePlugin

LOGGER = logging.getLogger(__name__)


class MouseEventCatcher(QtWidgets.QWidget):
    """
    A widget made to be top level and just catch mosue events.
    """

    def __init__(self):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_AlwaysStackOnTop)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)


class LqtImageViewport(QtWidgets.QWidget):
    """
    A widget showing a rectangular area called "viewport". The viewport is an infinite
    2D canvas containing the image to display.

    You can move in that canvas freely, using panning or zooming.

    That viewport doesn't know anything about image processing, like isolating channels,
    color-management and so on. It just displays directly the numpy array.
    """

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self._plugins: list[BasePluginType] = []
        self._shortcuts = LIVKeyShortcuts.get_default()

        # 1. Create
        self.event_catcher = MouseEventCatcher()
        self.graphic_scene = LIVGraphicScene(0, 0, 128, 128)
        self.graphic_scene_top = ScreenSpaceGraphicsScene(0, 0, 128, 128)
        self.graphic_view = LIVGraphicView(
            scene=self.graphic_scene,
            key_shortcuts=self._shortcuts,
        )
        self.graphic_view_top = ScreenSpaceGraphicsView(
            scene=self.graphic_scene_top,
            view_background=self.graphic_view,
            key_shortcuts=self._shortcuts,
        )

        # 2. Add
        self.graphic_view.setParent(self)
        self.graphic_view_top.setParent(self)
        # ! must be added last to be on top
        self.event_catcher.setParent(self)

        # 3. Modify
        self.event_catcher.installEventFilter(self)

    def resizeEvent(self, event: QtGui.QResizeEvent):
        super().resizeEvent(event)
        geometry = self.geometry()
        self.event_catcher.setGeometry(geometry)
        self.graphic_view.setGeometry(geometry)
        self.graphic_view_top.setGeometry(geometry)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched != self.event_catcher:
            return super().eventFilter(watched, event)

        if event.type() in (
            event.MouseButtonPress,
            event.MouseButtonRelease,
            event.MouseMove,
            event.Wheel,
        ):
            QtWidgets.QApplication.sendEvent(self.graphic_view.viewport(), event)
            QtWidgets.QApplication.sendEvent(self.graphic_view_top.viewport(), event)
            return True

        return super().eventFilter(watched, event)

    def set_image_from_array(self, array: numpy.ndarray):
        """
        Set the image displayed, from a numpy array.

        Args:
            array: SHOULD be an uint16 R-G-B-A array (4 channels), else the method will
            try to uniform it, so it become encoded as such.
        """
        if array.dtype != numpy.core.uint16:
            LOGGER.debug(f"converting array dtype from {array.dtype} to uint16 ...")
            array = convert_bit_depth(array, numpy.core.uint16)

        if len(array.shape) == 2 or array.shape[2] != 4:
            LOGGER.debug(f"ensuring array of shape {array.shape} has 4 channels ...")
            array = ensure_rgba_array(array)

        self.graphic_scene.image_item.set_image_array(array)

    def add_plugin(self, plugin: BasePluginType):
        """
        Add the given plugin to handle.

        Args:
            plugin:
                instance of the plugin to draw when necessary.
                already-added plugins are handled properly (discarded).
        """
        if plugin in self._plugins:
            return

        if isinstance(plugin, BaseScreenSpacePlugin):
            plugin.initialize(screenspace_view=self.graphic_view_top)
        else:
            raise TypeError(f"Unsupported plugin subclass {plugin}")

        self._plugins.append(plugin)
