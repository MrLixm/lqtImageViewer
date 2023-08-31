import abc
import logging
import typing
from typing import Optional
from typing import Union

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from ._item import ImageItem
from ._view import LIVGraphicView


LOGGER = logging.getLogger(__name__)


class BaseWorldSpacePlugin(QtWidgets.QGraphicsItem):
    def __init__(self, image_item: ImageItem) -> None:
        super().__init__()

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


class BaseScreenSpacePlugin(QtWidgets.QWidget):
    """

    Pluin different state:
        uninitialized: by default it cannot be used in code or by user
        initialized: can be used in code
        deactivated: not visible to user, cannot interact
        activated: visible to user, can interact
    """

    def __init__(self) -> None:
        super().__init__()
        self._image_item: Optional[ImageItem] = None
        self._graphicview: Optional[LIVGraphicView] = None
        self.__initialized = False
        self._activated = False
        self._visible = False
        self.installEventFilter(self)

    def initialize(
        self, image_item: ImageItem, view: LIVGraphicView, parent: QtWidgets.QWidget
    ):
        """
        "Load" the plugin with the given "context".

        Args:
            image_item: the main ImageItem in the QGraphicsScene
            view: the QQGraphicsView that can be used to retrieve information
            parent: usual QWidget parent system
        """
        if self.__initialized:
            raise RuntimeError(f"Plugin instance {self} is already initialized.")

        self._image_item = image_item
        self._graphicview = view
        # ensure this widget always have the full size of the GraphicsView
        self._graphicview.add_widget_to_resize(self)
        self.setParent(parent)
        # self.installEventFilter(parent)
        self.__initialized = True

    @typing.overload
    def map_to_image_coordinates(self, obj: QtGui.QPainterPath) -> QtGui.QPainterPath:
        ...

    @typing.overload
    def map_to_image_coordinates(self, obj: QtCore.QPoint) -> QtCore.QPointF:
        ...

    @typing.overload
    def map_to_image_coordinates(self, obj: QtCore.QRect) -> QtCore.QRectF:
        ...

    def map_to_image_coordinates(self, obj: QtGui.QPolygon) -> QtGui.QPolygonF:
        """
        Convert local widget coordinates to image coordinates.

        Image coordinates assume top-left is x=0,y=0
        """
        return self._image_item.mapFromScene(self._graphicview.mapToScene(obj))

    @typing.overload
    def map_from_image_coordinates(self, obj: QtGui.QPainterPath) -> QtGui.QPainterPath:
        ...

    @typing.overload
    def map_from_image_coordinates(self, obj: QtCore.QPointF) -> QtCore.QPoint:
        ...

    @typing.overload
    def map_from_image_coordinates(self, obj: QtCore.QRectF) -> QtCore.QRect:
        ...

    def map_from_image_coordinates(self, obj: QtGui.QPolygonF) -> QtGui.QPolygon:
        """
        Convert image coordinates to local widget coordinates.

        Image coordinates assume top-left is x=0,y=0
        """
        return self._graphicview.mapFromScene(self._image_item.mapToScene(obj))

    def set_visible(self, visible: bool):
        """
        True to make the plugin visible to the user.

        Note that the QtWidget is always visible (show() in qt terms) but nothing
        is drawn until visible is True.
        """
        self._visible = visible
        self.update()

    # Overrides

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """
        Provide a minimal default implementation for event handling.

        By default, we just do not paint the widget unless marked as visible.

        Args:
            watched:
            event:

        Returns:
            True if the event must be filtered (ignored) for this instance.
        """
        if watched is not self:
            return super().eventFilter(watched, event)

        # arbitrary event check for initialization
        if event.type() == event.Paint and not self.__initialized:
            raise RuntimeError(
                f"Cannot paint, plugin {self} has not been initialized !"
            )

        if event.type() == event.Paint and not self._visible:
            return True

        return super().eventFilter(watched, event)


BasePluginType = Union[BaseWorldSpacePlugin, BaseScreenSpacePlugin]


class ColorPickerPlugin(BaseScreenSpacePlugin):
    def __init__(self) -> None:
        super().__init__()
        self._drawing_state = False
        self._origin: Optional[QtCore.QPointF] = None
        self._target: Optional[QtCore.QPointF] = None

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        filter_event = False

        # we first assume that all mouse events are not consumed by default
        if event.type() in (
            event.MouseButtonPress,
            event.MouseButtonRelease,
            event.MouseMove,
            event.Wheel,
        ):
            filter_event = True

        if (
            isinstance(event, QtGui.QMouseEvent)
            and event.type() == event.MouseButtonPress
            and event.button() == QtCore.Qt.LeftButton
            and not event.modifiers()
        ):
            self._visible = True
            self._activated = True
            filter_event = False

        if (
            isinstance(event, QtGui.QMouseEvent)
            and event.type() == event.MouseButtonRelease
            and event.button() == QtCore.Qt.LeftButton
            and self._activated
        ):
            self._activated = False
            filter_event = False

        if filter_event and self._activated:
            filter_event = False

        if filter_event:
            QtWidgets.QApplication.sendEvent(self._graphicview.viewport(), event)
            return True

        return super().eventFilter(watched, event)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        super().mousePressEvent(event)
        image_rect = self._graphicview.get_image_viewport_rect()

        # you can only color pick if you clicked on the image
        if not image_rect.contains(event.pos()):
            return

        self._drawing_state = True
        self._origin = self.map_to_image_coordinates(event.pos())
        self._origin = QtCore.QPointF(self._origin.toPoint())
        self._target = self.map_to_image_coordinates(event.pos())
        # ensure the area is always 1x1 minimum
        self._target += QtCore.QPointF(1, 1)
        self.update()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        super().mouseMoveEvent(event)

        if not self._drawing_state:
            return

        image_rect = self._graphicview.get_image_viewport_rect()
        # make sure the area is not bigger than the image
        if not image_rect.contains(event.pos()):
            return

        self._target = self.map_to_image_coordinates(event.pos())
        self._target = QtCore.QPointF(self._target.toPoint())
        # ensure the area is always 1x1 minimum
        if self._target.x() == self._origin.x() or self._target.y() == self._origin.y():
            self._target = self._origin + QtCore.QPointF(1, 1)

        self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self._drawing_state = False

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor(150, 50, 50, 50))
        painter.setPen(QtGui.QPen(QtGui.QColor("blue"), 2))
        painter.drawRect(self._graphicview.get_image_viewport_rect())
        if self._origin is None:
            return

        # we interpolate the point to its nearest pixel by rounding it
        # this give the "pixel snappy" look.
        origin = QtCore.QPointF(self._origin.toPoint())
        target = QtCore.QPointF(self._target.toPoint())

        max_rect = QtCore.QRect(
            self.map_from_image_coordinates(origin),
            self.map_from_image_coordinates(target),
        )
        painter.setPen(QtGui.QPen(QtGui.QColor("red"), 2))
        painter.drawRect(max_rect)

        text_rect = QtCore.QRect(0, 0, 100, 50)
        text_rect.moveCenter(max_rect.center())
        text_rect.moveBottom(max_rect.top())
        text = ""
        text += f"{self._origin.toPoint().toTuple()}\n"
        text += f"{self._target.toPoint().toTuple()}"
        painter.drawText(text_rect, QtCore.Qt.AlignCenter, text)
