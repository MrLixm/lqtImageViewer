import logging

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

from ._item import ImageItem
from .config import LIVKeyShortcuts

LOGGER = logging.getLogger(__name__)


class LIVGraphicScene(QtWidgets.QGraphicsScene):
    """
    A QGraphicsScene that holds the image to display.

    It also stores the shortcuts for user interaction.
    """

    def __init__(self, image_item: ImageItem, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._image_item = image_item
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
