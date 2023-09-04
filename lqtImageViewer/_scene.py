import logging

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from ._item import ImageItem

LOGGER = logging.getLogger(__name__)


class LIVGraphicScene(QtWidgets.QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._image_item = ImageItem()
        self.addItem(self._image_item)

    @property
    def image_item(self) -> ImageItem:
        return self._image_item
