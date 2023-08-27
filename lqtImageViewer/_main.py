import logging

import numpy
from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from lqtImageViewer._view import LIVGraphicView
from lqtImageViewer._item import ImageItem
from lqtImageViewer._encoding import convert_bit_depth
from lqtImageViewer._encoding import ensure_rgba_array


LOGGER = logging.getLogger(__name__)


class LqtImageViewer(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        # 1. Create
        self.layout_main = QtWidgets.QVBoxLayout()
        # we need only a single item
        self.graphic_item = ImageItem()
        self.graphic_scene = QtWidgets.QGraphicsScene(-1280 / 2, -720 / 2, 1280, 720)
        self.graphic_view = LIVGraphicView(self.graphic_scene)

        # 2. Add
        self.setLayout(self.layout_main)
        self.layout_main.addWidget(self.graphic_view)
        self.graphic_scene.addItem(self.graphic_item)

        # 3. Modify
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.graphic_item.move_to_scene_origin()
        self.graphic_item.setSelected(True)

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

        self.graphic_item.set_image_array(array)
