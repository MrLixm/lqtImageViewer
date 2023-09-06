import logging
from typing import Optional

import numpy
from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from lqtImageViewer.config import LIVKeyShortcuts
from lqtImageViewer._scene import LIVGraphicScene
from lqtImageViewer._view import LIVGraphicView
from lqtImageViewer._encoding import convert_bit_depth
from lqtImageViewer._encoding import ensure_rgba_array
from lqtImageViewer.plugins import BasePluginType
from lqtImageViewer.plugins import CoordinatesGridPlugin
from lqtImageViewer.plugins import ColorPickerPlugin

LOGGER = logging.getLogger(__name__)


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
        self.layout_main = QtWidgets.QVBoxLayout()
        self.graphic_scene = LIVGraphicScene(-1280 / 2, -720 / 2, 1280, 720)
        self.graphic_view = LIVGraphicView(
            scene=self.graphic_scene,
            key_shortcuts=self._shortcuts,
        )
        self.plugin_color_picker = ColorPickerPlugin()
        self.plugins_coord = CoordinatesGridPlugin()

        # 2. Add
        self.setLayout(self.layout_main)
        self.layout_main.addWidget(self.graphic_view)
        LOGGER.debug(f"registering builtin plugin {self.plugins_coord}")
        self.add_plugin(self.plugins_coord)
        LOGGER.debug(f"registering builtin plugin {self.plugin_color_picker}")
        self.add_plugin(self.plugin_color_picker)

        # 3. Modify
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.graphic_scene.installEventFilter(self)
        self.graphic_scene.shortcuts = self._shortcuts

    @property
    def color_picker(self):
        """
        Get the color picker builtin plugin.
        """
        return self.plugin_color_picker

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
        self._plugins.append(plugin)
        self.graphic_view.add_plugin(plugin)

    def get_color_picked_area(self) -> Optional[QtCore.QRect]:
        """
        Return the area that is currently being color picked, in pixel scene coordinates.

        Retrun None if no area is being picked right now.
        """
        if not self.plugin_color_picker.isVisible():
            return None
        return self.plugin_color_picker.get_picked_area()

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
        [plugin.reload() for plugin in self._plugins]

    # Overrides

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched is self.graphic_scene:
            [plugin.set_visibility_from_scene_event(event) for plugin in self._plugins]
        return super().eventFilter(watched, event)
