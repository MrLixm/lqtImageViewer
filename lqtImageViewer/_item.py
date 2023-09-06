import logging
import random
from typing import Optional

import numpy
from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets


LOGGER = logging.getLogger(__name__)


def _generate_default_image(image_size=512, tile_number=5, noise_opacity=5):
    """
    Generate a checker image to use as default when no image loaded yet.

    Args:
        image_size: in pixels, width and height of the image.
        tile_number: number of checker tile visible. MUST be uneven number.
        noise_opacity: [0-255] range, opcaity of the random nosie layered on top.
    """
    tile_size = image_size / tile_number

    image = QtGui.QImage(image_size, image_size, QtGui.QImage.Format_RGB888)
    image.fill(QtGui.QColor(100, 100, 100))

    painter = QtGui.QPainter(image)
    painter.setRenderHint(painter.Antialiasing, False)

    # we precalculate a tile of noise that will be repeated, to avoid performance hit
    # it is faster than iterating over all the image pixel to draw a random color
    pixmap_noise = QtGui.QPixmap(int(tile_size), int(tile_size))
    pixmap_noise.fill(QtGui.QColor(0, 0, 0, 0))
    painter_noise = QtGui.QPainter(pixmap_noise)
    # arbitrary seed to ensure noise pattern is the same between runs
    random.seed(4325615)
    for x in range(int(tile_size)):
        for y in range(int(tile_size)):
            color = random.randint(0, 255)
            painter_noise.fillRect(
                QtCore.QRect(x, y, 1, 1),
                QtGui.QColor(color, color, color, noise_opacity),
            )
    painter_noise.end()

    for tile_n_x in range(0, tile_number, 1):
        for tile_n_y in range(0, tile_number, 1):
            rect = QtCore.QRectF(
                tile_size * tile_n_x,
                tile_size * tile_n_y,
                tile_size,
                tile_size,
            )
            if (tile_n_x + tile_n_y) % 2 == 0:
                painter.fillRect(rect, QtGui.QColor(135, 135, 135))
            painter.drawPixmap(rect.toRect(), pixmap_noise)

    painter.end()
    return image


class ImageItem(QtWidgets.QGraphicsItem):
    def __init__(
        self,
        parent: Optional[QtWidgets.QGraphicsItem] = None,
        default_image: Optional[QtGui.QImage] = None,
    ) -> None:
        super().__init__(parent)

        self._image: QtGui.QImage = default_image or _generate_default_image()
        self._array: Optional[numpy.ndarray] = None

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

        LOGGER.debug(f"generating QImage from array {array.shape} ...")

        self._image = QtGui.QImage(
            self._array,
            array.shape[1],
            array.shape[0],
            QtGui.QImage.Format_RGBA64,
        )
        self.update()

    # Overrides

    def boundingRect(self) -> QtCore.QRectF:
        return QtCore.QRectF(self._image.rect())

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        painter.drawImage(option.rect, self._image)
