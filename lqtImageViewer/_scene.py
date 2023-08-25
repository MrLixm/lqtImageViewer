from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets


class LIVGraphicScene(QtWidgets.QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        # we want to have item unselected on double click
        # TODO test if it unselect in the rubber band
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        # prevent item un-selection on single click by not calling super
        if event.button() in [
            QtCore.Qt.LeftButton,
            QtCore.Qt.MiddleButton,
            QtCore.Qt.RightButton,
        ] and not self.items(event.scenePos()):
            return
        super().mousePressEvent(event)
