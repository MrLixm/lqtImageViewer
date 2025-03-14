import abc
import enum
import logging
import typing
from typing import Optional

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

from lqtImageViewer._item import ImageItem
from lqtImageViewer._scene import LIVGraphicScene
from lqtImageViewer.config import LIVKeyShortcuts


LOGGER = logging.getLogger(__name__)


class BaseScreenSpacePlugin(QtWidgets.QGraphicsItem):
    """
    A special QGraphicsItem ignoring view transformations to allow drawing screenspace effect.

    As an example zooming the view will not affect the width of a line drawn in this item.

    Assuming we have an image of size 128,128 where top left is at 0,0 in scene coordinates :

    - with no zoom the bottom right is at 128,128 in scene coordinates AND screenspace ones
    - with a zoom-in (image bigger), scene coordinates doesn't move but screenspace become bigger
    - with a zoom-out (image smaller), scene coordinates doesn't move but screenspace become smaller
    """

    def __init__(self) -> None:
        super().__init__()
        self.setFlag(self.GraphicsItemFlag.ItemIgnoresTransformations)
        self._transform = QtGui.QTransform()

    @property
    def transform(self) -> QtGui.QTransform:
        """
        Transform matrix to apply for converting from and to image coordinates
        """
        return self._transform

    @transform.setter
    def transform(self, new_transform: QtGui.QTransform):
        """
        Args:
            new_transform: usually retrieved from the graphics view
        """
        self._transform = new_transform

    @property
    def image_item(self) -> Optional[ImageItem]:
        """
        The image item living in the same scene as this plugin.

        Return None if the plugin hasn't been loaded into a scene yet.
        """
        scene: LIVGraphicScene = self.scene()
        if not scene:
            return None
        return scene.image_item

    @property
    def image_scene_rect(self) -> Optional[QtCore.QRectF]:
        """
        Rectangular area of the image in screenspace coordinates (already mapped).

        Return None if the plugin hasn't been loaded into a scene yet.
        """
        image = self.image_item
        if not image:
            return None
        return self.map_to_screenspace(self.image_item.sceneBoundingRect())

    @property
    def shortcuts(self) -> Optional[LIVKeyShortcuts]:
        """
        Key shortcuts curtenly configured for the application.
        """
        scene: LIVGraphicScene = self.scene()
        if not scene:
            return None
        return scene.shortcuts

    @typing.overload
    def map_from_screenspace(self, obj: QtGui.QPainterPath) -> QtGui.QPainterPath:
        ...

    @typing.overload
    def map_from_screenspace(self, obj: QtCore.QPoint) -> QtCore.QPoint:
        ...

    @typing.overload
    def map_from_screenspace(self, obj: QtCore.QPointF) -> QtCore.QPointF:
        ...

    @typing.overload
    def map_from_screenspace(self, obj: QtCore.QRect) -> QtCore.QRect:
        ...

    @typing.overload
    def map_from_screenspace(self, obj: QtCore.QRectF) -> QtCore.QRectF:
        ...

    @typing.overload
    def map_from_screenspace(self, obj: QtGui.QPolygon) -> QtGui.QPolygon:
        ...

    @typing.overload
    def map_from_screenspace(self, obj: QtGui.QPolygonF) -> QtGui.QPolygonF:
        ...

    def map_from_screenspace(self, obj):
        """
        Convert screenspace scene coordinates to image world scene coordinates.
        """
        matrix = self._transform.inverted()[0]
        if isinstance(obj, (QtCore.QRect, QtCore.QRectF)):
            return matrix.mapRect(obj)
        return matrix.map(obj)

    @typing.overload
    def map_to_screenspace(self, obj: QtGui.QPainterPath) -> QtGui.QPainterPath:
        ...

    @typing.overload
    def map_to_screenspace(self, obj: QtCore.QPoint) -> QtCore.QPoint:
        ...

    @typing.overload
    def map_to_screenspace(self, obj: QtCore.QPointF) -> QtCore.QPointF:
        ...

    @typing.overload
    def map_to_screenspace(self, obj: QtCore.QRect) -> QtCore.QRect:
        ...

    @typing.overload
    def map_to_screenspace(self, obj: QtCore.QRectF) -> QtCore.QRectF:
        ...

    @typing.overload
    def map_to_screenspace(self, obj: QtGui.QPolygon) -> QtGui.QPolygon:
        ...

    @typing.overload
    def map_to_screenspace(self, obj: QtGui.QPolygonF) -> QtGui.QPolygonF:
        ...

    def map_to_screenspace(self, obj):
        """
        Convert image world scene coordinates to screenspace scene coordinates.

        Watch out as the transformation might round float values !
        """
        matrix = self._transform
        if isinstance(obj, (QtCore.QRect, QtCore.QRectF)):
            return matrix.mapRect(obj)
        return matrix.map(obj)

    def on_image_changed(self):
        """
        This method is called right after a new image has been loaded.

        You can override it and perform action to update your plugin with the new image.
        The base implementation does nothing.

        Note that the [`reload`][lqtImageViewer.BaseScreenSpacePlugin.reload] method is
        called just before this callback.
        """
        pass

    def reload(self):
        """
        Perform any action necessary for the plugin to be reloaded visually.

        Made to be overriden, don't forget to call super at the end.
        """
        self.prepareGeometryChange()

    def set_visibility_from_scene_event(self, event: QtCore.QEvent):
        """
        Method to override in super class that can be used to show or hide the plugin
        based on the current events.

        You are responsible for calling show() or hide() properly and not overriding
        any existing shortcuts.

        Args:
            event: arbitrary event send to the graphics scene
        """
        pass

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
