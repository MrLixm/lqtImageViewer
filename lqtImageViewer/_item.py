import logging
from typing import Optional

import numpy
from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets


LOGGER = logging.getLogger(__name__)


def _generate_default_image():
    image_size = 512
    tile_number = 5
    tile_size = image_size / tile_number

    image = QtGui.QImage(image_size, image_size, QtGui.QImage.Format_RGB888)
    image.fill(QtGui.QColor(100, 100, 100))

    painter = QtGui.QPainter(image)
    painter.setRenderHint(painter.Antialiasing, False)

    for tile_n_x in range(0, tile_number, 1):
        for tile_n_y in range(0, tile_number, 1):
            if (tile_n_x + tile_n_y) % 2 == 0:
                rect = QtCore.QRectF(
                    tile_size * tile_n_x,
                    tile_size * tile_n_y,
                    tile_size,
                    tile_size,
                )
                painter.fillRect(rect, QtGui.QColor(135, 135, 135))

    painter.end()
    return image


class ImageItem(QtWidgets.QGraphicsItem):
    def __init__(self, parent: Optional[QtWidgets.QGraphicsItem] = None) -> None:
        super().__init__(parent)
        self._image: QtGui.QImage = _generate_default_image()
        self._array: Optional[numpy.ndarray] = None
        self._is_mouse_over: bool = False
        self.setFlag(self.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

    @property
    def is_mouse_hover(self) -> bool:
        """
        Return True if the mouse cursor is currently hovering that item.
        """
        return self._is_mouse_over

    def move_to_scene_origin(self):
        self.setPos(0, 0)
        self.moveBy(-self.boundingRect().width() / 2, -self.boundingRect().height() / 2)

    def set_image_array(self, array: Optional[numpy.ndarray]):
        """
        References:
            - [1] https://stackoverflow.com/a/55522279/13806195

        Args:
            array: MUST be an uint16 R-G-B-A array (4 channels)
        """
        if array is None:
            self._array = None
            self._image = _generate_default_image()
            return

        # we keep an internal reference to avoid garbage collection
        self._array = array.tobytes()

        LOGGER.debug("generating QImage ...")

        self._image = QtGui.QImage(
            self._array,
            array.shape[1],
            array.shape[0],
            QtGui.QImage.Format_RGBA64,
        )
        self.update()
        self.move_to_scene_origin()

    # Overrides

    def boundingRect(self) -> QtCore.QRectF:
        return QtCore.QRectF(self._image.rect())

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        self._is_mouse_over = True

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        self._is_mouse_over = False

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        painter.drawImage(option.rect, self._image)
