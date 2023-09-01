import abc
import logging
import typing
from typing import Optional

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from ._view import ScreenSpaceGraphicsView


LOGGER = logging.getLogger(__name__)


class BaseScreenSpacePlugin(QtWidgets.QGraphicsItem):
    """
    A special QGraphicsItem that is actually aware of the view it is indirectly child of.
    """

    def __init__(self) -> None:
        super().__init__()
        self._view: Optional[ScreenSpaceGraphicsView] = None
        self.__initialized = False

    def initialize(
        self,
        screenspace_view: ScreenSpaceGraphicsView,
    ):
        """
        "Load" the plugin with the given "context".
        """
        if self.__initialized:
            raise RuntimeError(f"Plugin instance {self} is already initialized.")

        self._view = screenspace_view
        self._view.scene().addItem(self)
        self.__initialized = True

    @typing.overload
    def map_to_image_coordinates(self, obj: QtGui.QPainterPath) -> QtGui.QPainterPath:
        ...

    @typing.overload
    def map_to_image_coordinates(self, obj: QtCore.QPoint) -> QtCore.QPointF:
        ...

    @typing.overload
    def map_to_image_coordinates(self, obj: QtCore.QRect) -> QtGui.QPolygonF:
        ...

    @typing.overload
    def map_to_image_coordinates(self, obj: QtGui.QPolygon) -> QtGui.QPolygonF:
        ...

    def map_to_image_coordinates(self, obj):
        """
        Convert local widget coordinates to image coordinates.

        Image coordinates assume top-left is x=0,y=0
        """
        return self._view.map_to_image_coordinates(obj)

    @typing.overload
    def map_from_image_coordinates(self, obj: QtGui.QPainterPath) -> QtGui.QPainterPath:
        ...

    @typing.overload
    def map_from_image_coordinates(self, obj: QtCore.QPointF) -> QtCore.QPoint:
        ...

    @typing.overload
    def map_from_image_coordinates(self, obj: QtCore.QRectF) -> QtGui.QPolygon:
        ...

    @typing.overload
    def map_from_image_coordinates(self, obj: QtGui.QPolygonF) -> QtGui.QPolygon:
        ...

    def map_from_image_coordinates(self, obj):
        """
        Convert image coordinates to local widget coordinates.

        Image coordinates assume top-left is x=0,y=0
        """
        return self._view.map_from_image_coordinates(obj)

    # Overrides

    @abc.abstractmethod
    def boundingRect(self) -> QtCore.QRectF:
        pass

    @abc.abstractmethod
    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        pass


BasePluginType = BaseScreenSpacePlugin


class ColorPickerPlugin(BaseScreenSpacePlugin):
    def __init__(self) -> None:
        super().__init__()
        self._drawing_state = False
        self._origin: QtCore.QPointF = QtCore.QPointF(0, 0)
        self._target: QtCore.QPointF = QtCore.QPointF(10, 10)

    def boundingRect(self) -> QtCore.QRectF:
        # we interpolate the point to its nearest pixel by rounding it
        # this give the "pixel snappy" look.
        origin = QtCore.QPointF(self._origin.toPoint())
        target = QtCore.QPointF(self._target.toPoint())
        max_rect = QtCore.QRectF(
            QtCore.QPointF(self.map_from_image_coordinates(origin)),
            QtCore.QPointF(self.map_from_image_coordinates(target)),
        )
        return max_rect

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        bounding_rect = self.boundingRect()
        painter.setPen(QtGui.QPen(QtGui.QColor("red"), 2))
        painter.drawRect(bounding_rect)

        text_rect = QtCore.QRectF(0, 0, 100, 50)
        text_rect.moveCenter(bounding_rect.center())
        text_rect.moveBottom(bounding_rect.top())
        text = ""
        text += f"◸{self._origin.toPoint().toTuple()}\n"
        text += f"◿{self._target.toPoint().toTuple()}"
        painter.drawText(text_rect, QtCore.Qt.AlignCenter, text)
