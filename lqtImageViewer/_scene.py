import logging

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from ._item import ImageItem
from .config import LIVKeyShortcuts

LOGGER = logging.getLogger(__name__)


class LIVGraphicScene(QtWidgets.QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._image_item = ImageItem()
        self._shortcuts = LIVKeyShortcuts.get_default()
        self.addItem(self._image_item)

    @property
    def shortcuts(self) -> LIVKeyShortcuts:
        return self._shortcuts

    @shortcuts.setter
    def shortcuts(self, new_shortcuts: LIVKeyShortcuts):
        self._shortcuts = new_shortcuts

    @property
    def image_item(self) -> ImageItem:
        return self._image_item
