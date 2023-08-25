import numpy
from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from lqtImageViewer._view import LIVGraphicView
from lqtImageViewer._item import ImageItem


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
            array: MUST be an uint16 R-G-B array (3 channels)
        """
        if array.dtype != numpy.core.uint16:
            raise TypeError(f"Array dtype must be uint16, not {array.dtype}")
        if array.shape[2] != 4:
            raise TypeError(
                f"Number of array's channel must be 4, not {array.shape[2]}"
            )

        self.graphic_item.set_image_array(array)
